import dash
import dash_bootstrap_components as dbc
import diskcache
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from dash import Input, Output, html
from dash import dcc
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from dash.html import Figure
from dash.long_callback import DiskcacheLongCallbackManager
from dash_bootstrap_templates import load_figure_template
from endpoint import integration
from flask_caching import Cache
from icecream import ic
from typing import Union
from uuid import uuid4
import random
import numpy as np
background_callback_manager = DiskcacheLongCallbackManager(
    background_cache := diskcache.Cache("./cache"),
)
random_tags = ['drunk', 'high', 'stupid', 'inexperienced', 'woman', 'bitchy']

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.DARKLY],
                suppress_callback_exceptions=True,
                background_callback_manager=background_callback_manager
                )
app.config.suppress_callback_exceptions = True

memoization_cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'memoization_cache'
})

TIMEOUT = 30000
DROPDOWN_TIMEOUT = 10

server = app.server

templates = [
    "lux"]

load_figure_template(templates)

dropdowns = dbc.Container(
    dbc.Row(
        [
            dbc.Col([
                dcc.Dropdown([], id='map-hash-select', placeholder="select mapHash",
                             ),

            ]

            ),
            dbc.Col([
                dcc.Dropdown([], id='settings-hash-select',
                             placeholder="select settingHash", ),

            ]

            ),
            dbc.Col(
                [
                    dcc.Dropdown([], id='run-id-select', placeholder="select runId", ),
                ],

            ),
            dbc.Col(
                [
                    dcc.Dropdown([], id='chart-type-select',
                                 placeholder="select chart type", ),
                ],

            ),

            dbc.Col(
                [

                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(children="analyze", id="run-simulation-button", color="primary"),
                                width={"size": 1, "order": 1, "offset": 0},

                            ),
                            dbc.Col(dbc.Button(id="cancel_run_simulation", children="cancel", color='danger',
                                               disabled=True),
                                    width={"size": 7, "order": 2, "offset": 1},

                                    ),

                        ],
                        justify="between",
                    ),

                ],
                width=2

            ),

        ],
        style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', },
    ),

)

dropdown_container = dbc.Container(
    children=[
        dropdowns
    ],
    fluid=True,
    id='container',
    style={'width': '100%', 'height': '100%'},
    className="mt-2 mb-1 ",
)

result_container = dbc.Container([

    dcc.Loading([
        dbc.Row([
            dbc.Col(id='chart-container', width=12, style={'height': '100%'}),
        ]),
        dbc.Row(dbc.Col(id='simulation-filters', children=[
            dbc.Label("simulation-filters"),
            dcc.Dropdown(random_tags, id='simulation-filters-select', multi=True, value=random_tags),
        ], width=5),
                )
    ],
        type="graph",
        fullscreen=False,
    )
],
    fluid=True,
    id='result-container',
    style={'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)'}
)

additional_handlers = dbc.Container([
    dcc.ConfirmDialog(id='confirm', message='Please select all parameters'),
]
)

