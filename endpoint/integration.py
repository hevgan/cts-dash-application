import json
import os
import random
import time
import requests

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask_caching import Cache

# create headers api key for api call
from typing import List, Union

from dash.html import Figure
from icecream import ic



headers = {
    'Content-Type': 'application/json',
    'ApiKey': '1234'
}


map_hashes = ['map_hash_1', 'map_hash_2', 'map_hash_3']
settings_hashes = ['settings_hash_1', 'settings_hash_2', 'settings_hash_3']
run_ids = ['run_id_1', 'run_id_2', 'run_id_3']
chart_types = ['replay', 'position heatmap',  'map', 'settings', 'speed heatmap' 'acceleration heatmap', 'speed histogram', 'acceleration histogram']


URL = ''

# TODO @Aleksander add car features, frame count/s, min and max map size to metadata

# # create function to get data from api
# def fetch_data(endpoint : str, params : dict = None) -> dict:
#     querystring = build_uri_params_from_dict(params)
#     url = URL + '/' + endpoint
#     response = requests.request("GET", url, headers=headers, params=querystring)
#     return response.json()
#
#
#
#
# def build_uri_params_from_dict(params : dict) -> str:
#     return '&'.join([f"{key}={value}" for key, value in params.items()])





def dump_replay_position_plot_data_to_file():
    data = json.loads(open('test-simulation-01.json').read())
    df_cols = ['id', 'state', 'position_x', 'position_y', 'distanceToPrecedingCar', 'frame', 'color',
               'display_size']

    tmp_df = pd.DataFrame(columns=df_cols)
    car_colors = {
    }
    min_x = 0
    max_x = 0
    min_y = 0
    max_y = 0

    for frame in data['frames'][100:]:
        for car in frame['cars']:
            print(frame['frameNumber'])

            x = car["position"]["x"]
            y = car["position"]["y"]

            color = random.choice(['red', 'blue', 'green', ])
            if car.get('id') not in car_colors:
                car_colors[car.get('id')] = color
            tmp_df = pd.concat([tmp_df, pd.DataFrame([[car['id'], car['state'], x,
                                                       y, car['distanceToPrecedingCar'],
                                                       frame['frameNumber'], car_colors.get(car.get("id")),
                                                       15]],
                                                     columns=df_cols)], ignore_index=True)
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

    tmp_df['display_size'] = tmp_df['display_size'].apply(pd.to_numeric)

    with open('replay-simulation.json', 'w') as f:
        dataframe_to_plot = tmp_df.to_json(orient='records')
        tmp = {"metadata":
                   {"min_x": min_x,
                    "max_x": max_x,
                    "min_y": min_y,
                    "max_y": max_y,
                    "num_of_frames": len(tmp_df),
                    "available_car_attributes": []},
               "data": dataframe_to_plot,

               }
        json.dump(tmp, f, separators=(',', ':'))


def load_replay_position_plot_data_from_file() -> (pd.DataFrame, dict):
    metadata = json.load(open('replay-simulation.json'))['metadata']
    data = pd.read_json(json.load(open('replay-simulation.json'))['data'])
    return data, metadata


def get_simulation_replay(map_hash : str, settings_hash : str, run_id : str, chart_type: str) -> go.Figure:
    if not os.path.exists('replay-simulation.json'):
        dump_replay_position_plot_data_to_file()

    dataframe_to_plot, simulation_metadata = load_replay_position_plot_data_from_file()
    # change to query_replay_data once redoing app as a one page

    fig = px.scatter(dataframe_to_plot,
                     x="position_x",
                     y="position_y",
                     # nbinsx = 10,
                     #    nbinsy = 10,
                     animation_frame="frame",
                     color="color",
                     animation_group="id",
                     hover_name="id",
                     size="display_size",
                     log_x=False,
                     size_max=20,
                     range_x=[simulation_metadata['min_x'], simulation_metadata['max_x']],
                     range_y=[simulation_metadata['min_y'], simulation_metadata['max_y']],
                     template="plotly_dark"
                     )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000 / (
                simulation_metadata.get('frames_per_second') or 60)

    return fig


def placeholder_chart(map_hash : str, settings_hash : str, run_id : str, chart_type : str) -> go.Figure:
    df = px.data.iris()
    return px.scatter(df, x="sepal_width", y="sepal_length", color="species", template="plotly_dark",
                     title=f'{map_hash} {settings_hash} {run_id} {chart_type} plot')


def dump_heatmap_position_to_file():
    data = json.loads(open('test-simulation-01.json').read())
    df_cols = ['id', 'state', 'position_x', 'position_y', 'distanceToPrecedingCar', 'frame', 'color',
               'display_size']

    tmp_df = pd.DataFrame(columns=df_cols)
    car_colors = {
    }
    min_x = 0
    max_x = 0
    min_y = 0
    max_y = 0

    for frame in data['frames'][100:]:
        for car in frame['cars']:
            print(frame['frameNumber'])

            x = car["position"]["x"]
            y = car["position"]["y"]

            color = random.choice(['red', 'blue', 'green', ])
            if car.get('id') not in car_colors:
                car_colors[car.get('id')] = color
            tmp_df = pd.concat([tmp_df, pd.DataFrame([[car['id'], car['state'], x,
                                                       y, car['distanceToPrecedingCar'],
                                                       frame['frameNumber'], car_colors.get(car.get("id")),
                                                       15]],
                                                     columns=df_cols)], ignore_index=True)
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

    tmp_df['display_size'] = tmp_df['display_size'].apply(pd.to_numeric)

    with open('heatmap.json', 'w') as f:
        dataframe_to_plot = tmp_df.to_json(orient='records')
        tmp = {"metadata":
                   {"min_x": min_x,
                    "max_x": max_x,
                    "min_y": min_y,
                    "max_y": max_y,
                    "num_of_frames": len(tmp_df),
                    "available_car_attributes": []},
               "data": dataframe_to_plot,

               }
        json.dump(tmp, f, separators=(',', ':'))


