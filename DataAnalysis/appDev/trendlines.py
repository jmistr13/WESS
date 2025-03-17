# Page 2: Trendlines

import dash
import pandas as pd
from dash import html, dcc, callback, Input, Output
import plotly.express as px

from df_customMethods import *

filename = csv_path()

df = loadAndProcessData(filename)
sensor_names=df['sensorName'].unique() # pull names of sensors in csv
pollutant_names = ['CO','NH3','NO2','TDS','turbidity']

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
        html.Div([
            html.Div([
                html.H2('Select a Sensor:',style={'flex': '1','text-align':'right','align-items':'right'}), #text for selector

                html.Div([
                    dcc.RadioItems(sensor_names,sensor_names[0],inline=True,
                        labelStyle={"color":"D0C8CC","margin-right": "20px","accent-color": "#20A4F3"}, #styling of text
                        id='sensor-select')
                ], style={'flex': '1','text-align':'left','margin-left':'20px'})
            ], style={'display': 'flex','align-items':'center', 'text-align':'center','margin-right':'15%'})]),

        html.P('Toggle displayed pollutants by clicking on it in the legend. Double click to isolate pollutant.',
               style={"text-align":"center",'align-items':'center','color':'#f2f4ff'}),

        dcc.Graph(id='trendline-graph'),

        #update graph content periodically
        dcc.Interval(
            id='interval-component',
            interval=5000, # in milliseconds
            n_intervals=0
        ),
    ])

def update_graph(selectedSensor, n_intervals):
    global df, sensor_names
    df = loadAndProcessData(filename)
    sensor_names=df['sensorName'].unique()

    dfThis = df[df['sensorName'] == selectedSensor].copy()  # Filter by selected sensor
    
    # Ensure 'transmitDateTime' is in datetime format
    dfThis['transmitDateTimeFormatted'] = pd.to_datetime(dfThis['transmitDateTime'], errors='coerce')

    # Drop any NaT (invalid datetime) values
    dfThis = dfThis.dropna(subset=['transmitDateTimeFormatted'])

    # Sort data by datetime to ensure correct time series plotting
    dfThis = dfThis.sort_values(by='transmitDateTimeFormatted')

    # Keep only latest 50 values
    dfThis = dfThis.tail(25)

    # Ensure we have multiple timestamps
    if dfThis['transmitDateTimeFormatted'].nunique() <= 1:
        print("Warning: Only one unique timestamp found for", selectedSensor)

    fig = px.scatter() #create plot

    #add data to plot for each checked value
    for pollutant in pollutant_names:
        if pollutant in pollutant_names:  # Ensure the pollutant exists in the DataFrame
            fig.add_scatter(
                x=dfThis['transmitDateTimeFormatted'],
                y=dfThis[pollutant],
                mode='lines+markers',
                marker=dict(color=pollutant_colors[pollutant], size=6,symbol='circle'), # marker on graph
                name=pollutant,
                hovertemplate=f'{pollutant}: '+'%{y}<br>Time: %{x|%H:%M:%S}<extra></extra>' # hovertext display
            )
    
    # Update layout
    fig.update_layout(
        hovermode='closest', # style of hover text
        title=f"Pollutants at {selectedSensor}", # figure title
        xaxis_title="DateTime", # x axis
        yaxis_title="Concentration (PPM)", # y axis
        xaxis=dict(tickformat="%m-%d-%Y", type='date'), # convert datetime format
        legend=dict( #format legend
            orientation='h',
            x=0.5, y=1,
            xanchor='center', yanchor='bottom',
        ),
        margin=dict(l=40, r=40, t=40, b=40), # space for legend
        height=375,
    )
    
    return fig

def register_callbacks(wessApp):
    wessApp.callback(
        Output('trendline-graph', 'figure'), # graph
        Input('sensor-select', 'value'), # radio
        Input('interval-component', 'n_intervals')  # time refresh
    )(update_graph)
