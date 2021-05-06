import sys
sys.path.append('..')
from cchess_zero import mcts_pool, mcts_async
import urllib.parse
import urllib.request
from cchess import BaseChessBoard
from gameplays.game_convert import boardarr2netinput
from cchess import *
from common import board
import common
from net import resnet
from cchess_zero.gameboard import *
from collections import deque, defaultdict, namedtuple
import random
import numpy as np
from asyncio.queues import Queue
import asyncio
from config import conf
import os


currentpath = os.path.dirname(os.path.realpath(__file__))
project_basedir = os.path.join(currentpath, '..')
sys.path.append(project_basedir)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    print("uvloop not detected, ignoring")
    pass

labels = common.board.create_uci_labels()
uci_labels = common.board.create_uci_labels()
QueueItem = namedtuple("QueueItem", "feature future")


class Player(object):
    def __init__(self, side):
        assert(side in ['w', 'b'])
        self.side = side

    async def make_move(self, state):
        raise NotImplementedError()

    async def oppoent_make_move(self, move, state):
        pass

    async def game_end(self, state, winner_name):
        pass


class HumanPlayer(Player):
    def __init__(self, side, game_id):
        super(HumanPlayer, self).__init__(side)
        self.game_id = game_id
        self.queue_rx = Queue(maxsize=1)
        self.queue_tx = Queue(maxsize=1)

    async def make_move(self, state):
        assert(state.currentplayer == self.side)
        legal_move = GameBoard.get_legal_moves(
            state.statestr, state.currentplayer)
        GameBoard.print_borad(state.statestr)

        while True:
            print("Wait for human input")
            await self.send_message(state, {'validMoves': legal_move})
            move = await self.queue_rx.get()
            if move in legal_move:
                break
            else:
                print("Invalid human move")
                await self.send_message(state, {'error': '无效操作'})

        state.do_move(move)
        return move, None

    async def game_end(self, state, winner_name):
        await self.send_message(state, {'end': winner_name, 'validMoves': []})

    async def send_message(self, state, message):
        human_side = self.side
        if human_side == 'w':
            net_side = 'b'
        else:
            net_side = 'w'

        await self.queue_tx.put({
            'id': self.game_id,
            'state': state.statestr,
            'humanSide': self.side,
            'netSide': net_side,
            **message
        })


class NetworkPlayer(Player):
    def __init__(self, side, network, debugging=True, n_playout=800, search_threads=16, virtual_loss=0.02, policy_loop_arg=True, c_puct=5, dnoise=False, temp_round=conf.train_temp_round, can_surrender=False, surrender_threshold=-0.99, allow_legacy=False, repeat_noise=True, is_selfplay=False):
        super(NetworkPlayer, self).__init__(side)
        self.network = network
        self.debugging = debugging
        self.queue = Queue(400)
        self.temp_round = temp_round
        self.can_surrender = can_surrender
        self.allow_legacy = allow_legacy
        self.surrender_threshold = surrender_threshold
        self.repeat_noise = repeat_noise
        self.mcts_policy = mcts_async.MCTS(self.policy_value_fn_queue, n_playout=n_playout, search_threads=search_threads,
                                           virtual_loss=virtual_loss, policy_loop_arg=policy_loop_arg, c_puct=c_puct, dnoise=dnoise)
        self.is_selfplay = is_selfplay

    async def push_queue(self, features, loop):
        future = loop.create_future()
        item = QueueItem(features, future)
        await self.queue.put(item)
        return future

    async def prediction_worker(self, mcts_policy_async):
        (sess, graph), ((X, training), (net_softmax, value_head)) = self.network
        q = self.queue
        while mcts_policy_async.num_proceed < mcts_policy_async._n_playout:
            if q.empty():
                await asyncio.sleep(1e-3)
                continue
            item_list = [q.get_nowait() for _ in range(q.qsize())]
            #print("processing : {} samples".format(len(item_list)))
            features = np.concatenate(
                [item.feature for item in item_list], axis=0)

            action_probs, value = sess.run([net_softmax, value_head], feed_dict={
                                           X: features, training: False})
            for p, v, item in zip(action_probs, value, item_list):
                item.future.set_result((p, v))

    async def policy_value_fn_queue(self, state, loop):
        bb = BaseChessBoard(state.statestr)
        statestr = bb.get_board_arr()
        net_x = np.transpose(boardarr2netinput(
            statestr, state.get_current_player()), [1, 2, 0])
        net_x = np.expand_dims(net_x, 0)
        future = await self.push_queue(net_x, loop)
        await future
        policyout, valout = future.result()
        policyout, valout = policyout, valout[0]
        legal_move = GameBoard.get_legal_moves(
            state.statestr, state.get_current_player())
        # if state.currentplayer == 'b':
        #    legal_move = board.flipped_uci_labels(legal_move)
        legal_move = set(legal_move)
        legal_move_b = set(board.flipped_uci_labels(legal_move))

        action_probs = []
        if state.currentplayer == 'b':
            for move, prob in zip(uci_labels, policyout):
                if move in legal_move_b:
                    move = board.flipped_uci_labels([move])[0]
                    action_probs.append((move, prob))
        else:
            for move, prob in zip(uci_labels, policyout):
                if move in legal_move:
                    action_probs.append((move, prob))
        #action_probs = sorted(action_probs,key=lambda x:x[1])
        return action_probs, valout

    def get_random_policy(self, policies):
        sumnum = sum([i[1] for i in policies])
        randnum = random.random() * sumnum
        tmp = 0
        for val, pos in policies:
            tmp += pos
            if tmp > randnum:
                return val

    async def make_move(self, state, actual_move=True):
        assert(state.currentplayer == self.side)
        if state.move_number < self.temp_round or (self.repeat_noise and state.maxrepeat > 1):
            temp = 1
        else:
            temp = 1e-4
        if state.move_number >= self.temp_round and self.is_selfplay == True:
            can_apply_dnoise = True
        else:
            can_apply_dnoise = False
        acts, act_probs = await self.mcts_policy.get_move_probs(state, temp=temp, verbose=False, predict_workers=[
            self.prediction_worker(self.mcts_policy)], can_apply_dnoise=can_apply_dnoise)
        policies, score = list(zip(acts, act_probs)
                               ), self.mcts_policy._root._Q
        score = -score

        # 1 means going to win, -1 means going to lose
        if score < self.surrender_threshold and self.can_surrender:
            return None, score

        move = self.get_random_policy(policies)

        if actual_move:
            state.do_move(move)
            self.mcts_policy.update_with_move(
                move, allow_legacy=self.allow_legacy)
        return move, score

    # async def oppoent_make_move(self, move, state):
    #     self.mcts_policy.update_with_move(move, allow_legacy=self.allow_legacy)
