"""Database access and chart helpers shared by every dashboard page."""

from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

DATABASE_PATH = Path(__file__).parents[1] / "bakery.duckdb"

# Every row of every chart starts from this: order lines joined to their order, product and
# date, narrowed by the filter row. Pages aggregate on top of it.
FILTERED_SALES = """
    SELECT i.*, o.customer_id, o.store_id, o.hour, o.customer_rating,
           CAST(o.date AS DATE) AS sale_date, p.category, d.day_of_week
    FROM fact_order_items i
    JOIN fact_orders o USING (order_id)
    JOIN dim_product p USING (product)
    JOIN dim_date d ON d.date = o.date
    WHERE CAST(o.date AS DATE) BETWEEN $start AND $end
      AND list_contains($stores, o.store_id)
      AND list_contains($categories, p.category)
"""


@st.cache_data(ttl=60, show_spinner=False)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    # Open and close a read-only connection per query so the dashboard never holds a lock
    # that would stop Dagster from rebuilding the tables.
    with duckdb.connect(str(DATABASE_PATH), read_only=True) as con:
        return con.execute(sql, params or {}).df()


def sales_query(select: str) -> pd.DataFrame:
    """Run `select` against a `sales` CTE limited to the filter row's current selection."""
    return query(f"WITH sales AS ({FILTERED_SALES}) {select}", st.session_state.filters)


def series_color() -> str:
    """Categorical slot 1, stepped for whichever theme the viewer is using."""
    theme = getattr(getattr(st.context, "theme", None), "type", None)
    return "#3987e5" if theme == "dark" else "#2a78d6"


def table_view(df: pd.DataFrame) -> None:
    with st.expander("View data"):
        st.dataframe(df, hide_index=True, width="stretch")


def bar_chart(df: pd.DataFrame, category: str, value: str, value_title: str,
              horizontal: bool, sort: list[str] | str,
              extra_tooltips: list[alt.Tooltip] | None = None) -> alt.Chart:
    category_enc = alt.X if not horizontal else alt.Y
    value_enc = alt.Y if not horizontal else alt.X
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, color=series_color())
        .encode(
            category_enc(f"{category}:O", sort=sort, title=None),
            value_enc(f"{value}:Q", title=value_title),
            tooltip=[alt.Tooltip(f"{category}:O"), alt.Tooltip(f"{value}:Q", format=",.1f"),
                     *(extra_tooltips or [])],
        )
    )
