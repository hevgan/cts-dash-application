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



layout = html.Div([
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
