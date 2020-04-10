import pandas as pd
import numpy as np
import os

root_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
confirmed_url_base_name = "time_series_covid19_confirmed_global.csv"
dead_url_base_name = "time_series_covid19_deaths_global.csv"
recovered_url_base_name = "time_series_covid19_recovered_global.csv"


def get_data_and_meld(base_url: str, val_name: str, allow_cache: bool = False) -> pd.DataFrame:
    """Prepare a dataframe using an URL and a name for the column
    
    Arguments:
        base_url {str} -- file name
        val_name {str} -- name of the column
    
    Returns:
        DataFrame -- Built dataframe
    """
    if allow_cache and os.path.isfile(os.path.join(".", "cached_data", base_url)):
        return pd.read_csv(os.path.join(".", "cached_data", base_url))
    else:
        tmp_df = (
            pd.read_csv(root_url + base_url, error_bad_lines=False)
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
        if allow_cache:
            tmp_df.to_csv(os.path.join(".", "cached_data", base_url))
        return tmp_df


def get_wrangled_cssegis_df(allow_cache: bool = False):
    # build the three root dataframes
    df_confirmed = get_data_and_meld(
        base_url=confirmed_url_base_name, val_name="confirmed", allow_cache=allow_cache
    )
    df_dead = get_data_and_meld(
        base_url=dead_url_base_name, val_name="dead", allow_cache=allow_cache
    )
    df_recovered = get_data_and_meld(
        base_url=recovered_url_base_name, val_name="recovered", allow_cache=allow_cache
    )

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
    df_all = pd.concat((df_merged, df_world)).sort_values(["country_region", "date"])

    # Remove regions
    df_no_region = (
        df_all.drop(columns=["province_state"])
        .groupby(["country_region", "date"])
        .sum()
        .reset_index()
    )

    # Add columns
    df_new_column = (
        df_no_region.assign(confirmed_total=df_no_region.confirmed)
        .assign(recovered_total=df_no_region.recovered)
        .assign(dead_total=df_no_region.dead)
        .assign(country=df_no_region.country_region)
        .assign(
            confirmed_daily=df_no_region.confirmed.subtract(
                df_no_region.confirmed.shift(1), fill_value=0
            ).clip(0)
        )
        .assign(
            recovered_daily=df_no_region.recovered.subtract(
                df_no_region.recovered.shift(1), fill_value=0
            ).clip(0)
        )
        .assign(
            dead_daily=df_no_region.dead.subtract(
                df_no_region.dead.shift(1), fill_value=0
            ).clip(0)
        )
        .drop(columns=["confirmed", "recovered", "dead", "country_region"])
    )

    df = df_new_column[
        [
            "country",
            "date",
            "lat",
            "long",
            "confirmed_total",
            "confirmed_daily",
            "recovered_total",
            "recovered_daily",
            "dead_total",
            "dead_daily",
        ]
    ]

    # Set recovered to int
    # df.recovered_total = df.recovered_total.fillna(-1)
    # df.recovered_total = pd.to_numeric(df.recovered_total, downcast="integer")
    # df.recovered_total = df.recovered_total.replace(-1, np.nan)

    return df
