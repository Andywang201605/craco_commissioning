from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import plotly.express as px

import numpy as np
import json

dash.register_page(__name__, title="UVFITS INSPECTION")

with open("assets/30ants_465bls_idx.json") as fp:
    bidx_info = json.load(fp)

# workout baseline index and baseline name mapping
blnames = np.array([f"{_a1},{_a2}" for _bidx, (_a1, _a2) in bidx_info["bidx_ants"]])

### Layout functions...
### input field for npy files folder
def folder_input():
    return dbc.Container([dbc.Col(
        [
            dbc.Row(
                html.H5("Please input the path of the folder that contains npy files..."),
                style={"margin-top": "15px"},
                ),
            dbc.Row(
                dcc.Input(id="folder_input", value="/import/ada1/zwan4817/craco/workdir/npy"),
                style={"margin-left": "10px", "margin-right": "10px"}
                ),
            dbc.Row(
                [
                    dbc.Col(html.H5("Please indicate the beam number")),
                    dbc.Col(dcc.Input(id="beam_input", type="number", value=0, min=0, max=35, step=1))
                ],
                style={"margin-top": "15px"}
            )
        ]
    )])


def load_data_button():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Button("Load Data", id="btn_load_uvdata", n_clicks=0)
                        ),
                    dbc.Col(dbc.Row([
                        dbc.Col("Loading Status - "),
                        dbc.Col(dcc.Loading(id="loading_status_para", children="N/A", fullscreen=False))
                    ]))
                ],
                style={"margin-top": "20px"}
            )
        ]
    )


def data_range_input():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col("Start Frequency"),
                    dbc.Col(dcc.Input(id="freqstart_input", type="number", value=743.4)),
                    dbc.Col("End Frequency"),
                    dbc.Col(dcc.Input(id="freqend_input", type="number", value=887.4)),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col("Start Integration"),
                    dbc.Col(dcc.Input(id="tstart_input", type="number", value=0, min=0)),
                    dbc.Col("End Integration"),
                    dbc.Col(dcc.Input(id="tend_input", type="number", value=1200, min=0)),
                ]
            )
        ]
    )


def plot_button_layout():
    return dbc.Container(
        dbc.Row([
            dbc.Col(dbc.Row(
                [
                    dcc.Dropdown(
                        ["Cross Correlation", "Auto Correlation", "All Correlation"],
                        value = "Cross Correlation", id="corr_data_type_select"
                    )
                ]
            )),
            dbc.Col(dbc.Row(
                [
                    dbc.Col(html.Button("Plot", id="btn_plot", n_clicks=0)),
                    dbc.Col(dcc.Loading(id="waterfall_plot_status"))
                ]
            )),
            dbc.Col(dbc.Row([
                dbc.Col(html.Button("Update", id="btn_update_waterfall", n_clicks=0)),
                dbc.Col(dcc.Loading(id="waterfall_update_status"))
            ]))
            # dbc.Col(html.Button("Update", id="btn_update_range", n_clicks=0)),
            # dbc.Col(html.Button("Reset", id="btn_reset_range", n_clicks=0)),
        ])
    )

def diagnose_plot_layout():
    return dbc.Container(
        [
            dbc.Row(id="water_fall_plot_contain"),
            dbc.Row([
                dbc.Col(id="spectrum_plot_contain"),
                dbc.Col(id="lightcurve_plot_contain")
            ])
        ]
    )


### part for antenna diagnose

def antenna_plot_layout():
    return dbc.Container([
        dbc.Row(
                [
                    dbc.Col(html.Button("Plot Antenna", id="btn_plot_ants", n_clicks=0)),
                    dbc.Col(dcc.Loading(id="ant_plot_status"))
                ]
        ),
        dbc.Row(
            [
                dbc.Col(id="antenna_auto_plot_freq_contain"),
                dbc.Col(id="antenna_cross_plot_freq_contain"),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(id="antenna_auto_plot_t_contain"),
                dbc.Col(id="antenna_cross_plot_t_contain"),
            ]
        )
    ])

### part for baseline diagnose

def all_baseline_plot_layout():
    button_layout = dbc.Row([
        dbc.Col(html.Button("Plot Baselines", id="btn_bl_plot", n_clicks=0)),
        dbc.Col(dcc.Loading(id="all_bl_plot_status"))
    ])

    figure_layout = dbc.Row([
        dbc.Col(id="all_baselines_freq_plot_contain"),
        dbc.Col(id="all_baselines_time_plot_contain")
    ])

    return dbc.Container([
        button_layout, figure_layout, 
    ])


