# Python program that displays data using dash

import dash
from df_customMethods import *
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd

from DataAnalysis.data_displays.plotly_display import sensor_data, latitudes, longitudes

df = pd.read_csv('data.csv', usecols=['sensorName', 'lat', 'long', 'transmitDate', 'transmitHour', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                 comment='#') #TODO: combine transmitDate and transmitHour with a space in between, makes sorting by date much easier

df_recent = mostRecentValidLoc(df)
df_recent = df_recent.fillna('')
print(df_recent)
df_recent.to_csv('newdata.csv', index=True)


labels = []
latitudes = []
longitudes = []
sensor_data = []

for row in df_recent.itertuples():
    labels.append(row.sensorName)
    latitudes.append(row.lat)
    longitudes.append(row.long)


#print(df.loc[df['sensorName'] == 'Union Bay'].CO.values)

#  coordinates and sensor data

'''coordinates = [
    (47.6097, -122.3331, "Seattle", 23.5),  # Seattle, sensor reading = 23.5
    (48.7150, -122.4905, "Bellingham", 19.8),  # Bellingham, sensor reading = 19.8
    (46.8527, -121.7603, "Mount Rainier", 15.0)  # Mount Rainier, sensor reading = 15.0
]

# Extract latitudes, longitudes, labels, and data for plotting
latitudes = [lat for lat, lon, label, data in coordinates]
longitudes = [lon for lat, lon, label, data in coordinates]
labels = [label for lat, lon, label, data in coordinates]
sensor_data = [data for lat, lon, label, data in coordinates]'''

# Create the plot
'''fig = go.Figure(go.Scattermap(
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

fig = px.scatter_map( # Using plotly express, not graph objects
    df_recent,
    lat='lat',
    lon='long', # Keep in mind plotly refers to this as lon, but we call it long
    color='CO', # whatever value is here is what will define the color of the point, this could change to quickly visualize different pollutants
    range_color=[4.2, 4.5], #TODO: Figure out healthy ranges for all pollutants, perhaps make a dictionary
    center=dict(lat=df_recent['lat'].mean(), lon=df_recent['long'].mean()), # Places center of map at average lat and long
    zoom=14, #This zoom works well for campus size, this number has no real scale so its trial and error
    hover_name='sensorName',
    hover_data=dict(lat=False, long=False, transmitDate=True, transmitHour=True, CO=True, NH3=True, NO2=True, TDS=True, turbidity=True) #False removes from hover, true keeps it in
)

# Set the layout for the map
fig.update_layout(
    mapbox_style="carto-positron",  # You can choose other map styles (e.g., 'open-street-map')
    mapbox_center={"lat": 47.6097, "lon": -122.3331},  # Center the map on Seattle
    mapbox_zoom=7,  # Zoom level
    title="Sensor Locations with Data",
)

# Create a Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("WESS Data"),
    dcc.Dropdown(
        id='colorDropdown',
        options=[
            {'label': 'CO', 'value': 'CO'}, # dict(name='CO', range=[4.2, 4.5])
            {'label': 'NH3', 'value': 'NH3'}, # dict(name='NH3', range=[0, 1])
            {'label': 'NO2', 'value': 'NO2'}, # dict(name='NO2', range=[0, 0.5])
            {'label': 'TDS', 'value': 'TDS'}, # dict(name='TDS', range=[0, 1])
            {'label': 'Turbidity', 'value': 'turbidity'}, # dict(name='turbidity', range=[0, 1])
        ],
        value='CO',  # Default value
        clearable=False
    ),
    dcc.Graph(id='map', figure=fig),
    html.Div(id='sensor-data')
])


# Callback to update the sensor data when a point is clicked
""""@app.callback(
    Output('sensor-data', 'children'),
    [Input('map', 'clickData'), Input('colorDropdown', 'colorValue')]"""

@app.callback(
    Output('sensor-data', 'children'),
    [Input('map', 'clickData')]
)


def display_sensor_data(clickData):
    if clickData is None:
        return "Click on a sensor point to see its data."

    # Get the point clicked
    point = clickData['points'][0]
    customdata = point['customdata']
    label = point['hovertext']

    #return f"Sensor: {label} | Temperature: {data}C"
    return (f"Sensor: {label} | CO: {df_recent.loc[df_recent['sensorName'] == label].CO.values[0]} | NH3: {df_recent.loc[df_recent['sensorName'] == label].NH3.values[0]} | NO2: {df_recent.loc[df['sensorName'] == label].NO2.values[0]}")



# Run the app
if __name__ == '__main__':
    #app.run(host='10.18.158.12', port=8050) #The host IP was my local IP on UW wifi, was able to host webserver and access it with phone
    app.run(debug=True)
