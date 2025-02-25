# Page 1: Map and Time Series
# Default page

import dash
from dash import html, dcc, callback, Input, Output
#import plotly.graph_objects as go
import plotly.express as px

from df_customMethods import * #import all custom methods for data frames

def layout():
    return html.Div([
        html.Div([
            html.H2('Pollutant to Display'), #text above checklist

            dcc.RadioItems(options=[
                {'label':'CO', 'value':'CO'},
                {'label':'NH3', 'value':'NH3'},
                {'label':'NO2', 'value':'NO2'},
                {'label':'TDS', 'value':'TDS'},
                {'label':'Turbidity', 'value':'turbidity'}],
                value='CO', #default selected
                labelStyle={"display": "inline-flex", "align-items": "left", "margin-right": "15px","accent-color": "#20A4F3"}, #style options
                id='data-select')
            ], style={"flex": "1",'align-items':'center',"text-align":"center","padding-right":'0%'}),

        html.Br(), #break

        #Component to display map
        dcc.Graph(id='sensor-map')
    ])

#generates map based on changes for checked data
def update_map(selected_values):
    df_recent = loadAndProcessData() #this is the real hack, generating a new df_recent everytime the map is updated, probably computationally heavy
    #alternative to doing this is using a dcc store, but it requires dataframe to convert to JSON, messes with the formatting of some of the numbers?

    fig = px.scatter_mapbox(
        df_recent, #dataframe
        lat='lat',
        lon='lon',
        hover_name='sensorName', #name of sensor
        hover_data=selected_values,
        center=dict(lat=df_recent['lat'].mean(), lon=df_recent['long'].mean()), # Places center of map at average lat and long
        zoom=14, # Arbitrary value, default zoom value for map 
        map_style='outdoors'
    )
    # Update hovertext based on checklist values
    hovertext = []
    if 'CO' in selected_values:
        hovertext.append(df_recent['CO'].astype(str))
    if 'NH3' in selected_values:
        hovertext.append(df_recent['NH3'].astype(str))
    if 'NO2' in selected_values:
        hovertext.append(df_recent['NO2'].astype(str))
    if 'TDS' in selected_values:
        hovertext.append(df_recent['TDS'].astype(str))
    if 'turbidity' in selected_values:
        hovertext.append(df_recent['turbidity'].astype(str))

    # Combine selected hovertext values
    combined_hovertext = ['<br>'.join(item) for item in zip(*hovertext)]
    
    # Update the map figure with new hovertext
    fig.update_traces(hovertext=combined_hovertext)
    fig.update_layout()

    return fig

def register_callbacks(wessApp):
    wessApp.callback(
        Output('sensor-map', 'figure'),
        Input('data-select', 'value')
    )(update_map)

def loadAndProcessData():
    df = pd.read_csv('data2.csv', usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#') #data2 is a larger one I had chatGPT make
    df_new = mostRecentValidLoc(df) #TODO: Consider making a mode or swtich that changes which custom method we use?
    df_new = df_new.fillna('') #Filling nan with empty string,
    df_new.to_csv('newdata.csv', index=True)
    return df_new

#TODO: see if we can load map before tab to avoid loading errors
