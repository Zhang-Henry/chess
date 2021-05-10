import sys
sys.path.append('..')
import argparse
import os
from net import resnet
import common
import numpy as np
import random
import time
import uuid
import asyncio
from config import conf
import tensorflow as tf
from aiohttp import web
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

    async def play_till_end(self):
        winner = 'peace'
        moves = []
        peace_round = 0
        remain_piece = gameplay.countpiece(self.gamestate.statestr)
        while True:
            if self.gamestate.move_number % 2 == 0:
                player_name = 'w'
                player = self.white
                opponent_player = self.black
            else:
                player_name = 'b'
                player = self.black
                opponent_player = self.white

            move, score = await player.make_move(self.gamestate)
            print("Move", player_name, move)

            if move is None:  # Surrender
                winner = 'b' if player_name == 'w' else 'w'
                break
            moves.append(move)

            game_end, winner_p = self.gamestate.game_end()
            if game_end:
                winner = winner_p
                await player.game_end(self.gamestate, winner)
                await opponent_player.game_end(self.gamestate, winner)
                break
            else:
                await opponent_player.oppoent_make_move(move, self.gamestate)

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


def get_net():
    labels = common.board.create_uci_labels()
    new_name = sorted(
        [i[:-6] for i in os.listdir(conf.distributed_server_weight_dir) if '.index' in i])[-1]
    return resnet.get_model('{}/{}'.format(conf.distributed_server_weight_dir, new_name), labels,
                            GPU_CORE=[0], FILTERS=conf.network_filters, NUM_RES_LAYERS=conf.network_layers)


async def new_game(network, human):
    if random.random() < 0.5:
        human.side = 'w'
        vg = Game(human, players.NetworkPlayer('b', network))
    else:
        human.side = 'b'
        vg = Game(
            players.NetworkPlayer('w', network), human)

    winner, moves = await vg.play_till_end()
    print(winner, moves)


newnet = None

games = {}
routes = web.RouteTableDef()

COMMON_HEADERS = {'Access-Control-Allow-Origin': '*'}


@routes.post("/game")
async def handle_new_game(request):
    global newnet, games

    if newnet is None:
        newnet = get_net()

    game_id = str(uuid.uuid4())
    human_player = players.HumanPlayer('w', game_id)
    asyncio.get_event_loop().create_task(new_game(newnet, human_player))
    games[game_id] = human_player

    return web.json_response(await human_player.queue_tx.get(), headers=COMMON_HEADERS)


@routes.post("/game/interact")
async def handle_move(request):
    global games
    data = await request.post()
    game_id = data['uuid']
    move = data['move']
    player = games[game_id]
    await player.queue_rx.put(move)
    return web.json_response(await player.queue_tx.get(), headers=COMMON_HEADERS)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=10080)
