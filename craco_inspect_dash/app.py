from flask import Flask
from dash import Dash, html, callback

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from common import header, footer

server = Flask(__name__)
app = Dash(
    __name__,
    server=server,
    url_base_pathname="/",
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ]
)

app.layout = html.Div(
    [
        header(),
        dash.page_container,
        footer(),
    ]
)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8024, debug=True)