app.layout = html.Div([
    dbc.NavbarSimple(
        [
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Creators", header=True),
                    dbc.DropdownMenuItem("Aleksander Błaszkiewicz", href='https://github.com/ablaszkiewicz'),
                    dbc.DropdownMenuItem("Maciej Adryan", href="https://github.com/hevgan"),
                    dbc.DropdownMenuItem("Michał Matejuk", href='https://github.com/matejukx'),
                    dbc.DropdownMenuItem("Jakub Brzozowski", href="https://github.com/brzzw5k"),


                    dbc.DropdownMenuItem("Repos", header=True),
                    dbc.DropdownMenuItem("Backend", href='https://github.com/matejukx/city-traffic-simulator-backend'),
                    dbc.DropdownMenuItem("Computational backend", href="https://github.com/brzzw5k/city-traffic-simulator-computing-microservice"),
                    dbc.DropdownMenuItem("Dashboard", href="https://github.com/hevgan/cts-dash-application"),
                    dbc.DropdownMenuItem("Simulation", href="https://github.com/ablaszkiewicz/city-traffic-simulation"),

                    dbc.DropdownMenuItem("Documentation", header=True),
                    dbc.DropdownMenuItem("Backend", href='https://ctsbackend.bieda.it/swagger/index.html'),

                    dbc.DropdownMenuItem("External components", header=True),
                    dbc.DropdownMenuItem("Flask", href="https://flask.palletsprojects.com/en/2.0.x/"),
                    dbc.DropdownMenuItem("Dash", href="https://dash.plotly.com/"),
                    dbc.DropdownMenuItem("Plotly", href="https://plotly.com/python/"),
                    dbc.DropdownMenuItem("Dash Bootstrap Components", href="https://dash-bootstrap-components.opensource.faculty.ai/"),
                    dbc.DropdownMenuItem("Diskcache", href="https://www.grantjenks.com/docs/diskcache/"),
                    dbc.DropdownMenuItem("Unity", href="https://unity.com/"),


                    dbc.DropdownMenuItem("University", header=True),
                    dbc.DropdownMenuItem("GUT", href="https://pg.edu.pl/en/"),

                ],
                nav=True,
                in_navbar=True,
                label="Links",
            ),

        ],
        brand="City Traffic Simulator PROD",
        brand_href="javascript:window.location.reload(true)",
        color="secondary",
        dark=True,
    ),
    dropdown_container,
    result_container,
    additional_handlers,
])


@app.callback(
    output=(Output(component_id='map-hash-select', component_property='options'),
            Output(component_id='settings-hash-select', component_property='options'),
            Output(component_id='run-id-select', component_property='options'),
            Output(component_id='chart-type-select', component_property='options'),
            Output(component_id='run-simulation-button', component_property='disabled')),
    inputs=(
            Input(component_id='map-hash-select', component_property='value'),
            Input(component_id='settings-hash-select', component_property='value'),
            Input(component_id='run-id-select', component_property='value'),
            Input(component_id='chart-type-select', component_property='value'))

)
def update_dropdowns(map_hash, settings_hash, run_id, chart_type):
    is_analyze_button_enabled = not all([map_hash, settings_hash, run_id, chart_type])
    try:
        matching_dropdown_values = get_matching_dropdown_values(map_hash=map_hash, settings_hash=settings_hash,
                                                        run_id=run_id, chart_type=chart_type)
    except:
        return [], [], [], [], False
    values = [*matching_dropdown_values, is_analyze_button_enabled]
    return values


#@memoization_cache.memoize(timeout=10)
def get_matching_dropdown_values(map_hash, settings_hash, run_id, chart_type):
    return integration.get_matching_simulations(map_hash, settings_hash, run_id, chart_type)


@dash.callback(
    output=(Output(component_id='chart-container', component_property='children')),
    inputs=(Input(component_id='run-simulation-button', component_property='n_clicks'),
            State(component_id='map-hash-select', component_property='value'),
            State(component_id='settings-hash-select', component_property='value'),
            State(component_id='run-id-select', component_property='value'),
            State(component_id='chart-type-select', component_property='value'),
            State(component_id='simulation-filters-select', component_property='value')),
    running=[
        (Output("run-simulation-button", "disabled"), True, False),
        (Output("cancel_run_simulation", "disabled"), False, True),
        (Output("result-container", "style"),
         {'position': 'fixed', 'top': '50%', 'left': '50%', 'transform': 'translate(-50%, -50%)'}, {}),
    ],
    cancel=[Input("cancel_run_simulation", "n_clicks")],
    background=True,
    prevent_initial_call=True,
)
def update_chart_container(n_clicks, map_hash, settings_hash, run_id, chart_type, filters):
    if n_clicks is None:
        raise PreventUpdate

    all_selected = all([map_hash, settings_hash, str(run_id), chart_type])


    if ctx_id := dash.callback_context.triggered_id == 'run-simulation-button':
        if all_selected:
            if chart_type != 'analitycal dashboard':
                chart = get_chart(map_hash, settings_hash, run_id, chart_type, filters)
                container = get_chart_container(chart)
            else:
                container = get_analytical_dashboard(map_hash, settings_hash, run_id)
            return container
        else:
            return {}
    raise PreventUpdate


