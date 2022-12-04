import json
import os
import time
from typing import Union
from uuid import uuid4
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, html
from dash import dcc
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from dash.html import Figure
from dash.long_callback import DiskcacheLongCallbackManager
from dash_bootstrap_templates import load_figure_template
from flask_caching import Cache
from icecream import ic
import plotly.express as px

from endpoint import integration

launch_uid = uuid4()

import diskcache


background_callback_manager = DiskcacheLongCallbackManager(
    background_cache := diskcache.Cache("./cache"),
)

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

server = app.server


def get_data(map_hash: str, settings_hash: str, run_id: str, chart_type: str) -> pd.DataFrame:
    integration.get_simulation_replay()


templates = [
    "lux"]

load_figure_template(templates)

dropdowns = dbc.Container(
    dbc.Row(
        [
            dbc.Col([
                # dbc.Label("map hash"),
                dcc.Dropdown([], id='map-hash-select', placeholder="select mapHash",
                             ),

            ]

            ),
            dbc.Col([
                # dbc.Label("setting hash"),
                dcc.Dropdown([], id='settings-hash-select',
                             placeholder="select settingHash", ),

            ]

            ),
            dbc.Col(
                [
                    # dbc.Label("run id"),
                    dcc.Dropdown([], id='run-id-select', placeholder="select runId", ),
                ],

            ),
            dbc.Col(
                [

                    # dbc.Label("chart type"),
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
        # dbc row component with fixed height

        dbc.Row([
            dbc.Col(id='chart-container', width=12, style={'height': '100%'}),
        ]),

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


@app.callback(

    Output(component_id='map-hash-select', component_property='options'),
    Output(component_id='settings-hash-select', component_property='options'),
    Output(component_id='run-id-select', component_property='options'),
    Output(component_id='chart-type-select', component_property='options'),
    Output(component_id='run-simulation-button', component_property='disabled'),

    Input(component_id='map-hash-select', component_property='value'),
    Input(component_id='settings-hash-select', component_property='value'),
    Input(component_id='run-id-select', component_property='value'),
    Input(component_id='chart-type-select', component_property='value')

)
def update_dropdowns(map_hash, settings_hash, run_id, chart_type):
    print("update_dropdowns")
    is_analyze_button_enabled = not all([map_hash, settings_hash, run_id, chart_type])
    matching_dropdown_values = get_matching_simulation_from_backend(map_hash=map_hash, settings_hash=settings_hash,
                                                                    run_id=run_id, chart_type=chart_type)

    values = [*matching_dropdown_values, is_analyze_button_enabled]
    ic(values)
    return values


@dash.callback(
    output=(Output(component_id='chart-container', component_property='children')),
    inputs=(Input(component_id='run-simulation-button', component_property='n_clicks'),
            State(component_id='map-hash-select', component_property='value'),
            State(component_id='settings-hash-select', component_property='value'),
            State(component_id='run-id-select', component_property='value'),
            State(component_id='chart-type-select', component_property='value')),
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
def update_chart_container(n_clicks, map_hash, settings_hash, run_id, chart_type):
    # print("update_chart_container")
    # if n_clicks is None:
    #     raise PreventUpdate

    display_confirm = all([map_hash, settings_hash, str(run_id), chart_type])

    if ctx_id := dash.callback_context.triggered_id == 'run-simulation-button':
        if display_confirm:
            ic("before fetching")
            tmp_chart_to_replace = get_chart(map_hash, settings_hash, run_id, chart_type)
            ic("fetching done")
            container = dbc.Container([
                dbc.Row([
                    dbc.Col(
                        id='chart', children=[
                            # dbc.Label("chart"),
                            dcc.Graph(figure=tmp_chart_to_replace, style={'width': '100%', 'height': '80vh'})]),

                ],
                ),
                dbc.Row(dbc.Col(id='simulation-manipulation-container', children=[
                    dbc.Label("simulation manipulation"),
                    dcc.Dropdown(["a", "b", "c"]),
                ], width=5),
                        )
            ],
                style={'width': '100%', 'height': '100%'},
                fluid=True,
                className="mt-4",
            )

            return container
        else:
            return {}

    raise PreventUpdate


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        [
            dbc.NavItem(dbc.NavLink("Home", href="/")),
        ],
        brand="City Traffic Simulator PROD",
        brand_href="#",
        color="secondary",
        dark=True,
    ),
    dropdown_container,
    result_container,
    additional_handlers,
])


#@memoization_cache.memoize(timeout=TIMEOUT)  # in seconds
def get_attributes_pie_chart(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


def get_speed_heatmap(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


def get_acceleration_heatmap(map_hash, run_id, settings_hash):
    return integration.placeholder_chart()


def get_simulation_replay(map_hash : str, settings_hash : str, run_id : str, chart_type: str) -> go.Figure:
    import requests
    api_url = 'https://ctsbackend.bieda.it/api/processed/find'
    headers = {
        'ApiKey': '1234'
    }
    params = {
        'SettingsHash': settings_hash,
        'MapHash': map_hash,
        'RunId': run_id,
        'ChartType': 'POSITION_HEATMAP'
    }

    ic(params)

    response = requests.get(url=api_url, headers=headers, params=params)
    ic(response)

    # load json to object
    # content = content.replace('"_id" : ObjectId("638361e8e21a30ba017e8db7"), ', '')
    # content = content.replace('\\\\', '\\')
    # print(content)
    loaded_json = json.loads(response.content)
    frame = loaded_json.get("Data")
    ic(frame)
    # frame = json.loads(frame)
    metadata = loaded_json.get("Metadata")
    min_x, max_x, min_y, max_y = metadata.get("min_x"), metadata.get("max_x"), metadata.get("min_y"), metadata.get(
        "max_y")
    min_x, max_x, min_y, max_y = -10, 10, -10, 10
    scale_factor = 100
    # ic(min_x, min_y, max_y, max_x)
    dataframe_to_plot = frame
    dataframe_to_plot['display_size'] = 20
    dataframe_to_plot['display_color'] = 'red'




    fig = px.scatter(dataframe_to_plot,
                     x="x",
                     y="y",
                     # nbinsx = 10,
                     #    nbinsy = 10,
                     animation_frame="frame",
                     color="display_color",
                     animation_group="id",
                     hover_name="id",
                     size="display_size",
                     log_x=False,
                     size_max=20,
                     range_x=[metadata['min_x'], metadata['max_x']],
                     range_y=[metadata['min_y'], metadata['max_y']],
                     template="plotly_dark",

                     )
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000 / (
                metadata.get('frames_per_second') or 6)
    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # fig.update_layout(xaxis=dict(showgrid=False),
    #                   yaxis=dict(showgrid=False)
    #                   )
    # fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
    # fig.update_layout(xaxis_visible=False, xaxis_showticklabels=False)


    fig.update_layout(
        shapes=[

            # Cubic Bezier Curves
            dict(
                type="path",
                path="M 1,4 C 2,8 6,4 8,8",
                line_color="MediumPurple",
            ),

        ]
    )
    return fig


def get_chart(map_hash: str, settings_hash: str, run_id: str, chart_type: str) -> Union[Figure, dict]:
    # wait for 60 seconds five times
    # ic("waiting for 5 seconds")
    # for i in range(5):
    #     ic(f"waiting {i + 1}")
    #     time.sleep(1)

    if chart_type == 'replay simulation':
        return get_simulation_replay(map_hash, settings_hash, run_id, chart_type)
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
    elif chart_type:
        return {}
    else:
        return {}


def get_position_heatmap(map_hash, run_id, settings_hash):
    import requests
    api_url = 'https://ctsbackend.bieda.it/api/processed/find'
    headers = {
        'ApiKey': '1234'
    }
    params = {
        'SettingsHash': settings_hash,
        'MapHash': map_hash,
        'RunId': run_id,
        'ChartType': 'POSITION_HEATMAP'
    }
    response = requests.get(url=api_url, headers=headers, params=params)
    # load json to object
    # content = content.replace('"_id" : ObjectId("638361e8e21a30ba017e8db7"), ', '')
    # content = content.replace('\\\\', '\\')
    # print(content)
    loaded_json = json.loads(response.content)
    frame = loaded_json.get("Data")
    ic(frame)
    # frame = json.loads(frame)
    metadata = loaded_json.get("Metadata")
    min_x, max_x, min_y, max_y = metadata.get("min_x"), metadata.get("max_x"), metadata.get("min_y"), metadata.get(
        "max_y")
    min_x, max_x, min_y, max_y = -10, 10, -10, 10
    scale_factor = 100
    # ic(min_x, min_y, max_y, max_x)
    df = frame
    # mask = df.other_filterable_car_attributes.apply(lambda x: 'red' in x)
    # df_filtered_red = df[mask]
    # ic(df.tail(20))


    #df = dataframe_to_plot
    #df['z'] = {i : 1 for i in range(len(df))}
    df['frame'] = {i : i for i in range(len(df))}
    ic("generating chart")


    fig = px.density_heatmap(df,
                             nbinsx=100,
                             nbinsy=100,
                             x="x",
                             y="y",
                             #animation_frame="frame",
                             #marginal_y="histogram",
                             #marginal_x="histogram",
                             #histfunc='sum',
                             title="Density heatmap",
                             template="plotly_dark",
                             #animation_frame="frame",
                             #animation_group="id",

                             #animation_group="id",
                             #hover_name="id",

                             )

    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )

    # fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000 / (
    #             simulation_metadata.get('frames_per_second') or 6)
    return fig


@memoization_cache.memoize(timeout=30)
def get_matching_simulation_from_backend(map_hash, settings_hash, run_id, chart_type):
    return integration.get_matching_simulations(map_hash, settings_hash, run_id, chart_type)

# health check endpoint returns 200 if app is running
@app.server.route('/health')
def health():
    from flask import  make_response
    return make_response({}, 200)

if __name__ == '__main__':
    app.run_server(port=8095, debug=True)
