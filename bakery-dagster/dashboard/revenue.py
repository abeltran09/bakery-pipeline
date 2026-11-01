import altair as alt
import pandas as pd
import streamlit as st

from common import bar_chart, sales_query, series_color, table_view

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Headline numbers. Rating is averaged per order, not per line, so big orders don't count twice.
kpis = sales_query("""
    SELECT SUM(total_bill) AS revenue,
           SUM(profit) AS profit,
           COUNT(DISTINCT order_id) AS orders,
           SUM(total_bill) / COUNT(DISTINCT order_id) AS avg_order_value,
           100.0 * SUM(unsold_units) / SUM(units_produced) AS waste_pct,
           (SELECT AVG(customer_rating) FROM (SELECT DISTINCT order_id, customer_rating FROM sales))
               AS avg_rating
    FROM sales
""").iloc[0]

if pd.isna(kpis.revenue):
    st.info("No sales match these filters.")
    st.stop()

tiles = st.columns(6)
tiles[0].metric("Revenue", f"{kpis.revenue:,.0f}")
tiles[1].metric("Profit", f"{kpis.profit:,.0f}")
tiles[2].metric("Orders", f"{int(kpis.orders):,}")
tiles[3].metric("Avg order value", f"{kpis.avg_order_value:,.2f}")
tiles[4].metric("Avg rating", f"{kpis.avg_rating:.2f} / 5")
tiles[5].metric("Waste", f"{kpis.waste_pct:.1f}%", help="Unsold units as a share of units produced")

st.subheader("Revenue by month")
monthly = sales_query("""
    SELECT date_trunc('month', sale_date) AS month, SUM(total_bill) AS revenue
    FROM sales GROUP BY ALL ORDER BY month
""")
hover = alt.selection_point(fields=["month"], nearest=True, on="pointerover", empty=False)
base = alt.Chart(monthly).encode(alt.X("month:T", title=None))
line = base.mark_line(strokeWidth=2, color=series_color()).encode(
    alt.Y("revenue:Q", title="Revenue"))
crosshair = (
    base.mark_rule(color="#898781")
    .encode(opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[alt.Tooltip("month:T", format="%b %Y"),
                     alt.Tooltip("revenue:Q", format=",.0f")])
    .add_params(hover)
)
point = line.mark_point(size=64, filled=True, color=series_color()).encode(
    opacity=alt.condition(hover, alt.value(1), alt.value(0)))
st.altair_chart(line + crosshair + point, width="stretch")
table_view(monthly.assign(month=monthly.month.dt.strftime("%Y-%m")))

left, right = st.columns(2)

with left:
    st.subheader("Most profitable products")
    top_products = sales_query("""
        SELECT product, SUM(profit) AS profit FROM sales
        GROUP BY ALL ORDER BY profit DESC LIMIT 10
    """)
    st.altair_chart(bar_chart(top_products, "product", "profit", "Profit",
                              horizontal=True, sort="-x"), width="stretch")
    table_view(top_products)

with right:
    st.subheader("Highest waste products")
    waste = sales_query("""
        SELECT product, 100.0 * SUM(unsold_units) / SUM(units_produced) AS waste_pct
        FROM sales GROUP BY ALL ORDER BY waste_pct DESC LIMIT 10
    """)
    st.altair_chart(bar_chart(waste, "product", "waste_pct", "Waste (% of units produced)",
                              horizontal=True, sort="-x"), width="stretch")
    table_view(waste)

left, right = st.columns(2)

with left:
    st.subheader("Revenue by hour of day")
    hourly = sales_query("""
        SELECT hour, SUM(total_bill) AS revenue FROM sales GROUP BY ALL ORDER BY hour
    """)
    st.altair_chart(bar_chart(hourly, "hour", "revenue", "Revenue",
                              horizontal=False, sort="ascending"), width="stretch")
    table_view(hourly)

with right:
    st.subheader("Revenue by day of week")
    weekday = sales_query("""
        SELECT day_of_week, SUM(total_bill) AS revenue FROM sales GROUP BY ALL
    """)
    st.altair_chart(bar_chart(weekday, "day_of_week", "revenue", "Revenue",
                              horizontal=False, sort=WEEKDAYS), width="stretch")
    table_view(weekday.set_index("day_of_week").reindex(WEEKDAYS).reset_index())