##@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_chart_container(chart):
    container = dbc.Container([
        dbc.Row([
            dbc.Col(
                id='chart', children=[
                    dcc.Graph(figure=chart, style={'width': '100%', 'height': '80vh'})]),

        ],
        ),

    ],
        style={'width': '100%', 'height': '100%'},
        fluid=True,
        className="mt-4",
    )
    return container


##@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_chart(map_hash: str, settings_hash: str, run_id: str, chart_type: str, filters) -> Union[Figure, dict]:
    if chart_type == 'replay simulation':
        return get_simulation_replay(map_hash, settings_hash, run_id, chart_type, filters)
    elif chart_type == 'position heatmap':
        fig = get_position_heatmap(map_hash, run_id, settings_hash)
        return fig
    elif chart_type == 'speed heatmap':
        fig = get_speed_heatmap(map_hash, run_id, settings_hash)
        return fig
    elif chart_type == 'acceleration heatmap':
        fig = get_acceleration_heatmap(map_hash, run_id, settings_hash)
        return fig
    elif chart_type == 'attributes percentage':
        fig = get_attributes_pie_chart(map_hash, run_id, settings_hash)
        return fig
    elif chart_type == 'analitycal dashboard':
        fig = get_analytical_dashboard(map_hash, run_id, settings_hash)
        return fig
    elif chart_type:
        return {}
    else:
        return {}


def get_analytical_dashboard(map_hash, run_id, settings_hash):
    # create dbc container with 2 rows and 2 columns
    fig = integration.placeholder_chart(map_hash, run_id, settings_hash, 'mock')
    style = {'display': 'inline-block', 'width': '100%'}
    graph1 = dcc.Graph(figure=fig, id='fig1', style=style)
    graph2 = dcc.Graph(figure=fig, id='fig2', style=style)
    graph3 = dcc.Graph(figure=fig, id='fig3',   style=style)
    graph4 = dcc.Graph(figure=fig, id='fig4', style=style)


    container = dbc.Container(
        [
            dbc.Row([
                dbc.Col([graph1, ], id='col1', style = {'display': 'inline-block', 'width': '100%'}),
                dbc.Col([graph2], id='col2', style = {'display': 'inline-block', 'width': '100%'}),

            ], id='row1',
                style={'display': 'inline-block', 'width': '100%'}

            ),
            dbc.Row([
                dbc.Col([graph3], id='col3', style = {'display': 'inline-block', 'width': '100%'}),
                dbc.Col([graph4], id='col4', style = {'display': 'inline-block', 'width': '100%'}),

            ],
                id='row2',
                style={'display': 'inline-block', 'width': '100%'}

            ),
        ],



    id = '2138',
        style={'display': 'inline-block', 'width': '100%'}
    )
    return container


    return dbc.Row([dbc.Col([graph])])


#@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_attributes_pie_chart(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


#@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_speed_heatmap(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


#@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_acceleration_heatmap(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


