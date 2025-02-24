import dash
from dash import Dash, html, dcc

wessApp = Dash(__name__, use_pages=True)

wessApp.layout = html.Div([
    html.H1('Wireless Environmental Sensor System'),
    html.Div([
        html.Div(
            dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
        ) for page in dash.page_registry.values()
    ]),
    dash.page_container
])

if __name__ == '__main__':
    wessApp.run(debug=True)
