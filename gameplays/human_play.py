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

    def play_till_end(self):
        winner = 'peace'
        moves = []
        peace_round = 0
        remain_piece = gameplay.countpiece(self.gamestate.statestr)
        while True:
            if self.gamestate.move_number % 2 == 0:
                player_name = 'w'
                player = self.white
            else:
                player_name = 'b'
                player = self.black

            move, score = player.make_move(self.gamestate)
            print("Move", player_name, move)

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


def get_net():
    labels = common.board.create_uci_labels()
    new_name = sorted(
        [i[:-6] for i in os.listdir(conf.distributed_server_weight_dir) if '.index' in i])[-1]
    return resnet.get_model('{}/{}'.format(conf.distributed_server_weight_dir, new_name), labels,
                            GPU_CORE=[0], FILTERS=conf.network_filters, NUM_RES_LAYERS=conf.network_layers)


def new_game(network):
    if random.random() < 0.5:
        vg = Game(players.HumanPlayer('w'),
                  players.NetworkPlayer('b', network))
    else:
        vg = Game(
            players.NetworkPlayer('w', network), players.HumanPlayer('b'))

    winner, moves = vg.play_till_end()
    print(winner, moves)


if __name__ == "__main__":
    newnet = get_net()
    new_game(newnet)