##@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_simulation_replay(map_hash: str, settings_hash: str, run_id: str, chart_type: str, filtered_values) -> go.Figure:
    import requests
    api_url = 'https://ctsbackend.bieda.it/api/simulation'
    headers = {
        'ApiKey': '1234'
    }
    params = {
        'settingsHash': settings_hash,
        'mapHash': map_hash,
        'runId': run_id,
    }
    response = requests.get(url=api_url, headers=headers, params=params)

    loaded_json = json.loads(response.content)
    data = loaded_json.get("frames")

    # create empty dataframe
    dataframe_to_plot = pd.DataFrame()

    # create variables for min_x, max_x, min_y, max_y

    # set variable "dupa" to max int value


    import sys

    min_x = sys.maxsize
    max_x = -sys.maxsize
    min_y = sys.maxsize
    max_y = -sys.maxsize


    # iterate over all frames
    for frame in data:
        # append each element of frame to dataframe
        # print(frame)
        for car in frame.get('cars'):
            # print(car)
            id = car.get('id')
            frame_number = frame.get('frameNumber')
            tags = ','.join(car.get('tags'))
            state = car.get('state')

            position_x, position_y = car.get('position').get('x'), car.get('position').get('y')

            if position_x < min_x:
                min_x = position_x
            if position_x > max_x:
                max_x = position_x
            if position_y < min_y:
                min_y = position_y
            if position_y > max_y:
                max_y = position_y


            velocity_x, velocity_y = car.get('velocity').get('x'), car.get('velocity').get('y')
            acceleration_x, acceleration_y = car.get('acceleration').get('x'), car.get('acceleration').get('y')
            distance_to_preceding_car = car.get('distanceToPrecedingCar')
            preceding_car_id = car.get('precedingCarId')
            display_size = 10

            # create dataframe row from id, tags, state, velocity_x, velocity_y, position_x, position_y, acceleration_x, acceleration_y, distance_to_preceding_car, preceding_car_id
            df_row = pd.DataFrame(
                {'id': id, 'display_size': display_size, 'tags': tags, 'state': state, 'velocity_x': velocity_x,
                 'velocity_y': velocity_y, 'position_x': position_x, 'position_y': position_y,
                 'acceleration_x': acceleration_x, 'acceleration_y': acceleration_y,
                 'distance_to_preceding_car': distance_to_preceding_car, 'preceding_car_id': preceding_car_id,
                 'frame_number': frame_number}, index=[0])
            # print(df_row)

            dataframe_to_plot = dataframe_to_plot.append(df_row, ignore_index=True)

    print(dataframe_to_plot.tail(10))


    metadata = None
    if not metadata:
        metadata = {
            'min_x': min_x,
            'max_x': max_y,
            'min_y': min_y,
            'max_y': max_y,
        }

    dataframe_to_plot['display_size'] =  10

    # change to get real tags
    dataframe_to_plot['tags'] = np.random.choice( random_tags,    dataframe_to_plot.shape[0])

    ic(dataframe_to_plot.tail(10))

    mask = dataframe_to_plot['tags'].isin(filtered_values)

    dataframe_to_plot = dataframe_to_plot[mask]


    fig = px.scatter(dataframe_to_plot,
                     x="position_x",
                     y="position_y",
                     animation_frame="frame_number",
                     animation_group="id",
                     size="display_size",
                     hover_name="id",
                     log_x=False,
                     log_y=False,
                     size_max=15,
                     labels={"display_color": "tags",},
                     range_x=[metadata.get('min_x'), metadata.get('max_x')],
                     range_y=[metadata.get('min_y'), metadata.get('max_y')],
                     template="plotly_dark",

                     )


    roads = get_roads_by_map_hash(map_hash)

    fix_fig_layout_for_replay(dataframe_to_plot, fig, metadata, roads)
    return fig


def get_roads_by_map_hash(map_hash):
    import requests
    api_url = f'https://ctsbackend.bieda.it/api/maps/{map_hash}'
    headers = {
        'ApiKey': '1234'
    }
    params = {}
    response = requests.get(url=api_url, headers=headers, params=params)

    loaded_json = json.loads(response.content).get("roads")
    return loaded_json

def get_data_metadata_from_response(response):
    loaded_json = json.loads(response.content)
    data = loaded_json.get("Data")
    metadata = loaded_json.get("Metadata")
    return data, metadata


def fix_fig_layout_for_replay(dataframe_to_plot, fig, metadata, roads):
    if len(dataframe_to_plot) > 0:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000 / (
                metadata.get('frames_per_second') or 6)

        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
    fig.update_layout(xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=False)
                      )
    fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
    fig.update_layout(xaxis_visible=False, xaxis_showticklabels=False)


    road_data = roads

    ic(roads)

    road_points = []

    for road in road_data:
        points = road.get('points')
        a, b, c, d, = points
        ic(a,b,c,d)

        a_x, a_y = a.values()
        b_x, b_y = b.values()
        c_x, c_y = c.values()
        d_x, d_y = d.values()
        path = f'M {a_x},{a_y} C {b_x},{b_y} {c_x},{c_y} {d_x}, {d_y}'
        road_points.append(
                dict(
                    type="path",
                    path=path,
                    line_color="white",
                )
            )


    fig.update_layout(
        shapes=road_points,
    )

    #ic(road_points)