def random_baseline_plot_layout():

    return dbc.Container(
        [
            dbc.Row([
                dbc.Col(html.Button("Plot Random Baselines", id="btn_rand_bl_plot", n_clicks=0)),
                dbc.Col(dcc.Loading(id="rand_bl_plot_status"))
            ]),
            dbc.Row(id="rand_bl_full_contain"),
        ]
    )

def selected_baseline_plot_layout():

    # input part
    return 


##### functions for callback...
@callback(
    Output("btn_load_uvdata", "n_clicks"),
    Output("loading_status_para", "children"),
    Output("tend_input", "value"),
    Output("tstart_input", "max"),
    Output("tend_input", "max"),
    Input("btn_load_uvdata", "n_clicks"),
    State("folder_input", "value"),
    State("beam_input", "value"),
)
def load_uvfits_data(n_click, folder, beam):
    if n_click == 0: raise PreventUpdate

    beam = "{:0>2}".format(beam)
    npy_fname = "{}/output_beam{}.uvfits.npy".format(folder, beam)

    print("Start to Loading data from {}".format(npy_fname))

    uvdata = np.load(npy_fname)[:, :, 0, :]

    ### some data contains zeros at the end - strip them
    timeseries = np.abs(uvdata).mean(axis=0).mean(axis=0)
    nsamp = len(timeseries)

    for i in range(nsamp):
        if timeseries[-i-1] != 0: 
            cut = i; break
    uvdata = uvdata[:, :, :nsamp-cut].copy()

    datashape = uvdata.shape

    global nbl, nfreq, nt 
    nbl, nfreq, nt = datashape

    global uvdata_amp, uvdata_angle
    uvdata_amp = np.abs(uvdata)
    uvdata_angle = np.angle(uvdata)

    global beam_idx
    beam_idx = beam

    return 0, "BEAM{} SUCCESSFUL!".format(beam), nt, nt, nt


@callback(
    Output("btn_plot", "n_clicks"),
    Output("water_fall_plot_contain", "children"),
    Output("spectrum_plot_contain", "children"),
    Output("lightcurve_plot_contain", "children"), 
    Output("waterfall_plot_status", "children"),
    State("freqstart_input", "value"),
    State("freqend_input", "value"),
    State("tstart_input", "value"),
    State("tend_input", "value"),
    State("corr_data_type_select", "value"),
    Input("btn_plot", "n_clicks"),
)
def plot_diagnose_plot(freqstart, freqend, tstart, tend, corr_type, n_clicks):
    if n_clicks == 0: raise PreventUpdate

    # only select certain correlation 
    if corr_type == "Cross Correlation":
        uvdata_bl_ave = uvdata_amp[bidx_info["cross_bidx"], ...].mean(axis=0)
    elif corr_type == "Auto Correlation":
        uvdata_bl_ave = uvdata_amp[bidx_info["auto_bidx"], ...].mean(axis=0)
    else:
        uvdata_bl_ave = uvdata_amp.mean(axis=0)

    print("averaging on baselines...")
    ts = np.arange(nt)
    fs = np.linspace(743.4, 887.4, 864)

    print("start plotting...")

    waterfall = px.imshow(
        uvdata_bl_ave, origin="lower",
        x=ts, y=fs,
        aspect="auto",
    )

    waterfall.update_layout(
        title_text="WaterFall Plot for BEAM{} - {}".format(beam_idx, corr_type),
        title_x = 0.5
    )

    waterfall.update_xaxes(
        title_text='Time (Integration)',
        range=[tstart-0.5, tend-0.5],
    )
    waterfall.update_yaxes(
        title_text='Frequency (MHz)',
        range=[freqstart, freqend], autorange=False,
    )

    print("waterfall plotted!")

    spectrum = px.line(
        x = fs, y = np.mean(uvdata_bl_ave, axis=1),
    )

    spectrum.update_xaxes(
        title_text='Frequency (MHz)', range=[freqstart, freqend]
    )
    spectrum.update_yaxes(title_text='Amplitude (Unit)')
    spectrum.update_layout(
        title_text="Spectrum for BEAM{} - {}".format(beam_idx, corr_type),
        title_x = 0.5
    )

    lightcurve = px.line(
        x=ts, y=np.mean(uvdata_bl_ave, axis=0)
    )
    lightcurve.update_xaxes(
        title_text='Time (Integration)', range=[tstart, tend]
    )
    lightcurve.update_yaxes(title_text='Amplitude (Unit)')
    lightcurve.update_layout(
        title_text="Lightcurve for BEAM{} - {}".format(beam_idx, corr_type),
        title_x = 0.5
    )


    return (
        0, dcc.Graph(id="water_fall_plot", figure=waterfall),
        dcc.Graph(id="spectrum_plot", figure=spectrum, ),
        dcc.Graph(id="lightcurve_plot", figure=lightcurve, ),
        None,
    )


