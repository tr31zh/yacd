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

confirmed_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
dead_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
recovered_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"


def get_data_and_meld(url: str, val_name: str) -> pd.DataFrame:
    """Prepare a dataframe using an URL and a name for the column
    
    Arguments:
        url {str} -- github raw link
        val_name {str} -- name of the column
    
    Returns:
        DataFrame -- Built dataframe
    """
    return (
        pd.read_csv(url, error_bad_lines=False)
        .rename(
            columns={
                "Province/State": "province_state",
                "Country/Region": "country_region",
                "Lat": "lat",
                "Long": "long",
            }
        )
        .melt(
            id_vars=["province_state", "country_region", "lat", "long"],
            var_name="date",
            value_name=val_name,
        )
    )


# build the three root dataframes
df_confirmed = get_data_and_meld(url=confirmed_url, val_name="confirmed")
df_dead = get_data_and_meld(url=dead_url, val_name="dead")
df_recovered = get_data_and_meld(url=recovered_url, val_name="recovered")

# Merge dataframes
df_merged = (
    df_confirmed.join(df_dead["dead"])
    .join(df_recovered["recovered"])
    .sort_values(["country_region", "date"])
    .reset_index()
    .drop(columns=["index"])
)
df_merged.date = pd.to_datetime(df_merged.date)

# Build world dataframe and add it to the mix
df_world = (
    df_merged.drop(columns=["province_state", "country_region", "lat", "long"])
    .set_index("date")
    .resample("d")
    .sum(min_count=180)
    .reset_index()
    .assign(country_region="World", lat=np.nan, long=np.nan)
)
df = pd.concat((df_merged, df_world)).sort_values(["country_region", "date"])

# Set recovered to int
df.recovered = df.recovered.fillna(-1)
df.recovered = pd.to_numeric(df.recovered, downcast="integer")
df.recovered = df.recovered.replace(-1, np.nan)

# Begin Dashboard
# external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
external_stylesheets = ["https://codepen.io/anon/pen/mardKv.css"]

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

title = html.H1(children="YACD",)
description = dcc.Markdown(
    children="""
        Yet another COVID-19 dashboard built by yet another data science enthusiast.  
        I made this so I can look at the data the way I like.  
        Please feel free to fork, modify and distribute.""",
)

header = dbc.Row([dbc.Col(title), dbc.Col(description)])

all_columns = df.columns.to_list()
num_columns = df.select_dtypes([np.int64, np.float64, np.datetime64]).columns.to_list()
cat_columns = df.select_dtypes([np.object, np.datetime64]).columns.to_list()
side_bar_label_width = 3
side_bar = dbc.Col(
    [
        dbc.Row(
            [
                dbc.Col(html.Label("Countries:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="selected_countries",
                        options=[{"label": i, "value": i} for i in df.country_region.unique()],
                        value="World",
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
                        options=[{"label": i, "value": i} for i in num_columns],
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
                        value="confirmed",
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
                        value="none",
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
                dbc.Col(html.Label("Facet:"), width=side_bar_label_width),
                dbc.Col(
                    dcc.Dropdown(
                        id="facet-column",
                        options=[{"label": i, "value": i} for i in ["none"] + cat_columns],
                        value="none",
                    )
                ),
            ]
        ),
    ]
)

epoch = dt.utcfromtimestamp(0).date()


def unix_time_days(dt):
    return (dt - epoch).total_seconds() // 86400


body = dbc.Row(
    [
        dbc.Col(side_bar, width=3),
        dbc.Col(
            [
                dbc.Row(dcc.Graph(id="output-graph")),
                dbc.Row(
                    [
                        dbc.Col(html.Button("Play", id="bt_play"), width="auto"),
                        dbc.Col(
                            dcc.Slider(
                                id="time-pos",
                                min=unix_time_days(df.date.dt.date.min()),
                                max=unix_time_days(df.date.dt.date.max()),
                                marks={unix_time_days(i): f"{str(i)}" for i in df.date.dt.date},
                                value=unix_time_days(df.date.dt.date.min()),
                            )
                        ),
                    ]
                ),
            ]
        ),
    ]
)

app.layout = html.Div(children=[header, body])


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
        Input("text-column", "value"),
        Input("time-pos", "value"),
        Input("filter-by-date", "value"),
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
    facet,
    text_column,
    time_pos,
    filter_by_date,
):
    lcl_df = df[
        df.country_region.isin(
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
    fig = px.scatter(
        data_frame=lcl_df,
        x=x_axis,
        log_x=log_x,
        range_x=rx,
        y=y_axis,
        log_y=log_y,
        range_y=ry,
        animation_frame="date" if filter_by_date else None,
        animation_group=color_column if color_column != "none" else None,
        color=color_column if color_column != "none" else None,
        size=dot_size if dot_size != "none" else None,
        size_max=60,
        facet_row=facet if facet != "none" else None,
        text=text_column if text_column != "none" else None,
        width=1400,
        height=800,
    )
    if filter_by_date:
        fig.update_layout(transition={"duration": 1000})
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
