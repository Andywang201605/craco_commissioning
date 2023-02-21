from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", title="CRACO Commissioning")

layout = dbc.Container(
    [
        html.P("This is an interactive tool for inspecting data")
    ]
)