@callback(
    Output("btn_update_waterfall", "n_clicks"),
    Output("spectrum_plot", "figure"),
    Output("lightcurve_plot", "figure"),
    State("water_fall_plot", "relayoutData"),
    State("spectrum_plot", "figure"),
    State("lightcurve_plot", "figure"),
    Input("btn_update_waterfall", "n_clicks"),
)
def update_spectrum_lightcurve_layout(
    waterfall_layout, spectrum, lightcurve, n_clicks
):
    if n_clicks == 0: raise PreventUpdate

    try:
        tstart = waterfall_layout["xaxis.range[0]"]
        tend = waterfall_layout["xaxis.range[1]"]
        freqstart = waterfall_layout["yaxis.range[0]"]
        freqend = waterfall_layout["yaxis.range[1]"]
    except: raise PreventUpdate

    spectrum["layout"]["xaxis"] = {"range": (freqstart, freqend)}
    lightcurve["layout"]["xaxis"] = {"range": (tstart, tend)}

    return 0, spectrum, lightcurve


@callback(
    Output("btn_plot_ants", "n_clicks"),
    Output("antenna_auto_plot_freq_contain", "children"),
    Output("antenna_cross_plot_freq_contain", "children"),
    Output("antenna_auto_plot_t_contain", "children"),
    Output("antenna_cross_plot_t_contain", "children"),
    Output("ant_plot_status", "value"),
    Input("btn_plot_ants", "n_clicks"),
)
def plot_antenna_diagnose_plot(n_clicks):
    if n_clicks == 0: raise PreventUpdate

    fs = np.linspace(743.4, 887.4, 864)

    auto_bidx = bidx_info["auto_bidx"]
    ant_bidx = bidx_info["ant_bidx"]

    print("Splitting data ...")
    auto_data = uvdata_amp[auto_bidx, ...]

    cross_data = []
    for i in range(1, 31): # 30 antennas:
        ant_single_bidx = np.array(ant_bidx[str(i)])
        ant_cross_idx = ant_single_bidx[~np.isin(ant_single_bidx, auto_bidx)]
        cross_data.append(uvdata_amp[ant_cross_idx, ...])

    cross_data = np.array(cross_data).mean(axis=1)

    ### plot auto-correlation
    auto_freq_ant = px.imshow(
        auto_data.mean(axis=2), aspect="auto",
        x=fs, y=np.arange(1, 31)
    )

    auto_freq_ant.update_layout(
        title_text = "Auto Correlation", title_x = 0.5
    )
    auto_freq_ant.update_xaxes(title_text="Frequency (MHz)")
    auto_freq_ant.update_yaxes(
        title_text="Antenna", range=(0.5, 30.5), autorange=False,
    )

    auto_time_ant = px.imshow(
        auto_data.mean(axis=1), aspect="auto",
        x=np.arange(nt), y=np.arange(1, 31)
    )

    auto_time_ant.update_xaxes(title_text="Time (Integration)", range=(-0.5, nt-1.5))
    auto_time_ant.update_yaxes(
        title_text="Antenna", range=(0.5, 30.5), autorange=False,
    )

    ### plot cross-correlation
    cross_freq_ant = px.imshow(
        cross_data.mean(axis=2), aspect="auto",
        x=fs, y=np.arange(1, 31)
    )

    cross_freq_ant.update_layout(
        title_text = "Cross Correlation", title_x = 0.5
    )
    cross_freq_ant.update_xaxes(title_text="Frequency (MHz)")
    cross_freq_ant.update_yaxes(
        title_text="Antenna", range=(0.5, 30.5), autorange=False,
    )

    cross_time_ant = px.imshow(
        cross_data.mean(axis=1), aspect="auto",
        x=np.arange(nt), y=np.arange(1, 31)
    )

    cross_time_ant.update_xaxes(title_text="Time (Integration)", range=(-0.5, nt-1.5))
    cross_time_ant.update_yaxes(
        title_text="Antenna", range=(0.5, 30.5), autorange=False,
    )


    # raise PreventUpdate

    return (
        0, dcc.Graph(id="antenna_auto_plot_freq", figure=auto_freq_ant),
        dcc.Graph(id="antenna_cross_plot_freq", figure=cross_freq_ant),
        dcc.Graph(id="antenna_auto_plot_time", figure=auto_time_ant),
        dcc.Graph(id="antenna_cross_plot_time", figure=cross_time_ant),
        None,
    )