def load_heatmap_position_plot_data_from_file():
    metadata = json.load(open('heatmap.json'))['metadata']
    data = pd.read_json(json.load(open('heatmap.json'))['data'])
    return data, metadata


def get_simulation_position_heatmap(map_hash, settings_hash, run_id):
    if not os.path.exists('position_heatmap.json'):
        dump_heatmap_position_to_file()

    dataframe_to_plot, simulation_metadata = load_heatmap_position_plot_data_from_file()

    # generate placeholder plot
    fig = placeholder_chart(map_hash, settings_hash, run_id, 'position heatmap')

    #

    return fig



# def get_chart(map_hash: str, settings_hash: str, run_id: str, chart_type: str) -> Union[Figure, dict]:
#
#
#     # wait for 5 seocnds
#     time.sleep(5)
#
#     if chart_type == 'replay':
#         return get_simulation_replay(map_hash, settings_hash, run_id)
#     elif chart_type == 'position heatmap':
#         return get_simulation_position_heatmap(map_hash, settings_hash, run_id)
#     elif chart_type == 'POSITION_HEATMAP':
#         import requests
#         api_url = 'https://ctsbackend.bieda.it/api/processed/find'
#         headers = {
#             'ApiKey': '1234'
#         }
#         params = {
#             'SettingsHash': settings_hash,
#             'MapHash': map_hash,
#             'RunId': run_id,
#             'ChartType': 'POSITION_HEATMAP'
#         }
#         response = requests.get(url=api_url, headers=headers, params=params)
#
#
#         #load json to object
#         #content = content.replace('"_id" : ObjectId("638361e8e21a30ba017e8db7"), ', '')
#         #content = content.replace('\\\\', '\\')
#         #print(content)
#         #loaded_json = json.loads(response.content)
#         #frame = loaded_json.get("Data")[0]
#
#
#
#         #ic(frame)
#         #frame = json.loads(frame)
#         #metadata = loaded_json.get("Metadata")
#         #min_x, max_x, min_y, max_y = metadata.get("min_x"), metadata.get("max_x"), metadata.get("min_y"), metadata.get("max_y")
#         min_x, max_x, min_y, max_y = -10, 10, -10, 10
#         scale_factor = 100
#         #ic(min_x, min_y, max_y, max_x)
#
#
#         #df = frame
#
#
#         # mask = df.other_filterable_car_attributes.apply(lambda x: 'red' in x)
#         # df_filtered_red = df[mask]
#        # ic(df.tail(20))
#        #  fig = px.density_heatmap(df, nbinsx=30,
#        #                           nbinsy=30, x="x", y="y",
#        #                           title="Density heatmap  ")
#        #  return fig
#         return placeholder_chart(map_hash, settings_hash, run_id, chart_type)
#
#
#
#
#     elif chart_type:
#         return placeholder_chart(map_hash, settings_hash, run_id, chart_type)
#     else:
#         return {}

#memoize

def get_matching_simulations(map_hash = None, settings_hash = None, run_id = None, chart_type = None):

    # wait for 5 seocnds
    #time.sleep(2)


    print("LOOKING FOR MATCHING SIMULATIONS")
    api_url = 'https://ctsbackend.bieda.it/api/processed/list'
    headers = {
        'ApiKey': '1234'
    }



    response = requests.get(url=api_url, headers=headers)

    ic(response.text)

    available_combinations = []
    for item in response.json():
        available_combinations.append(
            {'map_hash': item['mapHash'], 'settings_hash': item['settingsHash'], 'run_id': item['runId']})



    # filter available combination by map_hash, settings_hash, run_id, chart_type (if not None)
    if map_hash:
        available_combinations = [x for x in available_combinations if x['map_hash'] == map_hash]
    if settings_hash:
        available_combinations = [x for x in available_combinations if x['settings_hash'] == settings_hash]
    if run_id:
        available_combinations = [x for x in available_combinations if x['run_id'] == run_id]
    # if chart_type:
    #     available_combinations = [x for x in available_combinations if x['chart_type'] == chart_type]

    matching_combinations = available_combinations

    # print matching_combinations in for loop
    for combination in matching_combinations:
        print(combination)

    # extract all map_hashes from matching_combinations
    map_hashes = [c.get('map_hash') for c in matching_combinations]
    # extract all settings_hashes from matching_combinations
    settings_hashes = [c.get('settings_hash') for c in matching_combinations]
    # extract all run_ids from matching_combinations
    run_ids = [c.get('run_id') for c in matching_combinations]
    # extract all chart_types from matching_combinations
    chart_types = [c.get('chart_type') for c in matching_combinations]

    # only leave unique values in dicts
    map_hashes = list(set(map_hashes)) or []
    settings_hashes = list(set(settings_hashes)) or []
    run_ids = list(set(run_ids)) or []
    chart_types = ['replay', 'position heatmap', 'POSITION_HEATMAP']


    return map_hashes, settings_hashes, run_ids, chart_types