import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

import plotly.express as px

from dw_cssegis_data import get_wrangled_cssegis_df

df = get_wrangled_cssegis_df()


external_stylesheets = dbc.themes.BOOTSTRAP

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, external_stylesheets=[external_stylesheets])

layout_style = {
    "border": "1px solid #B3B6B7",
    # "padding": "4px",
    "background-color": "white",
}
text_layout = layout_style.copy()
text_layout["text-align"] = "center"


header = dbc.Row(
    html.H1(children="YACD - Yet Another COVID-19 dashboard", style=text_layout,),
    justify="center",
    style={"height": "8vh"},
)
footer = dbc.Row(dcc.Markdown(f"CSV last updated: {df.date.max().date()}"), justify="end")

all_columns = df.columns.to_list()
num_columns = df.select_dtypes([np.int64, np.float64, np.datetime64]).columns.to_list()
cat_columns = df.select_dtypes([np.object, np.datetime64]).columns.to_list()
side_bar_label_width = 4
side_bar = dbc.Col(
    [
        dbc.Row(html.Label("")),
        dbc.Row(
            [
                dbc.Col(html.Label("Countries:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="selected_countries",
                        options=[{"label": i, "value": i} for i in df.country.unique()],
                        value=["France", "Spain", "Italy", "Germany", "US", "China",],
                        multi=True,
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("X axis:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="xaxis-column",
                        options=[{"label": i, "value": i} for i in num_columns + ["country"]],
                        value="date",
                    )
                ),
                dbc.Col(
                    dcc.Checklist(
                        id="x-axis-type", options=[{"label": "Log", "value": "log-x"},],
                    ),
                    width=2,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Y axis:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="yaxis-column",
                        options=[{"label": i, "value": i} for i in num_columns],
                        value="confirmed_total",
                    )
                ),
                dbc.Col(
                    dcc.Checklist(
                        id="y-axis-type", options=[{"label": "Log", "value": "log-y"},],
                    ),
                    width=2,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dcc.Checklist(
                    id="filter-by-date",
                    options=[
                        {
                            "label": "Show one date only (use slider to change)",
                            "value": "filter-date",
                        },
                    ],
                ),
            )
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Color:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="color-column",
                        options=[{"label": i, "value": i} for i in ["none"] + cat_columns],
                        value="country",
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Dot size:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="size-column",
                        options=[{"label": i, "value": i} for i in ["none"] + num_columns],
                        value="none",
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Dot text:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="text-column",
                        options=[{"label": i, "value": i} for i in ["none"] + all_columns],
                        value="none",
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Facet column:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="facet-column",
                        options=[{"label": i, "value": i} for i in ["none"] + cat_columns],
                        value="none",
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Facet col wrap:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Input(
                        id="facet-column-wrap",
                        value=4,
                        type="number",
                        debounce=True,
                        min=1,
                        step=1,
                    ),
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Facet row:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="facet-row",
                        options=[{"label": i, "value": i} for i in ["none"] + cat_columns],
                        value="none",
                    )
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label("Graph type:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="plot-type",
                        options=[{"label": i, "value": i} for i in ["scatter", "bar", "line"]],
                        value="scatter",
                    )
                ),
            ]
        ),
        dbc.Row(html.Label("")),
    ],
    style=layout_style,
)

epoch = dt.utcfromtimestamp(0).date()


def unix_time_days(dt):
    return (dt - epoch).total_seconds() // 86400


body = dbc.Row(
    [
        dbc.Col([dbc.Row(side_bar),]),
        dbc.Col(
            [
                dbc.Row(
                    dcc.Graph(id="output-graph", style={"width": "98%"}),
                    style={"width": "78vw", "height": "84vh"},
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Slider(
                            id="time-pos",
                            min=unix_time_days(df.date.dt.date.min()),
                            max=unix_time_days(df.date.dt.date.max()),
                            marks={unix_time_days(i): f"{str(i)}" for i in df.date.dt.date},
                            value=unix_time_days(df.date.dt.date.min()),
                        )
                    ),
                ),
            ],
            style=layout_style,
        ),
    ],
)

app.layout = html.Div(
    children=dbc.Col([header, body, footer], width=12), style={"background-color": "#F9F9F9"},
)
server = app.server


@app.callback(
    Output("output-graph", "figure"),
    [
        Input("selected_countries", "value"),
        Input("xaxis-column", "value"),
        Input("x-axis-type", "value"),
        Input("yaxis-column", "value"),
        Input("y-axis-type", "value"),
        Input("color-column", "value"),
        Input("size-column", "value"),
        Input("facet-column", "value"),
        Input("facet-row", "value"),
        Input("facet-column-wrap", "value"),
        Input("text-column", "value"),
        Input("time-pos", "value"),
        Input("filter-by-date", "value"),
        Input("plot-type", "value"),
    ],
)
def update_figure(
    selected_countries,
    x_axis,
    log_x,
    y_axis,
    log_y,
    color_column,
    dot_size,
    facet_column,
    facet_row,
    facet_col_wrap,
    text_column,
    time_pos,
    filter_by_date,
    plot_type,
):
    lcl_df = df[
        df.country.isin(
            selected_countries if isinstance(selected_countries, list) else [selected_countries]
        )
    ]
    if filter_by_date:
        target_date = dt.strftime(
            dt.utcfromtimestamp(0).date()
            + timedelta(days=time_pos if time_pos is not None else 0),
            "%Y-%m-%d",
        )
        rx = [lcl_df[x_axis].min(), lcl_df[x_axis].max()]
        ry = [lcl_df[y_axis].min(), lcl_df[y_axis].max()]
        lcl_df = lcl_df[lcl_df.date == target_date]
    else:
        rx = None
        ry = None
    common_params = dict(
        data_frame=lcl_df,
        x=x_axis,
        range_x=rx,
        y=y_axis,
        range_y=ry,
        color=color_column if color_column != "none" else None,
        facet_row=facet_row if facet_row != "none" else None,
        facet_col=facet_column if facet_column != "none" else None,
        facet_col_wrap=facet_col_wrap,
    )
    lg_common = common_params.copy()
    lg_common["log_x"] = log_x
    lg_common["log_y"] = log_y
    if plot_type == "scatter":
        fig = px.scatter(
            **lg_common,
            size=dot_size if dot_size != "none" else None,
            size_max=60,
            text=text_column if text_column != "none" else None,
        )
        if filter_by_date:
            fig.update_layout(transition={"duration": 500})
    elif plot_type == "bar":
        fig = px.bar(**common_params)
    elif plot_type == "line":
        fig = px.line(**lg_common)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
