# Page 1: Map and Time Series
# Default page

import dash
from dash import html, dcc, callback, Input, Output

layout = html.Div([
    html.H1('WESS Map Data with Time Series'), # Page Title

    #checklist for data to display
    dcc.Checklist([
        {
            "label": html.Div(['CO'], style={'color': 'firebrick', 'font-size': 14}),
            "value": "CO",
        },
        {
            "label": html.Div(['NH3'], style={'color': 'chocolate', 'font-size': 14}),
            "value": "NH3",
        },
        {
            "label": html.Div(['NO2'], style={'color': 'gold', 'font-size': 14}),
            "value": "NO2",
        },
        {
            "label": html.Div(['TDS'], style={'color': 'limegreen', 'font-size': 14}),
            "value": "TDS",
        },
        {
            "label": html.Div(['Turbidity'], style={'color': 'darkcyan', 'font-size': 14}),
            "value": "Turbidity",
        },
    ], value=['CO','NH3','NO2','TDS','Turbidity'],
    labelStyle={"display": "flex", "align-items": "center"},
    inline=True,
    id='data-select')

    html.Div(id='checkbox-output')

    # Map of data selected
    fig = go.Figure(go.Scattermap(
    lat=latitudes,
    lon=longitudes,
    mode='markers+text',
    marker=dict(
        size=14,
        color='seagreen'
    ),
    text=labels,
    hovertemplate=(
        'Sensor: %{text}<br>' +
        'Data: %{customdata}<br>' +
        'Location: %{lat}, %{lon}'
    ),
    customdata=sensor_data  # This holds the sensor data
))
])

def hover_display():
    initial_string=''

