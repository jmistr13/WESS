# Page 2: Trendlines

import dash
from dash import html, dcc, callback, Input, Output
import plotly.express as px

dash.register_page(__name__)

# Ranges for pollutants for cmap
pollutant_ranges = {
    # Values in PPM
    'CO': [0, 50],
    'NH3': [0, 50],
    'NO2': [0, 3],
    'TDS': [0, 500],
    'turbidity': [0, 10] 
}

layout = html.Div([ #HTML that defines the Graph page
    #checklist for data to display
    html.Label('Select a Sensor'),
    dcc.RadioItems(['The Quad', 'Sylvan Grove', 'Union Bay', 'Arboretum'], 'The Quad'),

    html.Br(), #break

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
        }], 
        value=['CO','NH3','NO2','TDS','Turbidity'],
        labelStyle={"display": "flex", "align-items": "center"},
        inline=True,
        id='data-select'
    ), #end checklist

    dcc.Graph(id='trendline-graph'),
    html.Button('Update Map Data from CSV', id='update-button', n_clicks=0),
])

@callback(
    Output('trendline-graph', 'figure'),
    Input('data-select', 'value')
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