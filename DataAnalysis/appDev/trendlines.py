# Page 2: Trendlines

import dash
import pandas as pd
from dash import html, dcc, callback, Input, Output
import plotly.express as px

from df_customMethods import *

filename = csv_path()

df = pd.read_csv(filename, usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                          comment='#', parse_dates=['transmitDateTime'])
last_modified_time = get_csv_modified_time(filename) # make sure csv stays up to date

#print(df)
# Colors for trendline plot
pollutant_colors = {
    'CO': '#5BC0EB',
    'NH3': '#FDE74C',
    'NO2': '#9BC53D',
    'TDS': '#CA054D',
    'turbidity': '#FA7921'
}

def layout():
    return html.Div([ #HTML that defines the Graph page
        html.Div([html.Div([
            html.H2('Select a Sensor'), #text above selector
                dcc.RadioItems(['The Quad', 'Sylvan Grove', 'Union Bay', 'Arboretum'], 'The Quad',inline=True,
                        labelStyle={"color":"D0C8CC","margin-right": "20px","accent-color": "#20A4F3"}, #styling of text
                        id='sensor-select')
            ], style={"flex": "1",'align-items':'center',"text-align":"center","padding-left":'16%'}),

            html.Div([
                html.H2('Pollutants to Display'), #text above checklist

                dcc.Checklist(options=[
                    {'label':'CO', 'value':'CO'},
                    {'label':'NH3', 'value':'NH3'},
                    {'label':'NO2', 'value':'NO2'},
                    {'label':'TDS', 'value':'TDS'},
                    {'label':'Turbidity', 'value':'turbidity'}],
                    value=['CO','NH3','NO2'], #default selected
                    labelStyle={"display": "inline-flex", "align-items": "left", "margin-right": "15px","accent-color": "#20A4F3"}, #style options
                    id='data-select')
            ], style={"flex": "1",'align-items':'center',"text-align":"center","padding-right":'16%'})
            ], style={"display": "flex", "gap": "20px", 'align-items':'center'}),

        html.Br(),

        dcc.Graph(id='trendline-graph'),

        #update graph content periodically
        dcc.Interval(
            id='interval-component',
            interval=5000, # in milliseconds
            n_intervals=0
        ),
    ])

def update_graph(selectedPollutants, selectedSensor, n_intervals):
    global df, last_modified_time

    # Check if the CSV file has been modified
    current_modified_time = get_csv_modified_time(filename)
    if current_modified_time > last_modified_time:
        df = loadAndProcessData(filename)  # Reload the data
        last_modified_time = current_modified_time  # Update the last known modification time

    dfThis = df[df['sensorName'] == selectedSensor].copy()  # Filter by selected sensor
    
    # Ensure 'transmitDateTime' is in datetime format
    dfThis['transmitDateTimeFormatted'] = pd.to_datetime(dfThis['transmitDateTime'], errors='coerce')

    # Drop any NaT (invalid datetime) values
    dfThis = dfThis.dropna(subset=['transmitDateTimeFormatted'])

    # Sort data by datetime to ensure correct time series plotting
    dfThis = dfThis.sort_values(by='transmitDateTimeFormatted')

    # Ensure we have multiple timestamps
    if dfThis['transmitDateTimeFormatted'].nunique() <= 1:
        print("Warning: Only one unique timestamp found for", selectedSensor)

    fig = px.scatter() #create plot

    #add data to plot for each checked value
    for pollutant in selectedPollutants:
        if pollutant in dfThis.columns:  # Ensure the pollutant exists in the DataFrame
            fig.add_scatter(
                x=dfThis['transmitDateTimeFormatted'],
                y=dfThis[pollutant],
                mode='lines+markers',
                marker=dict(color=pollutant_colors[pollutant], size=6,symbol='circle'), # marker on graph
                name=pollutant,
                hovertemplate=f'{pollutant}: '+'%{y}<br>Time: %{x|%H:%M}<extra></extra>' # hovertext display
            )
    
    # Update layout
    fig.update_layout(
        hovermode='x unified', # style of hover text
        title=f"Pollutants at {selectedSensor}", # figure title
        xaxis_title="DateTime", # x axis
        yaxis_title="Concentration (PPM)", # y axis
        xaxis=dict(tickformat="%m-%d-%Y", type='date'), # convert datetime format
        legend=dict( #format legend
            orientation='h',
            x=0.5, y=1,
            xanchor='center', yanchor='bottom',
            itemclick=False, itemdoubleclick=False, #disable clicking on legend features
        ),
        margin=dict(l=40, r=40, t=40, b=40), # space for legend
    )
    
    return fig

def register_callbacks(wessApp):
    wessApp.callback(
        Output('trendline-graph', 'figure'), # graph
        Input('data-select', 'value'), # check
        Input('sensor-select', 'value'), # radio
        Input('interval-component', 'n_intervals')  # time refresh
    )(update_graph)
