# Python program that displays data using dash

import dash
import numpy as np
import plotly.graph_objects

from df_customMethods import *
from dash import dcc, html
#import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd

#from DataAnalysis.data_displays.plotly_display import sensor_data, latitudes, longitudes

def loadAndProcessData():
    df = pd.read_csv('data2.csv', usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#') #data2 is a larger one I had chatGPT make
    df_new = mostRecentValidLoc(df) #TODO: Consider making a mode or swtich that changes which custom method we use?
    df_new = df_new.fillna('') #Filling nan with empty string,
    df_new.to_csv('newdata.csv', index=True)
    return df_new

df = pd.read_csv('data2.csv', usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#')
def updateMainDf():
    global df
    df = pd.read_csv('data2.csv', usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#')

df_recent = loadAndProcessData()
print(df_recent)

#TODO: Define healthy ranges for each pollutant, needed for coloring on the map
pollutant_ranges = {
    'test': [5, 6.7],
    'CO': [4.2, 4.5],
    'NH3': [0, 1],
    'NO2': [0, 0.5],
    'TDS': [0, 1],
    'turbidity': [0, 1]
}

# Create a Dash app
app = dash.Dash(__name__)

#Callback for update-button on map page
@app.callback(
    Input('update-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_data(n_clicks):
    """Reload and process data when the update button is clicked."""
    global df_recent
    df_recent = loadAndProcessData()
    updateMainDf()
    #return df_recent


# Callback to update the sensor data text on map page when a point is clicked
@app.callback(
    Output('sensor-data', 'children'),
    [Input('map', 'clickData')]
)
def display_sensor_data(clickData):
    if clickData is None:
        return "Click on a sensor point to see its data."

    # Get the point clicked
    point = clickData['points'][0]
    #customdata = point['customdata']
    label = point['hovertext']

    return (f"Sensor: {label} | CO: {df_recent.loc[df_recent['sensorName'] == label].CO.values[0]} | NH3: {df_recent.loc[df_recent['sensorName'] == label].NH3.values[0]} | NO2: {df_recent.loc[df_recent['sensorName'] == label].NO2.values[0]}")

# Callback to generate map, triggered either by changing colorDropdown or hitting update-button
@app.callback(
    Output('map', 'figure'),
    Input('colorDropdown', 'value'),
    Input('update-button', 'n_clicks') #Kinda a hack, running this callback on update-button press
)
def update_map(selectedPollutant, clicks):
    print(selectedPollutant)
    df_recent = loadAndProcessData() #this is the real hack, generating a new df_recent everytime the map is updated, probably computationally heavy
    #alternative to doing this is using a dcc store, but it requires dataframe to convert to JSON, messes with the formatting of some of the numbers?

    #TODO: consider using global df_recent, not updating dataframe when selectedPollutant changes might improve performance on the Pi
    fig = px.scatter_map( # Using plotly express, not graph objects
        df_recent,
        lat='lat',
        lon='long', # Keep in mind plotly refers to this as lon, but we call it long
        size=np.linspace(20, 20, len(df_recent)), # just making an array of 20's with length of df_recent, the size needs a value for every data point
        color=selectedPollutant, # whatever value is here is what will define the color of the points
        range_color=pollutant_ranges.get(selectedPollutant, [0,1]), #selectedPollutant
        #color_continuous_scale='Jet', #I quite like this one too
        color_continuous_scale=["rgb(0, 255, 0)", "rgb(120, 255, 0)", "rgb(255, 255, 0)", "rgb(255, 120, 0)", "rgb(255, 0, 0)"], # green to yellow to red
        center=dict(lat=df_recent['lat'].mean(), lon=df_recent['long'].mean()), # Places center of map at average lat and long
        zoom=14, #This zoom works well for campus size, this number has no real scale so its trial and error
        hover_name='sensorName',
        map_style='carto-positron',
        #mapbox_style='none',
        hover_data=dict(lat=False, long=False, transmitDateTime=True, CO=True, NH3=True, NO2=True, TDS=True, turbidity=True) #False removes from hover, true keeps it in
        #TODO: Figure out how to hide "size" in the hover data
    )

    # Set the layout for the map
    fig.update_layout(
        title="Sensor Locations with Most Recent Readings",
    )
    return fig

# Callback to generate graph over time, triggered by change in pollutant or sensor option
@app.callback(
    Output('graph', 'figure'),
    Input('graphDropdown', 'value'),
    Input('graphSensorNameDropdown', 'value' ),
)
def update_graph(selectedPollutant, selectedSensor):
    global df
    dfThis = df[df['sensorName'] == selectedSensor] #Getting only the needed sensor rows from the main dataframe
    dfThis.drop_duplicates(subset='transmitDateTime', keep='first', inplace=True) #Dropping any duplicates of transmit date and time, which one to keep should be arbitrary
    dfThis['transmitDateTimeFormatted'] = pd.to_datetime(dfThis['transmitDateTime']) #Want to keep "unformated" DateTime for readability, but scatter needs it formatted for graphing

    fig = px.scatter(
        dfThis,
        x='transmitDateTimeFormatted',
        y=selectedPollutant,
        hover_name='transmitDateTime',
        trendline='lowess' #TODO: This needs statsmodels package, remember to install on Pi dataV venv
        #hover_data=dict(selectedPollutant=True),
        #template=plotly.graph_objects.layout.Template()
    ).update_traces(mode='lines+markers') #If theres a "Value is trying to be set on a copy of a slice error its probably this line

    # Set the layout for the map
    fig.update_layout(
        title=f"{selectedPollutant} at {selectedSensor}",
    )
    return fig

app.layout = html.Div([
    html.H1("WESS"),
    dcc.Tabs(id='tabs', value='map-page', children=[
        dcc.Tab(label='Map', value='map-page'),
        dcc.Tab(label='Data Graphs', value='graph-page')
    ]),
    html.Div(id='tabs-content') #This HTML comes from the render_content function, that way it can be swapped out between pages
])

#This callback has all the acutal HTML definitions for the page other than the page tabs
@app.callback(Output('tabs-content', 'children'),
          Input('tabs', 'value'))
def render_content(tab):
    if tab == 'map-page':
        return html.Div([ #HTML that defines the map page
            #html.H2("Data"),
            dcc.Store(id='stored-data'), #keeping this just in case but I don't think ill use it
            dcc.Dropdown(
                id='colorDropdown',
                options=[
                    {'label': 'CO', 'value': 'CO'},
                    {'label': 'NH3', 'value': 'NH3'},
                    {'label': 'NO2', 'value': 'NO2'},
                    {'label': 'TDS', 'value': 'TDS', 'disabled': True},  # Disabling these for now
                    {'label': 'Turbidity', 'value': 'turbidity', 'disabled': True},
                ],
                placeholder='Select a pollutant to map',
                optionHeight=50,
                clearable=False
            ),
            dcc.Graph(id='map'),
            html.Div(id='sensor-data'),
            html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
        ])
    elif tab == 'graph-page':
        return html.Div([ #HTML that defines the Graph page
            #html.H2('Select a sensor to graph'),
            dcc.Dropdown(
                id='graphSensorNameDropdown',
                options=df['sensorName'].unique(),
                placeholder='Select a sensor',
                optionHeight=30,
                clearable=False
            ),
            dcc.Tabs(id='graphDropdown', value='CO', children=[ #I know it's called a dropdown, I dont feel like changing the name :p
                dcc.Tab(label='CO', value='CO'),
                dcc.Tab(label='NH3', value='NH3'),
                dcc.Tab(label='NO2', value='NO2'),
                dcc.Tab(label='TDS', value='TDS', disabled=True), #Disabling for now
                dcc.Tab(label='Turbidity', value='turbidity', disabled=True),
            ]),
            dcc.Graph(id='graph'),
            html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
        ])


# Run the app
if __name__ == '__main__':
    #app.run(host='10.18.158.12', port=8050) #The host IP was my local IP on UW wifi, was able to host webserver and access it with phone
    app.run(debug=True)
