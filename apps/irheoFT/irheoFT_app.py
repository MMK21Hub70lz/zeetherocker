import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import time
import pandas as pd

from app import app

# import components and its generation
from components.upload.upload import upload_component_generate
from components.download.download import download_component_generate
from components.oversampling.oversampling import oversampling_component_generate
from components.tab.tabs import ft_tabs_generate
from components.loglinearswitch.axisSwitch import vertical_axis_swith

# import algorithm
from algorithm.oversample import get_oversampling_data
from algorithm.read_data import convert_lists_to_df, generate_df, generate_df_from_local
from algorithm.pwft import ftdata, fast_ftdata

# Using your own app name. Can't be same.
prefix_app_name = "FTAPP"

# TODO need modify and change the algorithm plus with function
Layout = dbc.Row([
            dbc.Col([
                    html.H5("Support .txt"),
                    html.Div([
                        upload_component_generate("FTAPP-upload"),
                        dcc.Store(id="FTAPP-raw-data-store", storage_type="session"),
                        dcc.Store(id="FTAPP-oversampling-data-store", storage_type="session"),
                        dcc.Store(id="FTAPP-ft-data-store", storage_type="session"),
                        dcc.Loading([dcc.Store(id="FTAPP-oversampled-ft-data-store", storage_type="session")],
                            id="FTAPP-full-screen-mask", fullscreen=True, debug=True)
                    ], className="btn-group me-2"),
                    html.Div([dbc.Button("Load Example data", id="FTAPP-load-example", 
                              color="primary", style={"margin": "5px"})],
                              className="btn-group me-2"),
                    html.Div(id="FTAPP-upload-message"),
                    # This is just for show the loading message
                    html.Div(id="FTAPP-loading-message"),
                    html.Hr(),
                    oversampling_component_generate(prefix_app_name),
                    vertical_axis_swith(prefix_app_name),
                    html.Hr(),
                    download_component_generate(prefix_app_name)
                    ], width=3),
            dbc.Col(ft_tabs_generate(prefix_app_name), width=True),
            # Loading
])

# ================ Upload callback ========================

"""
Trigger when the experiental data(raw data) uploaded  
"""
@app.callback(
    Output("FTAPP-raw-data-store", "data"),
    Output("FTAPP-ft-data-store", "data"),
    # Output("FTAPP-upload-message", "children"),
    Output("FTAPP-loading-message", "children"),
    Input("FTAPP-upload", "contents"),
    Input("FTAPP-load-example", "n_clicks"),
    Input("FTAPP-g_0", "value"),
    Input("FTAPP-g_inf", "value"),
    State("FTAPP-upload", "filename"),
    prevent_initial_call=True
)
def store_raw_data(content, n_clicks, g_0, g_inf,file_name):
    # Deciding which raw_data used according to the ctx 
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df = pd.DataFrame()
    if button_id == "FTAPP-load-example":
        path = "./example_data/ft/example.txt"
        df = generate_df_from_local(path)
    else:
        if content is None:
            raise dash.exceptions.PreventUpdate
        
        df = generate_df(content)

    # save file_name and lens for message recovering when app changing
    raw_data = {
        "x": df[0],
        "y": df[1],
        "filename": file_name,
        "lines": len(df)
    }

    # default g_0: 1, g_inf: 0
    g_0 = 1 if g_0 is None else float(g_0)
    g_inf = 0 if g_inf is None else float(g_inf)
    
    # omega, g_p, g_pp = ftdata(df, g_0, g_inf, False)
    # fast FT processing
    omega, g_p, g_pp, non_time_g_p, non_time_g_pp = fast_ftdata(df, g_0, g_inf, False)

    ft_data = {
        "x": omega,
        "y1": g_p,
        "y2": g_pp,
        "non_time_y1": non_time_g_p,
        "non_time_y2": non_time_g_pp
    }

    """
    Don't pass any string to this return. This component only for loading message.
    """
    return raw_data, ft_data, ""

