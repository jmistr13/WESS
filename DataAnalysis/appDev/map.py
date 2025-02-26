# Page 1: Map and Time Series
# Default page

import dash
from dash import html, dcc, callback, Input, Output
#import plotly.graph_objects as go
import plotly.express as px

from df_customMethods import * #import all custom methods for data frames

filename = csv_path()
df = loadAndProcessData(filename)

last_modified_time = get_csv_modified_time(filename) # make sure csv stays up to date

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
                html.H2('Select Pollutant to View'), #text above selector
                dcc.Dropdown(options=[
                    {'label':'CO', 'value':'CO'},
                    {'label':'NH3', 'value':'NH3'},
                    {'label':'NO2', 'value':'NO2'},
                    {'label':'TDS', 'value':'TDS'},
                    {'label':'Turbidity', 'value':'turbidity'}],
                    value='CO',
                    id='data-select',
                    className='custom-dropdowns',
                )
            ], style={"flex": "1",'align-items':'center',"text-align":"center",'padding-left':'3%'}),
            html.Div([
                html.H2(id='graph-title',
                        style={'size':36,'align':'center'})
            ], style={"flex": "3",'align-items':'center',"text-align":"left",'padding-left':'15%'}),
        ], style={"display": "flex", "gap": "20px", 'align-items':'center'}),
        dcc.Graph(id='sensor-map'),

        #update map content periodically 
        dcc.Interval(
            id='interval-component',
            interval=5000, # in milliseconds
            n_intervals=0
        ),
    ])

#generates map based on changes for checked data
def update_map(selectedPollutant,n_intervals):
    global df, last_modified_time

    # Check if the CSV file has been modified
    current_modified_time = get_csv_modified_time(filename)
    if current_modified_time > last_modified_time:
        df = loadAndProcessData(filename)  # Reload the data
        last_modified_time = current_modified_time  # Update the last known modification time

    fig = px.scatter_map( # Using plotly express, not graph objects
        df,
        lat='lat',
        lon='long', # Keep in mind plotly refers to this as lon, but we call it long
        size=np.linspace(20, 20, len(df)), # just making an array of 20's with length of df, the size needs a value for every data point
        color=selectedPollutant, # whatever value is here is what will define the color of the points
        range_color=pollutant_ranges.get(selectedPollutant, [0,1]), #selectedPollutant
        #color_continuous_scale='Jet', #I quite like this one too
        color_continuous_scale=["rgb(0, 255, 0)", "rgb(120, 255, 0)", "rgb(255, 255, 0)", "rgb(255, 120, 0)", "rgb(255, 0, 0)"], # green to yellow to red
        center=dict(lat=df['lat'].mean(), lon=df['long'].mean()), # Places center of map at average lat and long
        zoom=14, #This zoom works well for campus size, this number has no real scale so its trial and error
        hover_name='sensorName',
        map_style='carto-positron',
        #mapbox_style='none',
        hover_data=dict(lat=False, long=False, transmitDateTime=True, CO=True, NH3=True, NO2=True, TDS=True, turbidity=True) #False removes from hover, true keeps it in
        #TODO: Figure out how to hide "size" in the hover data
    )
    
    fig.update_layout(
        title=f"Most Recent {selectedPollutant} Reading",
    )
    return fig

def update_title(selectedPollutant):
    return f'Most Recent {selectedPollutant} Readings'

def register_callbacks(wessApp):
    # Update the map when the selection changes or the CSV updates
    wessApp.callback(
        Output('sensor-map', 'figure'),
        Input('data-select', 'value'),
        Input('interval-component', 'n_intervals')  # Refreshes periodically
    )(update_map)

    # Update the H2 title when the pollutant selection changes
    wessApp.callback(
        Output('graph-title', 'children'),  # Fix: Use 'children' instead of 'value'
        Input('data-select', 'value')
    )(update_title)

