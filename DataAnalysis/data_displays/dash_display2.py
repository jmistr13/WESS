# Python program that displays data using dash
import dash
import numpy as np
from df_customMethods import *
from dash import dcc, html
import plotly.express as px
from dash.dependencies import Input, Output, State
import pandas as pd


# Initial data load and processing
def load_and_process_data():
    df = pd.read_csv('data.csv',
                     usecols=['sensorName', 'lat', 'long', 'transmitDateTime', 'CO', 'NH3', 'NO2', 'TDS', 'turbidity'],
                     comment='#')
    df_recent = mostRecentValidLoc(df)
    df_recent = df_recent.fillna('')
    return df_recent


# Load initial data
initial_data = load_and_process_data()

# Define healthy ranges for pollutants
pollutant_ranges = {
    'CO': [4.2, 4.5],
    'NH3': [0, 1],
    'NO2': [0, 0.5],
    'TDS': [0, 1],
    'turbidity': [0, 1]
}

# Create a Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("WESS Data"),
    dcc.Store(id='stored-data', data=initial_data.to_json(date_format='iso', orient='split')),
    dcc.Dropdown(
        id='colorDropdown',
        options=[
            {'label': 'CO', 'value': 'CO'},
            {'label': 'NH3', 'value': 'NH3'},
            {'label': 'NO2', 'value': 'NO2'},
            {'label': 'TDS', 'value': 'TDS'},
            {'label': 'Turbidity', 'value': 'turbidity'},
        ],
        value='CO',  # Default value
        clearable=False
    ),
    html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
    dcc.Graph(id='map'),
    html.Div(id='sensor-data')
])


# Callback to reload CSV data when button is clicked
@app.callback(
    Output('stored-data', 'data'),
    Input('update-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_data(n_clicks):
    """Reload and process data when the update button is clicked."""
    updated_data = load_and_process_data()
    return updated_data.to_json(date_format='iso', orient='split')


# Callback to update the map based on stored data and dropdown
@app.callback(
    Output('map', 'figure'),
    Input('colorDropdown', 'value'),
    Input('stored-data', 'data')
)
def update_map(selected_pollutant, data):
    """Regenerate map with latest data and selected pollutant."""
    df_recent = pd.read_json(data, orient='split')

    fig = px.scatter_map(
        df_recent,
        lat='lat',
        lon='long',
        size=np.linspace(20, 20, len(df_recent)),
        color=selected_pollutant,
        range_color=pollutant_ranges.get(selected_pollutant, [0, 1]),
        color_continuous_scale=["rgb(0, 255, 0)", "rgb(120, 255, 0)", "rgb(255, 255, 0)", "rgb(255, 120, 0)",
                                "rgb(255, 0, 0)"],
        center=dict(lat=df_recent['lat'].mean(), lon=df_recent['long'].mean()),
        zoom=14,
        hover_name='sensorName',
        map_style='carto-positron',
        hover_data=dict(lat=False, long=False, transmitDateTime=True, CO=True, NH3=True, NO2=True, TDS=True,
                        turbidity=True)
    )

    fig.update_layout(
        title="Sensor Locations with Most Recent Readings",
    )
    return fig


# Callback to display sensor data when a point is clicked
@app.callback(
    Output('sensor-data', 'children'),
    Input('map', 'clickData'),
    Input('stored-data', 'data')
)
def display_sensor_data(clickData, data):
    """Show sensor readings when a map point is clicked."""
    if not clickData:
        return "Click on a sensor point to see its data."

    df_recent = pd.read_json(data, orient='split')
    point = clickData['points'][0]
    sensor_name = point['hovertext']

    # Safely extract values
    sensor_data = df_recent[df_recent['sensorName'] == sensor_name]
    if sensor_data.empty:
        return "Data not found for this sensor."

    values = {
        'CO': sensor_data['CO'].values[0],
        'NH3': sensor_data['NH3'].values[0],
        'NO2': sensor_data['NO2'].values[0],
        'TDS': sensor_data['TDS'].values[0],
        'turbidity': sensor_data['turbidity'].values[0]
    }

    return f"Sensor {sensor_name}: CO={values['CO']}, NH3={values['NH3']}, NO2={values['NO2']}, TDS={values['TDS']}, Turbidity={values['turbidity']}"


# Run the app
if __name__ == '__main__':
    app.run(debug=True)