"""
Trigger when the experiental data(raw data) has already uploaded
and the oversampling button clicked with the oversampling ntimes.
"""
@app.callback(
    Output("FTAPP-oversampling-data-store", "data"),
    Output("FTAPP-oversampled-ft-data-store", "data"),
    Input("FTAPP-oversampling-btn", "n_clicks"),
    Input("FTAPP-g_0", "value"),
    Input("FTAPP-g_inf", "value"),
    State("FTAPP-raw-data-store", "data"),
    State("FTAPP-oversampling-input", "value")
)
def store_oversampling_data(n_clicks, g_0, g_inf, data, ntimes):
    if n_clicks is None or data is None or ntimes is None:   
        # return None, None  
        # time.sleep(10)   
        raise dash.exceptions.PreventUpdate

    # avoid float number
    ntimes = int(ntimes)
    df = convert_lists_to_df(data)
    x, y = get_oversampling_data(df, ntimes)

    data = {
        "x": x,
        "y": y,
    }

    # default g_0: 1, g_inf: 0
    g_0 = 1 if g_0 is None else float(g_0)
    g_inf = 0 if g_inf is None else float(g_inf)

    # This function takes lots of time
    # omega, g_p, g_pp = ftdata(df, g_0, g_inf, True, ntimes)
    # fast FT
    omega, g_p, g_pp, non_time_g_p, non_time_g_pp = fast_ftdata(df, g_0, g_inf, True, ntimes)

    oversampled_ft_data = {
        "x": omega,
        "y1": g_p,
        "y2": g_pp,
        "non_time_y1": non_time_g_p,
        "non_time_y2": non_time_g_pp
    }

    return data, oversampled_ft_data

"""
Input(Sigma) Renedr ----- First tab
Trigger when the experiental data(raw data) or oversampling data changed
"""
app.clientside_callback(
    ClientsideFunction(
        namespace="clientsideSigma",
        function_name="tabChangeFigRender"
    ),
    Output("FTAPP-sigma-display", "figure"),
    Input("FTAPP-raw-data-store", "data"),
    Input("FTAPP-oversampling-data-store", "data"),
    Input("FTAPP-oversampling-render-switch", "value"),
    # prevent_initial_call=True
)

"""
Re & Im Renedr ----- Second tab
Trigger when the experiental data(raw data) or oversampling data changed
"""
app.clientside_callback(
    ClientsideFunction(
        namespace="clientsideFT",
        function_name="tabChangeFTfigRender"
    ),
    Output("FTAPP-FT-display", "figure"),
    Input("FTAPP-ft-data-store", "data"),
    Input("FTAPP-oversampled-ft-data-store", "data"),
    Input("FTAPP-oversampling-render-switch", "value"),
    Input("FTAPP-time-derivative", "value"),
    Input("FTAPP-vertical-axis-switch", "value")
    # prevent_initial_call=True
)

app.clientside_callback(
    ClientsideFunction(
        namespace="clientsideMessageRec",
        function_name="uploadMessage"
    ),
    Output("FTAPP-upload-message", "children"),
    Input("FTAPP-raw-data-store", "data"),
    # prevent_initial_call=True
)

# ================ Download callback ========================

@app.callback(
    Output("FTAPP-download-text", "data"),
    Output("FTAPP-download-message", "children"),
    Input("FTAPP-download-btn", "n_clicks"),
    State("FTAPP-begin-line-number", "value"),
    State("FTAPP-end-line-number", "value"),
    State("FTAPP-oversampling-data-store", "data"),
    prevent_initial_call=True,
)
def download(n_clicks, beginLineIdx, endLineIdx, data):
    if data is None:
        raise dash.exceptions.PreventUpdate

    # avoid float number
    beginLineIdx = int(beginLineIdx)
    endLineIdx   = int(endLineIdx)
    if beginLineIdx >= endLineIdx:
        return None, "Invaild parameters"

    try:
        saving_x_list = data.get("x")[beginLineIdx:endLineIdx+1]
        saving_y_list = data.get("y")[beginLineIdx:endLineIdx+1]
    except:
        # if the idx is out of range, say, endLineIdx > len(x)
        saving_x_list = data.get("x")[beginLineIdx:]
        saving_y_list = data.get("y")[beginLineIdx:]
    else:
        saving_df = pd.DataFrame({"x": saving_x_list, "y": saving_y_list})
        # saving_file_name = data.get("file_name") + "_Complex Moduli.txt"
        saving_file_name = "download_FT_data.txt"

    return (dcc.send_data_frame(saving_df.to_csv,saving_file_name, 
                                header=False, index=False, 
                                sep='\t', encoding='utf-8'), 
                                "Download OK !") 

# ================ Loading address ========================

# @app.callback(
#     Output("FTAPP-full-screen-mask", "loading_state"),
#     Input("FTAPP-oversampled-ft-data-store", "data"),
#     prevent_initial_call=True,
# )
# def screen_loading(data):
#     # print(loading)
#     loading_state = {
#         "component_name": "FTAPP-oversampled-ft-data-store",
#         "prop_name": "data"
#     }

#     if data is None:
#         loading_state["is_loading"] = False
#         print(loading_state)
#         time.sleep(10)
#         return loading_state  

#     # print()
#     loading_state["is_loading"] = True

#     print(loading_state)
#     return loading_state