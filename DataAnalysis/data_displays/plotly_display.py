# display data through python using plotly

import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Define coordinates and sensor data
coordinates = [
    (47.6097, -122.3331, "Seattle", 23.5),  # Seattle, sensor reading = 23.5
    (48.7150, -122.4905, "Bellingham", 19.8),  # Bellingham, sensor reading = 19.8
    (46.8527, -121.7603, "Mount Rainier", 15.0)  # Mount Rainier, sensor reading = 15.0
]

# Extract latitudes, longitudes, labels, and data for plotting
latitudes = [lat for lat, lon, label, data in coordinates]
longitudes = [lon for lat, lon, label, data in coordinates]
labels = [label for lat, lon, label, data in coordinates]
sensor_data = [data for lat, lon, label, data in coordinates]

# Create the plot
fig = go.Figure(go.Scattermapbox(
    lat=latitudes,
    lon=longitudes,
    mode='markers',
    marker=dict(
        size=10,
        color='blue'
    ),
    text=labels,
    hovertemplate=(
        'Sensor: %{text}<br>' +
        'Data: %{customdata}<br>' +
        'Location: %{lat}, %{lon}'
    ),
    customdata=sensor_data  # This holds the sensor data
))

# Set the layout for the map
fig.update_layout(
    mapbox_style="carto-positron",  # You can choose other map styles (e.g., 'open-street-map')
    mapbox_center={"lat": 47.6097, "lon": -122.3331},  # Center the map on Seattle
    mapbox_zoom=7,  # Zoom level
    title="Sensor Locations with Data"
)

# Show the map
plt.savefig('washington_state_map.png', dpi=300)
fig.show()
