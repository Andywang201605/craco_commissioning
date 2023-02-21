import dash
import dash_bootstrap_components as dbc
from dash import html

def header():
    return dbc.NavbarSimple(
        brand="Craco Commissioning Data Inspection",
        brand_href="#",
        color="primary",
        dark=True,
    )


def footer():
    return dbc.Container(
        [
            dbc.Row(
                html.P("ASKAP-CRACO @ 2023")
            )
        ]
    )


class MeasurementSetLoader:

    def __init__(self, measurementsetpath):
        ...
        

