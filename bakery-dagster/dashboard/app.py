"""Bakery sales dashboard, reading the tables the Dagster pipeline writes to bakery.duckdb.

Run from the bakery-dagster folder:  uv run streamlit run dashboard/app.py

This file runs on every page: it draws the shared filter row, then hands off to the page.
"""

import duckdb
import streamlit as st

from common import DATABASE_PATH, query

st.set_page_config(page_title="Bakery Sales", layout="wide")

page = st.navigation(
    [
        st.Page("revenue.py", title="Revenue", default=True),
        st.Page("customers.py", title="Customers"),
    ],
    position="top",
)

st.title(f"Bakery Sales · {page.title}")

if not DATABASE_PATH.exists():
    st.error(f"{DATABASE_PATH} not found. Materialize the Dagster pipeline first.")
    st.stop()

try:
    options = query("""
        SELECT min(CAST(date AS DATE)) AS first_day, max(CAST(date AS DATE)) AS last_day,
               list(DISTINCT store_id ORDER BY store_id) AS stores,
               (SELECT list(DISTINCT category ORDER BY category) FROM dim_product) AS categories
        FROM fact_orders
    """).iloc[0]
except duckdb.IOException:
    st.warning("The database is being rebuilt by Dagster. Refresh in a few seconds.")
    st.stop()

# One filter row scopes every chart on every page. Widgets live here, outside the pages,
# so the selection carries over when switching pages.
date_col, store_col, category_col = st.columns([2, 1, 2])
with date_col:
    picked = st.date_input(
        "Date range",
        value=(options.first_day, options.last_day),
        min_value=options.first_day,
        max_value=options.last_day,
    )
with store_col:
    stores = st.multiselect("Stores", list(options.stores), default=list(options.stores))
with category_col:
    categories = st.multiselect("Categories", list(options.categories),
                                default=list(options.categories))

# date_input returns a single date while the second end of the range is still being picked.
start, end = picked if len(picked) == 2 else (picked[0], picked[0])
if not stores or not categories:
    st.info("Select at least one store and one category.")
    st.stop()

st.session_state.filters = {"start": start, "end": end, "stores": stores,
                            "categories": categories}

page.run()

st.caption(f"Data from {DATABASE_PATH.name}, refreshed at most once a minute.")
