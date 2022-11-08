import datetime
import os

import ccxt
import pandas as pd
import streamlit as st
from pathlib import Path


def load_cached_data():
    perp_cached = pd.DataFrame()
    my_file = Path("./data/perp_data.csv")
    if my_file.is_file():
        perp_cached = pd.read_csv("./data/perp_data.csv")
        perp_cached = perp_cached.drop_duplicates()
    return perp_cached


def get_ftx_perp_markets(ftx):
    markets = ftx.load_markets()
    perp_list = []
    for i in markets.values():
        if i.get("type", "") in "swap":
            perp_list.append(i.get("id"))
    perp_list = set(perp_list)
    return perp_list


def fetch_funding_rate(ftx, perp_cached, symbol):
    if perp_cached.empty or (symbol not in perp_cached.future.values):
        limit = 150
        funding_rate = ftx.fetchFundingRateHistory(
            symbol,
            since=int(round(datetime.datetime.utcnow().timestamp() * 1000)),
            limit=limit,
        )
        funding_df = pd.DataFrame(funding_rate)
        funding_df = pd.concat(
            [funding_df.drop(["info"], axis=1), funding_df["info"].apply(pd.Series)],
            axis=1,
        )
        funding_df = funding_df.drop_duplicates()
        funding_df.to_csv(
            "./data/perp_data.csv",
            mode="a",
            header=not os.path.exists("./data/perp_data.csv"),
            index=False,
        )
        combined_df = funding_df
    else:
        perp_cached = load_cached_data()
        start_time = int(
            perp_cached[perp_cached["future"] == symbol]
            .sort_values("timestamp", ascending=True)["timestamp"]
            .tail(1)
            .reset_index(drop=True)[0]
        )
        funding_rate = ftx.fetchFundingRateHistory(
            symbol,
            since=start_time,
        )
        funding_df = pd.DataFrame(funding_rate)
        funding_df = pd.concat(
            [funding_df.drop(["info"], axis=1), funding_df["info"].apply(pd.Series)],
            axis=1,
        )
        funding_df = funding_df.drop_duplicates()
        perp_cached["timestamp"] = perp_cached["timestamp"].astype(str).astype("int64")
        funding_df["timestamp"] = funding_df["timestamp"].astype(str).astype("int64")
        funding_df = funding_df[funding_df["timestamp"] < start_time]
        funding_df = funding_df[funding_df["future"] == symbol]
        combined_df = pd.concat([perp_cached, funding_df])  # TODO write deduplication
        combined_df = combined_df.drop_duplicates()
        combined_df = combined_df.sort_values(["future", "timestamp"])
        funding_df.to_csv(
            "./data/perp_data.csv",
            mode="a",
            header=not os.path.exists("./data/perp_data.csv"),
            index=False,
        )
    return combined_df


def fetch_open_interest(ftx, symbol):
    open_interest = ftx.fetchOpenInterest(symbol)
    return open_interest


def fetch_volume(ftx, symbol):
    ticker_info = ftx.fetch_ticker(symbol)
    return ticker_info


def fetch_all_funding_rates(ftx, perp_list, perp_cached):
    funding_rates = []
    payment_frequency = 24
    for symbol in perp_list:
        rates = fetch_funding_rate(ftx, perp_cached, symbol)
        interest = fetch_open_interest(ftx, symbol)
        volume = fetch_volume(ftx, symbol)
        ticker_price = float(volume.get("info", "").get("last", ""))
        ticker_volume = float(volume.get("info", "").get("volumeUsd24h", ""))
        funding_rate = [float(i.get("fundingRate")) for i in rates]
        open_interest = float(interest.get("openInterestAmount", "")) * ticker_price
        next_funding_rate = float(interest.get("info", "").get("nextFundingRate", ""))
        one_hour = funding_rate[-1]
        avg_three_hours = sum(funding_rate[-3:]) / 3
        avg_daily = sum(funding_rate[-payment_frequency:]) / payment_frequency
        avg_three_days = sum(funding_rate[-3 * payment_frequency :]) / (
            3 * payment_frequency
        )
        avg_seven_days = sum(funding_rate[-7 * payment_frequency :]) / (
            7 * payment_frequency
        )
        avg_fourteen_days = sum(funding_rate[-14 * payment_frequency :]) / (
            14 * payment_frequency
        )
        avg_thirty_days = sum(funding_rate[-30 * payment_frequency :]) / (
            30 * payment_frequency
        )
        funding_rates.append(
            [
                symbol,
                ticker_volume,
                open_interest,
                next_funding_rate,
                one_hour,
                avg_three_hours,
                avg_daily,
                avg_three_days,
                avg_seven_days,
                avg_fourteen_days,
                avg_thirty_days,
            ]
        )
    return funding_rates


def annualise_funding_rate(df):
    df[["Next Funding", "1h", "3h", "1d", "3d", "7d", "14d", "30d",]] = (
        df[
            [
                "Next Funding",
                "1h",
                "3h",
                "1d",
                "3d",
                "7d",
                "14d",
                "30d",
            ]
        ]
        * 24
        * 365
    )
    # Such a bad way of doing this.

    df = df.sort_values(by="1h", ascending=False).reset_index(drop=True)
    return df


def round_numbers(df):
    df_styled = df.style.format(
        {
            "Ticker Volume": "${:20,.0f}",
            "Open Interest": "${:20,.0f}",
            "Next Funding": "{:.2%}",
            "1h": "{:.2%}",
            "3h": "{:.2%}",
            "1d": "{:.2%}",
            "3d": "{:.2%}",
            "7d": "{:.2%}",
            "14d": "{:.2%}",
            "30d": "{:.2%}",
        }
    )

    return df_styled


@st.cache(ttl=310, allow_output_mutation=True)
def get_coin_perp_funding(perp_cached):
    ftx = (
        ccxt.ftx()
    )  # Don't know if this is a good idea to pass objects around like this
    perp_list = get_ftx_perp_markets(ftx)
    funding_rates = fetch_all_funding_rates(ftx, perp_list, perp_cached)
    df = pd.DataFrame(
        funding_rates,
        columns=[
            "symbol",
            "Ticker Volume",
            "Open Interest",
            "Next Funding",
            "1h",
            "3h",
            "1d",
            "3d",
            "7d",
            "14d",
            "30d",
        ],
    )
    df = annualise_funding_rate(df)
    df_styled = round_numbers(df)
    return df_styled