def backend_call_with_header(map_hash, run_id, settings_hash):
    import requests
    api_url = 'https://ctsbackend.bieda.it/api/simulation'
    headers = {
        'ApiKey': '1234'
    }
    params = {
        'SettingsHash': settings_hash,
        'MapHash': map_hash,
        'RunId': run_id,
    }
    response = requests.get(url=api_url, headers=headers, params=params)
    return response


#@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_position_heatmap(map_hash, run_id, settings_hash):
    response = backend_call_with_header(map_hash, run_id, settings_hash)

    loaded_json = json.loads(response.content)
    frame = loaded_json.get("Data")
    ic(frame)

    #metadata = loaded_json.get("Metadata")

    # mask = df.other_filterable_car_attributes.apply(lambda x: 'red' in x)
    # df_filtered_red = df[mask]
    # ic(df.tail(20))

    loaded_json = json.loads(response.content)
    data = loaded_json.get("frames")

    # create empty dataframe
    dataframe_to_plot = pd.DataFrame()

    # create variables for min_x, max_x, min_y, max_y

    # set variable "dupa" to max int value

    import sys

    min_x = sys.maxsize
    max_x = -sys.maxsize
    min_y = sys.maxsize
    max_y = -sys.maxsize

    # iterate over all frames
    for frame in data:
        # append each element of frame to dataframe
        # print(frame)
        for car in frame.get('cars'):
            # print(car)
            id = car.get('id')
            frame_number = frame.get('frameNumber')
            tags = ','.join(car.get('tags'))
            state = car.get('state')

            position_x, position_y = car.get('position').get('x'), car.get('position').get('y')

            if position_x < min_x:
                min_x = position_x
            if position_x > max_x:
                max_x = position_x
            if position_y < min_y:
                min_y = position_y
            if position_y > max_y:
                max_y = position_y

            velocity_x, velocity_y = car.get('velocity').get('x'), car.get('velocity').get('y')
            acceleration_x, acceleration_y = car.get('acceleration').get('x'), car.get('acceleration').get('y')
            distance_to_preceding_car = car.get('distanceToPrecedingCar')
            preceding_car_id = car.get('precedingCarId')
            display_size = 10

            # create dataframe row from id, tags, state, velocity_x, velocity_y, position_x, position_y, acceleration_x, acceleration_y, distance_to_preceding_car, preceding_car_id
            df_row = pd.DataFrame(
                {'id': id, 'display_size': display_size, 'tags': tags, 'state': state, 'velocity_x': velocity_x,
                 'velocity_y': velocity_y, 'position_x': position_x, 'position_y': position_y,
                 'acceleration_x': acceleration_x, 'acceleration_y': acceleration_y,
                 'distance_to_preceding_car': distance_to_preceding_car, 'preceding_car_id': preceding_car_id,
                 'frame_number': frame_number}, index=[0])
            # print(df_row)

            dataframe_to_plot = dataframe_to_plot.append(df_row, ignore_index=True)

    print(dataframe_to_plot.tail(10))

    metadata = None
    if not metadata:
        metadata = {
            'min_x': min_x,
            'max_x': max_y,
            'min_y': min_y,
            'max_y': max_y,
        }



    fig = px.density_heatmap(dataframe_to_plot,
                             nbinsx=100,
                             nbinsy=100,
                             x="position_x",
                             y="position_y",

                             # animation_frame="frame",
                             # marginal_y="histogram",
                             # marginal_x="histogram",
                             # histfunc='sum',
                             title="Density heatmap",
                             template="plotly_dark",
                             # animation_frame="frame",
                             # animation_group="id",

                             # animation_group="id",
                             # hover_name="id",

                             )

    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000 / (
    #             simulation_metadata.get('frames_per_second') or 6)
    return fig

@app.server.route('/health')
def health():
    from flask import make_response
    return make_response({}, 200)

if __name__ == '__main__':
    app.run_server(port=8095, debug=True)
