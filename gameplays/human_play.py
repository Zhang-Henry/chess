import sys
sys.path.append('..')
import argparse
import os
from net import resnet
import common
import time
import numpy as np
import random
from cchess_zero import cbf
from config import conf
from net import net_maintainer
import urllib
import tensorflow as tf
import gameplay
import players

currentpath = os.path.dirname(os.path.realpath(__file__))
project_basedir = os.path.join(currentpath, '..')
sys.path.append(project_basedir)


class Game(object):
    def __init__(self, white, black, verbose=True):
        self.white = white
        self.black = black
        self.verbose = verbose
        self.gamestate = gameplay.GameState()

    def play_till_end(self):
        winner = 'peace'
        moves = []
        peace_round = 0
        remain_piece = gameplay.countpiece(self.gamestate.statestr)
        while True:
            if self.gamestate.move_number % 2 == 0:
                player_name = 'w'
                player = self.white
                # human move
                move, score = player.make_move(
                    self.gamestate, human_play=True)
            else:
                player_name = 'b'
                player = self.black
                # machine move
                move, score = player.make_move(self.gamestate)

            if move is None:  # Surrender
                winner = 'b' if player_name == 'w' else 'w'
                break
            moves.append(move)

            game_end, winner_p = self.gamestate.game_end()
            if game_end:
                winner = winner_p
                break

            remain_piece_round = gameplay.countpiece(
                self.gamestate.statestr)
            if remain_piece_round < remain_piece:
                remain_piece = remain_piece_round
                peace_round = 0
            else:
                peace_round += 1
            if peace_round > conf.non_cap_draw_round:
                winner = 'peace'
                break

        print('winner: {}'.format(winner))
        return winner, moves


class NetworkPlayGame(Game):
    def __init__(self, network_w, network_b, **xargs):
        whiteplayer = players.NetworkPlayer('w', network_w, **xargs)
        blackplayer = players.NetworkPlayer('b', network_b, **xargs)
        super(NetworkPlayGame, self).__init__(whiteplayer, blackplayer)


class ContinusNetworkPlayGames(object):
    def __init__(self, network_w=None, network_b=None, white_name='net', black_name='net', random_switch=True, recoard_game=True, recoard_dir='data/distributed/', play_times=np.inf, distributed_server=None, distributed_dir='data/download_weight', **xargs):
        self.network_w = network_w
        self.network_b = network_b
        self.white_name = white_name
        self.black_name = black_name
        self.random_switch = random_switch
        self.play_times = play_times
        self.recoard_game = recoard_game
        self.recoard_dir = recoard_dir
        self.xargs = xargs
        self.distributed_server = distributed_server
        self.distributed_dir = distributed_dir
        self.nm = net_maintainer.NetMatainer(
            server=distributed_server, netdir=distributed_dir)

    def begin_of_game(self):
        pass

    def end_of_game(self, cbf_name, moves, cbfile):
        pass

    def play(self):
        num = 0
        while num < self.play_times:
            num += 1
            self.begin_of_game()
            if self.random_switch and random.random() < 0.5:
                self.network_w, self.network_b = self.network_b, self.network_w
                self.white_name, self.black_name = self.black_name, self.white_name

            network_play_game = NetworkPlayGame(
                self.network_w, self.network_b, **self.xargs)
            winner, moves = network_play_game.play_till_end()
            print("moves:" + move)
            stamp = time.strftime('%Y-%m-%d_%H-%M-%S',
                                  time.localtime(time.time()))
            date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            cbfile = cbf.CBF(black=self.black_name, red=self.white_name, date=date,
                             site='北京', name='noname', datemodify=date,
                             redteam=self.white_name, blackteam=self.black_name, round='第一轮')
            cbfile.receive_moves(moves)

            randstamp = random.randint(0, 1000)
            cbffilename = '{}_{}_mcts-mcts_{}-{}_{}.cbf'.format(
                stamp, randstamp, self.white_name, self.black_name, winner)
            cbf_name = os.path.join(self.recoard_dir, cbffilename)
            cbfile.dump(cbf_name)
            self.end_of_game(cbffilename, moves, cbfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="mcts self play script")
    parser.add_argument('--verbose', '-v',
                        action='store_true', help='verbose mode')
    parser.add_argument('--gpu', '-g', choices=[int(i) for i in list(
        range(8))], type=int, help="gpu core number", default=0)
    parser.add_argument('--server', '-s', type=str,
                        help="distributed server location", default=conf.server)
    args = parser.parse_args()

    gpu_num = int(args.gpu)
    server = args.server
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_num)

    labels = common.board.create_uci_labels()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_num)
    new_name = sorted(
        [i[:-6] for i in os.listdir(conf.distributed_server_weight_dir) if '.index' in i])[-1]
    # if conf.weight_up_immediately:
    #     old_name = sorted([i[:-6] for i in os.listdir(conf.distributed_server_weight_dir)
    #                        if '.index' in i and conf.noup_flag not in i])[-2]
    # else:
    #     old_name = sorted([i[:-6] for i in os.listdir(conf.distributed_server_weight_dir)
    #                        if '.index' in i and conf.noup_flag not in i])[-1]
    netnew = resnet.get_model('{}/{}'.format(conf.distributed_server_weight_dir, new_name), labels,
                              GPU_CORE=[gpu_num], FILTERS=conf.network_filters, NUM_RES_LAYERS=conf.network_layers)
    vg = ContinusNetworkPlayGames(network_w=netnew, network_b=netnew, white_name='oldnet',
                                  black_name='newnet', play_times=200, recoard_dir='data/validate', n_playout=400)
    vg.play()
