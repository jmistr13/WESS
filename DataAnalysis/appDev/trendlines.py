# Page 2: Trendlines

import dash
import pandas as pd
from dash import html, dcc, callback, Input, Output
import plotly.express as px
from df_customMethods import *

filename = 'DataAnalysis/appDev/data2.csv'

df = pd.read_csv(filename, usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                          comment='#', parse_dates=['transmitDateTime'])
#print(df)

# Ranges for pollutants for cmap
pollutant_ranges = {
    # Values in PPM
    'CO': [0, 50],
    'NH3': [0, 50],
    'NO2': [0, 3],
    'TDS': [0, 500],
    'turbidity': [0, 10] 
}

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

                dcc.Checklist(options=[{'label':'CO', 'value':'CO'},
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
        html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
    ])

def update_graph(selectedPollutants, selectedSensor):
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

    fig = px.scatter()

    for pollutant in selectedPollutants:
        if pollutant in dfThis.columns:  # Ensure the pollutant exists in the DataFrame
            fig.add_scatter(
                x=dfThis['transmitDateTimeFormatted'],
                y=dfThis[pollutant],
                mode='lines+markers',
                marker=dict(color=pollutant_colors[pollutant], size=6,symbol='circle'),
                name=pollutant,
                hovertemplate=f'{pollutant}: '+'%{y}<br>Time: %{x|%H:%M}<extra></extra>'
            )
    
    # Update layout
    fig.update_layout(
        hovermode='x unified',
        title=f"Pollutants at {selectedSensor}",
        xaxis_title="DateTime",
        yaxis_title="Concentration (PPM)",
        xaxis=dict(tickformat="%m-%d-%Y", type='date'),
        legend=dict(
            orientation='h',
            x=0.5, y=1,
            xanchor='center', yanchor='bottom',
            itemclick=False, itemdoubleclick=False,
        ),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    
    return fig

def register_callbacks(wessApp):
    wessApp.callback(
        Output('trendline-graph', 'figure'),
        Input('data-select', 'value'),
        Input('sensor-select', 'value')
    )(update_graph)
