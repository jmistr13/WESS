# from dash import html
# from customMethods import *
#
# #Just copying imoprts here
# import dash
# from dash import html, dcc, callback, Input, Output
# #import plotly.graph_objects as go
# import plotly.express as px
#
# from df_customMethods import * #import all custom methods for data frames
#
# filename = csv_path()
# df = loadAndProcessData(filename)
#
# def layout():
#     return html.Div([ #HTML that defines the connections page
#             html.H2("Would you like to see this data on your mobile device?"),
#             html.P([
#                 "Connect to ",
#                 html.Strong(get_wifi_name()),  # Makes the Wi-Fi name bold
#                 " and navigate to ",
#                 html.Strong(f"{get_local_ip()}:8050"),  # Makes the IP address bold
#                 " on your mobile device."
#             ]),
#             html.Button("Download Current Data", id="btn-data-download"),
#             dcc.Download(id='data-download')
#         ])
#
# def generate_download():
#     return dcc.send_data_frame(df.to_csv, 'WESS_Current_Data.csv') #TODO: maybe change this to the current date and time as the file name insteaed?
#
# def register_callbacks(wessApp):
#     wessApp.callback(
#         Output('data-download', 'data'), # graph
#         Input('btn-data-download', 'n_clicks'), #
#     ) (generate_download)

from dash import html, dcc, callback, Input, Output, no_update
import dash
from datetime import datetime
import pandas as pd

# Assuming these functions are defined in customMethods and df_customMethods
from customMethods import get_wifi_name, get_local_ip
from df_customMethods import *

# Load and process data
filename = csv_path()
df = loadAndProcessData(filename)

def layout():
    return html.Div([  # HTML that defines the connections page
        html.H2("Would you like to see this data on your mobile device?"),
        html.P([
            "Connect to ",
            html.Strong(get_wifi_name()),  # Makes the Wi-Fi name bold
            " and navigate to ",
            html.Strong(f"{get_local_ip()}:8050"),  # Makes the IP address bold
            " on your mobile device."
        ]),
        html.Button("Download Current Data", id="btn-data-download"),
        dcc.Download(id='data-download')
    ])

#
def register_callbacks(wessApp):
    @wessApp.callback(
        Output('data-download', 'data'),  # Output is the download component
        Input('btn-data-download', 'n_clicks'),  # Input is the button click
        #prevent_initial_call=True  # Prevents the callback from firing on page load
    )
    def generate_download(n_clicks): #TODO: Figure out how to make this formatted like the other tab pages, just put (generate_download) here and have the def somewhere else
        if n_clicks is None:
            return no_update  # Prevents download if the button hasn't been clicked
        print(filename)

        # Generate a filename with the current date and time
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        downloadFilename = f"WESS_Current_Data_{current_time}.csv"

        # Basically reading data2.csv here (which I assume is the most up to date data) and formats it with send_string so dcc can make it a download
        # Could totally make this point to a different file or even a dataframe if need be
        with open(filename, 'r') as file:
            return dcc.send_string(file.read(), filename=downloadFilename)


