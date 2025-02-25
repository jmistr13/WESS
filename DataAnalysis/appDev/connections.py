from dash import html
from customMethods import *

def layout():
    return html.Div([ #HTML that defines the connections page
            html.H2("Would you like to see this data on your mobile device?"),
            html.P([
                "Connect to ",
                html.Strong(get_wifi_name()),  # Makes the Wi-Fi name bold
                " and navigate to ",
                html.Strong(f"{get_local_ip()}:8050"),  # Makes the IP address bold
                " on your mobile device."
            ])
        ])