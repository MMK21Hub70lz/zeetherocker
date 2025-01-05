import collections
from datetime import date
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
from dash_core_components.Store import Store
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from numpy import save
import plotly.express as px
import pandas as pd

from app import app

# import components
from components.upload.upload import Upload
from components.download.download import Download
from components.oversampling.oversampling import Oversampling
from components.tab.tabs import Tabs

# import algorithm
from algorithm.sigma import Sigma
from algorithm.oversample import get_oversampling_data
from algorithm.read_data import generate_df

Layout = dbc.Row([
            dbc.Col([
                    html.Div([
                        html.H5("Support .txt"),
                        Upload,
                        html.Div(id="upload-message"),
                        dcc.Store(id="raw-data-store"),
                        dcc.Store(id="oversampling-data-store"),
                        dcc.Store(id="FT-data-store")
                    ]),
                    html.Hr(),
                    html.Div([
                        html.H5("Example data"),
                        dbc.Button("Load Example data", id="load-example", 
                                   color="primary", style={"margin": "5px"})
                    ]),
                    html.Hr(),
                    Oversampling,
                    html.Hr(),
                    Download
                    ], width=3)
            , dbc.Col([Tabs], width=True)
])

# ================ Upload callback ========================

"""
Trigger when the experiental data(raw data) uploaded  
"""
@app.callback(
    Output("raw-data-store", "data"),
    Output("upload-message", "children"),
    Input("upload", "contents"),
    State("upload", "filename"),
    prevent_initial_call=True
)
def store_raw_data(content, file_name):
    df = generate_df(content)

    data = {
        "x" : df[0],
        "y" : df[1],
    }

    upload_messge = "The upload file {} with {} lines".format(file_name, len(df))

    return data, upload_messge

"""
Trigger when the experiental data(raw data) has already uploaded
and the oversampling button clicked with the oversampling ntimes.
"""
@app.callback(
    Output("oversampling-data-store", "data"),
    Input("oversampling-btn", "n_clicks"),
    State("upload", "contents"),
    State("oversampling-input", "value")
)
def store_oversampling_data(n_clicks, content, ntimes):
    if n_clicks is None or content is None or ntimes is None:
        raise PreventUpdate

    # avoid floor number
    ntimes = int(ntimes)
    x, y = get_oversampling_data(content=content, ntimes=ntimes)

    data = {
        "x" : x,
        "y" : y,
    }

    return data

"""
Trigger when the experiental data(raw data) or oversampling data changed
"""
app.clientside_callback(
    ClientsideFunction(
        namespace="clientsideSigma",
        function_name="tabChangeFigRender"
    ),
    Output("sigma-display", "figure"),
    Input("raw-data-store", "data"),
    Input("oversampling-data-store", "data"),
    Input("oversampling-render-switch", "value"),
    prevent_initial_call=True
)

# ================ Download callback ========================

@app.callback(
    Output("download-text", "data"),
    Output("download-message", "children"),
    Input("download-btn", "n_clicks"),
    State("begin-line-number", "value"),
    State("end-line-number", "value"),
    State("oversampling-data-store", "data"),
    prevent_initial_call=True,
)
def download(n_clicks, beginLineIdx, endLineIdx, data):
    if data is None:
        raise PreventUpdate

    # avoid floor number
    beginLineIdx = int(beginLineIdx)
    endLineIdx   = int(endLineIdx)
    if beginLineIdx >= endLineIdx:
        return None, "Invaild parameters"
    
    len = endLineIdx - beginLineIdx

    try:
        saving_x_list = data.get("x")[beginLineIdx:endLineIdx+1]
        saving_y_list = data.get("y")[beginLineIdx:endLineIdx+1]
    except:
        # if the idx is out of range, say, endLineIdx > len(x)
        saving_x_list = data.get("x")[beginLineIdx:]
        saving_y_list = data.get("y")[beginLineIdx:]
    else:
        saving_df = pd.DataFrame({"x": saving_x_list, "y": saving_y_list})

    return dcc.send_data_frame(saving_df.to_csv, "data.txt"), "Download OK !"    

# ================ FT callback ========================

