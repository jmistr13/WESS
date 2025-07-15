# Page 1: Map and Time Series
# Default page

import dash
from dash import html, dcc, callback, Input, Output
#import plotly.graph_objects as go
import plotly.express as px

from df_customMethods import * #import all custom methods for data frames

filename = csv_path()
df = loadAndProcessData(filename)

pollutant_names = ['CO','NH3','NO2','TDS','turbidity']
# Ranges for pollutants for cmap
pollutant_ranges = {
    # Values in PPM
    'CO': [0, 50],
    'NH3': [0, 50],
    'NO2': [0, 3],
    'TDS': [0, 500],
    'turbidity': [0, 10] 
}

def layout():
    return html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(options=[ # Dropdown to select what pollutant is displayed
                    {'label':'CO', 'value':'CO'},
                    {'label':'NH3', 'value':'NH3'},
                    {'label':'NO2', 'value':'NO2'},
                    {'label':'TDS', 'value':'TDS'},
                    {'label':'Turbidity', 'value':'turbidity'}],
                    value="CO",
                    id='data-select',
                    className='custom-dropdowns',
                    style={'background-color':'#f2f4ff','color':'#272838'}
                )
            ], style={"flex": "1",'align-items':'center',"text-align":"center",'padding-left':'3%'}),
            html.Div([ # Set Graph Title
                html.H2(id='graph-title',
                        style={'size':36,'align':'center'})
            ], style={"flex": "3",'align-items':'center',"text-align":"left",'padding-left':'15%'}),
        ], style={"display": "flex", "gap": "20px", 'align-items':'center'}),
        dcc.Graph(id='sensor-map'), # Graph

        #update map content periodically 
        dcc.Interval(
            id='interval-component',
            interval=5000, # in milliseconds
            n_intervals=0
        ),

        # Store map state
        dcc.Store(id='map-store', data={'zoom': 14, 'center': {'lat': df['lat'].mean(), 'lon': df['long'].mean()}}),
    ])

#generates map based on changes for checked data
def update_map(selectedPollutant,n_intervals,stored_data):
    global df

    display_index =pollutant_names.index(selectedPollutant) # Gets index of pollutant for cmap range

    # Use stored zoom and center if available
    zoom = stored_data.get('zoom', 14)
    center = stored_data.get('center', {'lat': df['lat'].mean(), 'lon': df['long'].mean()})

    fig = px.scatter_map( # Map figure 
        df,
        lat='lat',
        lon='long', # Keep in mind plotly refers to this as lon, but we call it long
        size=np.linspace(20, 20, len(df)), # just making an array of 20's with length of df, the size needs a value for every data point
        color=selectedPollutant, # whatever value is here is what will define the color of the points
        range_color=pollutant_ranges.get(selectedPollutant, [0,1]), #selectedPollutant
        #color_continuous_scale='Jet', #I quite like this one too
        color_continuous_scale=["rgb(0, 255, 0)", "rgb(120, 255, 0)", "rgb(255, 255, 0)", "rgb(255, 120, 0)", "rgb(255, 0, 0)"], # green to yellow to red
        center=center, # Places center of map at average lat and long
        zoom=zoom, #Arbitrary, 14 good for UW campus, 1.5 For prototype+dummy
        hover_name='sensorName',
        map_style='carto-positron',
        #mapbox_style='none',
        hover_data={p: (p == selectedPollutant) for p in pollutant_names},
        custom_data=df[['transmitDateTime','CO','NH3','NO2','TDS','turbidity']]
    )
    
    fig.update_layout(
        hoverlabel=dict(
        bgcolor="#272838"),
        height=420,
    )

    fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>"
                  "<br>Timestamp: %{customdata[0]}<br>"
                 f"{selectedPollutant}: %{{customdata[{display_index + 1}]:.2f}} ppm<br>"
                  "<extra></extra>"
    )

    return fig

def update_title(selectedPollutant):
    return f'Most Recent {selectedPollutant} Readings (PPM)'

def register_callbacks(app):
    # Update the map when the selection changes or the CSV updates
    app.callback(
        Output('sensor-map', 'figure'), # Map return
        Input('data-select', 'value'), # Dropdown selsction
        Input('interval-component', 'n_intervals'),  # Refreshes periodically
        Input('map-store', 'data') #stored map data
    )(update_map)

    # Store the map's zoom and center state when the user interacts
    app.callback(
        Output('map-store', 'data'),
        Input('sensor-map', 'relayoutData'),
        prevent_initial_call=True  # Avoid triggering on startup
    )(lambda relayoutData: {
        'zoom': relayoutData.get('mapbox.zoom', 14),
        'center': relayoutData.get('mapbox.center', {'lat': df['lat'].mean(), 'lon': df['long'].mean()})
    })

    # Update the H2 title when the pollutant selection changes
    app.callback(
        Output('graph-title', 'children'),  # Fix: Use 'children' instead of 'value'
        Input('data-select', 'value')
    )(update_title)
