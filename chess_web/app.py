import numpy as np
import pandas as pd
from flask import Flask, render_template
import os
import sys
project_basedir = '..'
sys.path.append(project_basedir)
from config import conf

def add_score(onedic,key,point):
    onedic.setdefault(key,0)
    onedic[key] += point


def cal_points(gameplays):
    point_dic = {}
    for onegame in gameplays:
        if onegame[-3:] != 'cbf':
            continue
        winner = onegame.split('_')[-1].split('.')[0]
        player1 = onegame.split('_')[-2].split('-')[0]
        player2 = onegame.split('_')[-2].split('-')[1]
        assert(winner in ['w','b','peace'])
        if winner == 'w':
            add_score(point_dic,player1,1)
            add_score(point_dic,player2,0)
        elif winner == 'b':
            add_score(point_dic,player1,0)
            add_score(point_dic,player2,1)
        elif winner == 'peace':
            add_score(point_dic,player1,0.5)
            add_score(point_dic,player2,0.5)
            add_score(point_dic,'peace',1)
        else:
            raise
    return point_dic

app = Flask(__name__)

@app.route('/')
def index():
    validate_dirs = os.listdir(conf.validate_dir)
    validate_dirs = [i for i in validate_dirs if i != '_blank']
    validate_dirs = sorted(validate_dirs)
    validate_dirs = [os.path.join(conf.validate_dir, i) for i in validate_dirs]
    game_numbers = [0]
    game_numbers_identity = [0]
    elu_points = [0]
    validate_games = [0]
    win_rate = [0]
    dates = ['start']
    peace_rates = [0]
    delta_elo = [0]
    for one_dir in validate_dirs:
        one_date = one_dir.split('/')[-1]
        gameplays = os.listdir(one_dir)
        pointcdic = cal_points(gameplays)
        game_num = len(gameplays)

        try:
            gn = len(os.listdir(os.path.join(conf.history_selfplay_dir, one_date.replace('_noup', ''))))
        except:
            gn = 0
        if game_num == 0:
            continue
        # print(os.path.join(conf.history_selfplay_dir, one_date.replace('_noup', '')))
        old_score = pointcdic.get('oldnet', 0) / game_num
        peace_rate = pointcdic.get('peace', 0) / game_num

        if old_score == 0:
            continue
        # print(gn)
        game_numbers.append(game_numbers[-1] + gn)
        game_numbers_identity.append(gn)

        elo = np.log10(1 / old_score - 1) * 400

        elu_points.append(elu_points[-1] + elo)
        validate_games.append(len(gameplays))
        win_rate.append(1 - old_score)
        dates.append(one_date)
        peace_rates.append(peace_rate)
        delta_elo.append(elo)

    df = pd.DataFrame({
        'dates': dates,
        'game_numbers': game_numbers,
        'game_numbers_identity': game_numbers_identity,
        'elu_points': elu_points,
        'validate_games': validate_games,
        'win_rate': win_rate,
        'peace_rates': peace_rates,
        'delta_elo': delta_elo,
        '上位情况': [('pending' if i is None else "上位") for i in delta_elo]
    })[-20:]
    df.index.name = 'index'
    return render_template('index.html', elu_points=elu_points, game_numbers=game_numbers , delta_elo=delta_elo, column_names=df.columns.values, row_data=list(df.values.tolist()), zip=zip)



if __name__ == '__main__':
    app.run(debug=True)
