# Python program that displays data using dash

import dash
from dash import dcc, html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd

from DataAnalysis.data_displays.plotly_display import sensor_data, latitudes, longitudes

df = pd.read_csv('data.csv', usecols=['sensorName', 'lat', 'long', 'transmitDate', 'transmitHour', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                 comment='#')
df['transmitDateTime'] = pd.to_datetime(df['transmitDate'] + ' ' + df['transmitHour'].astype(str))
df = df.sort_values(by=['sensorName', 'transmitDateTime'])

# Forward fill missing lat and long values within each sensorName group
df[['lat', 'long']] = df.groupby('sensorName')[['lat', 'long']].ffill()

# Drop the extra datetime column if not needed
df.drop(columns=['transmitDateTime'], inplace=True)

print(df.head())
#print(df['sensorName'])

labels = []
latitudes = []
longitudes = []
sensor_data = []
sensorCO = []
sensorNH3 = []

for row in df.itertuples():
    print(row.sensorName)
    labels.append(row.sensorName)
    latitudes.append(row.lat)
    longitudes.append(row.long)
    sensorCO.append(row.CO)
    sensorNH3.append(row.NH3)


print(df)

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
    customdata=[sensorCO, sensorNH3]   # This holds the sensor data
))

# Set the layout for the map
fig.update_layout(
    mapbox_style="carto-positron",  # You can choose other map styles (e.g., 'open-street-map')
    mapbox_center={"lat": 47.6097, "lon": -122.3331},  # Center the map on Seattle
    mapbox_zoom=7,  # Zoom level
    title="Sensor Locations with Data"
)

# Create a Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("WESS Data"),
    dcc.Graph(id='map', figure=fig),
    html.Div(id='sensor-data')
])


# Callback to update the sensor data when a point is clicked
@app.callback(
    Output('sensor-data', 'children'),
    [Input('map', 'clickData')]
)
def display_sensor_data(clickData):
    if clickData is None:
        return "Click on a sensor point to see its data."

    # Get the point clicked
    point = clickData['points'][0]
    label = point['text']
    data = point['customdata']

    #return f"Sensor: {label} | Temperature: {data}C"
    return (f"Sensor: {label} | CO: {df.loc[df['sensorName'] == label].CO.values[0]} | NH3: {df.loc[df['sensorName'] == label].NH3.values[0]} | NO2: {df.loc[df['sensorName'] == label].NO2.values[0]}")


# Run the app
if __name__ == '__main__':
    app.run(debug=False)
