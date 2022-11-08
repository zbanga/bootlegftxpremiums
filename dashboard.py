import time
from datetime import datetime as dt

import streamlit as st

from data_downloader import (
    get_coin_perp_funding,
    load_cached_data,
)

perp_loading = st.text("Loading")

perp_funding_usd_table = st.empty()

error_message = "Error loading data. Please refresh the page or try again later."
RELOAD_INTERVAL_MINS = 15
while True:
    timestamp = dt.utcnow()
    update_text = (
        f"Last updated: UTC {timestamp}. Updated every {RELOAD_INTERVAL_MINS} minutes"
    )
    try:
        perp_cached = load_cached_data()
        perp_funding_usd_table.dataframe(
            get_coin_perp_funding(perp_cached)
        )  # TODO Implement loading of existing/saved/cached values if present
        perp_loading.text(update_text)
    except Exception as e:
        print(e)
        perp_funding_usd_table.error(error_message)

    time.sleep(RELOAD_INTERVAL_MINS * 60)
