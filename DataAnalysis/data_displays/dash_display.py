# Python program that displays data using dash

import dash
import numpy as np
from df_customMethods import *
from dash import dcc, html
#import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd

#from DataAnalysis.data_displays.plotly_display import sensor_data, latitudes, longitudes

def loadAndProcessData():
    df = pd.read_csv('data.csv', usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#')
    df_new = mostRecentValidLoc(df)
    df_new = df_new.fillna('')
    df_new.to_csv('newdata.csv', index=True)
    return df_new

df_recent = loadAndProcessData()
print(df_recent)

'''# Create the plot
fig = go.Figure(go.Scattermap(
    lat=latitudes,
    lon=longitudes,
    mode='markers+text',
    marker=dict(
        size=10,
        color='blue'
    ),
    text=labels,
    hoverinfo='text',
    center=dict(lat=47.6097, lon=-122.3331)
    #customdata=[sensorCO, sensorNH3]   # This holds the sensor data
))'''

#TODO: Define healthy ranges for each pollutant
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

@app.callback(
    Input('update-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_data(n_clicks):
    """Reload and process data when the update button is clicked."""
    global df_recent
    df_recent = loadAndProcessData()
    #return df_recent


# Callback to update the sensor data text when a point is clicked
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

# Layout of the app
app.layout = html.Div([
    html.H1("WESS Data"),
    dcc.Store(id='stored-data'),
    dcc.Dropdown(
        id='colorDropdown',
        options=[
            #{'label': 'test', 'value': 'test'},
            {'label': 'CO', 'value': 'CO'},
            {'label': 'NH3', 'value': 'NH3'},
            {'label': 'NO2', 'value': 'NO2'},
            {'label': 'TDS', 'value': 'TDS', 'disabled': True}, #Disabling these for now
            {'label': 'Turbidity', 'value': 'turbidity', 'disabled':True},
        ],
        placeholder='Select a pollutant to map',
        optionHeight=50,
        clearable=False
    ),
    html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
    dcc.Graph(id='map'),
    html.Div(id='sensor-data')
])

# Run the app
if __name__ == '__main__':
    #app.run(host='10.18.158.12', port=8050) #The host IP was my local IP on UW wifi, was able to host webserver and access it with phone
    app.run(debug=True)