@callback(
    Output("btn_bl_plot", "n_clicks"),
    Output("all_baselines_freq_plot_contain", "children"),
    Output("all_baselines_time_plot_contain", "children"),
    Output("all_bl_plot_status", "value"),
    Input("btn_bl_plot", "n_clicks"),
)
def plot_all_baselines(n_clicks):
    if n_clicks == 0: raise PreventUpdate

    fs = np.linspace(743.4, 887.4, 864)

    ### only cross-correlation (as auto-correlation can be seen via antenna tabs...)
    cross_data = uvdata_amp[bidx_info["cross_bidx"], ...]

    bl_freq = px.imshow(
        cross_data.mean(axis=2), aspect="auto",
        x=fs, y=blnames[bidx_info["cross_bidx"]],
    )

    bl_freq.update_xaxes(
        title_text = "Frequency (MHz)",
    )
    bl_freq.update_yaxes(title_text = "Baseline")

    bl_time = px.imshow(
        cross_data.mean(axis=1), aspect="auto",
        x=np.arange(1, nt+1), y=blnames[bidx_info["cross_bidx"]],
    )

    bl_time.update_xaxes(
        title_text = "Time (Integration)", range=(0.5, nt-0.5)
    )
    bl_time.update_yaxes(title_text = "Baseline")

    return (
        0, dcc.Graph(figure=bl_freq, id="all_bls_freq_plot"),
        dcc.Graph(figure=bl_time, id="all_bls_time_plot"),
        None
    )


@callback(
    Output("btn_rand_bl_plot", "n_clicks"),
    Output("rand_bl_full_contain", "children"),
    Output("rand_bl_plot_status", "value"),
    Input("btn_rand_bl_plot", "n_clicks"),
)
def plot_random_baselines(n_clicks):
    print("`plot_random_baselines` callbacked is fired...")

    if n_clicks == 0: raise PreventUpdate

    fs = np.linspace(743.4, 887.4, 864)

    rand_bl_nx, rand_bl_ny = 2, 4

    selected_bl_idx = np.random.randint(0, 465, rand_bl_nx * rand_bl_ny)
    selected_bl_names = blnames[selected_bl_idx]

    figure_layout_content = []
    for i in range(rand_bl_ny):
        row_content = []
        for j in range(rand_bl_nx):
            fig_idx = i * rand_bl_nx + j

            bl_waterfall = uvdata_amp[selected_bl_idx[fig_idx]]
            bl_name = selected_bl_names[fig_idx]

            bl_waterfall = px.imshow(
                bl_waterfall, aspect="auto", 
                x=np.arange(nt), y=fs
            )

            bl_waterfall.update_layout(
                title_text="Baseline - {}".format(bl_name),
                title_x = 0.5
            )
            bl_waterfall.update_xaxes(
                title_text="Time (Integration)", range=(-0.5, nt-1.5)
            )
            bl_waterfall.update_yaxes(title_text="Frequency (MHz)")

            row_content.append(
                dbc.Col(
                    children=dcc.Graph(
                        id=f"rand_bl_plot_idx{fig_idx}", figure=bl_waterfall
                    ),
                    id="rand_bl_waterfall_contain_idx{}".format(fig_idx)
                )
            )
        figure_layout_content.append(dbc.Row(row_content))

    return (
        0, figure_layout_content, None
    )

layout = [
    folder_input(),
    load_data_button(),
    dbc.Container(html.Hr(style={"margin-bottom": "15px"})),
    data_range_input(),
    dbc.Container(html.Hr(style={"margin-bottom": "15px"})),
    plot_button_layout(),
    diagnose_plot_layout(),
    dbc.Container(html.Hr(style={"margin-bottom": "15px"})),
    antenna_plot_layout(),
    dbc.Container(html.Hr(style={"margin-bottom": "15px"})),
    all_baseline_plot_layout(),
    random_baseline_plot_layout(),
]