#main file for WESS app
import dash
from dash import Dash, html, dcc, callback, Input, Output
import plotly.express as px

# Import custom py files
from df_customMethods import *
import map, trendlines, connections

# function to send csv string to other programs.
# Replace string with desired csv path
def csv_path():
    return 'DataAnalysis/appDev/data2.csv'

wessApp = Dash(__name__, use_pages=False, suppress_callback_exceptions=True)
wessApp.layout = html.Div([
    html.H1('Wireless Environmental Sensor System'),
    dcc.Tabs(
        id="tabs",
        value="map",  # Default selected tab
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(label="Map", value="map",
                    className='custom-tab', selected_className='custom-tab--selected'),
            dcc.Tab(label="Trendline", value="trendline",
                    className='custom-tab', selected_className='custom-tab--selected'),
            dcc.Tab(label="Connections", value="connections",
                    className='custom-tab', selected_className='custom-tab--selected')
        ],
    ),
    html.Div(id="tab-content"),
])

@wessApp.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)

def render_page(tab_value):
    if(tab_value=='map'):
        return map.layout()
    elif(tab_value=='trendline'):
       return trendlines.layout()
    elif(tab_value=='connections'):
        return connections.layout()

map.register_callbacks(wessApp)
trendlines.register_callbacks(wessApp)

if __name__ == '__main__':
    wessApp.run(debug=True)
