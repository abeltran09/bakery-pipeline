import altair as alt
import pandas as pd
import streamlit as st

from common import bar_chart, sales_query, table_view

AGE_BANDS = ["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]

# One row per customer who bought something in the filtered slice. Every section below
# aggregates this, so "per customer" figures only count customers active in the slice.
CUSTOMER_SUMMARY = """
    customer_orders AS (
        SELECT customer_id,
               COUNT(DISTINCT order_id) AS orders,
               SUM(total_bill) AS revenue,
               SUM(profit) AS profit
        FROM sales GROUP BY customer_id
    ),
    customer_ratings AS (
        SELECT customer_id, AVG(customer_rating) AS avg_rating
        FROM (SELECT DISTINCT order_id, customer_id, customer_rating FROM sales)
        GROUP BY customer_id
    ),
    customers AS (
        SELECT c.*, o.orders, o.revenue, o.profit, r.avg_rating,
               CASE WHEN c.customer_age < 25 THEN '16-24'
                    WHEN c.customer_age < 35 THEN '25-34'
                    WHEN c.customer_age < 45 THEN '35-44'
                    WHEN c.customer_age < 55 THEN '45-54'
                    WHEN c.customer_age < 65 THEN '55-64'
                    ELSE '65+' END AS age_band
        FROM customer_orders o
        JOIN customer_ratings r USING (customer_id)
        JOIN dim_customer c USING (customer_id)
    )
"""


def customer_query(select: str) -> pd.DataFrame:
    """Run `select` with a `customers` table: one row per customer active in the filtered slice."""
    return sales_query(f", {CUSTOMER_SUMMARY} {select}")


kpis = customer_query("""
    SELECT COUNT(*) AS customers,
           100.0 * AVG(loyalty_member::INT) AS loyalty_pct,
           AVG(revenue) AS revenue_per_customer,
           AVG(orders) AS orders_per_customer,
           AVG(customer_age) AS avg_age
    FROM customers
""").iloc[0]

if not kpis.customers:
    st.info("No customers match these filters.")
    st.stop()

tiles = st.columns(5)
tiles[0].metric("Active customers", f"{int(kpis.customers):,}",
                help="Customers with at least one order in the selected slice")
tiles[1].metric("Loyalty members", f"{kpis.loyalty_pct:.0f}%")
tiles[2].metric("Revenue per customer", f"{kpis.revenue_per_customer:,.0f}")
tiles[3].metric("Orders per customer", f"{kpis.orders_per_customer:.1f}")
tiles[4].metric("Average age", f"{kpis.avg_age:.0f}")

st.subheader("Loyalty members vs non-members")
loyalty = customer_query("""
    SELECT CASE WHEN loyalty_member THEN 'Members' ELSE 'Non-members' END AS "Group",
           COUNT(*) AS "Customers",
           ROUND(AVG(orders), 1) AS "Orders per customer",
           ROUND(SUM(revenue) / SUM(orders), 2) AS "Avg order value",
           ROUND(AVG(revenue), 0) AS "Revenue per customer",
           ROUND(AVG(avg_rating), 2) AS "Avg rating"
    FROM customers GROUP BY ALL ORDER BY "Group"
""")
st.dataframe(loyalty, hide_index=True, width="stretch")

left, right = st.columns(2)

with left:
    st.subheader("Revenue per customer by segment")
    segments = customer_query("""
        SELECT customer_segment AS segment, COUNT(*) AS customers,
               AVG(revenue) AS revenue_per_customer, SUM(revenue) AS total_revenue
        FROM customers GROUP BY ALL ORDER BY revenue_per_customer DESC
    """)
    st.altair_chart(
        bar_chart(segments, "segment", "revenue_per_customer", "Revenue per customer",
                  horizontal=True, sort="-x",
                  extra_tooltips=[alt.Tooltip("customers:Q", title="Customers")]),
        width="stretch",
    )
    table_view(segments)

with right:
    st.subheader("Customers by age")
    ages = customer_query("""
        SELECT age_band, COUNT(*) AS customers, AVG(revenue) AS revenue_per_customer
        FROM customers GROUP BY ALL
    """)
    ages = ages.set_index("age_band").reindex(AGE_BANDS).dropna().reset_index()
    st.altair_chart(
        bar_chart(ages, "age_band", "customers", "Customers", horizontal=False,
                  sort=AGE_BANDS,
                  extra_tooltips=[alt.Tooltip("revenue_per_customer:Q", format=",.0f",
                                              title="Revenue per customer")]),
        width="stretch",
    )
    table_view(ages)

left, right = st.columns(2)

with left:
    st.subheader("How often customers order")
    frequency = customer_query("""
        SELECT orders, COUNT(*) AS customers FROM customers GROUP BY ALL ORDER BY orders
    """)
    st.altair_chart(
        bar_chart(frequency, "orders", "customers", "Customers", horizontal=False,
                  sort="ascending").encode(alt.X("orders:O", title="Orders per customer")),
        width="stretch",
    )
    table_view(frequency)

with right:
    st.subheader("Revenue per customer by gender")
    genders = customer_query("""
        SELECT customer_gender AS gender, COUNT(*) AS customers,
               AVG(revenue) AS revenue_per_customer
        FROM customers GROUP BY ALL ORDER BY revenue_per_customer DESC
    """)
    st.altair_chart(
        bar_chart(genders, "gender", "revenue_per_customer", "Revenue per customer",
                  horizontal=True, sort="-x",
                  extra_tooltips=[alt.Tooltip("customers:Q", title="Customers")]),
        width="stretch",
    )
    table_view(genders)

st.subheader("Top customers")
top = customer_query("""
    SELECT customer_id AS "Customer", customer_segment AS "Segment", customer_age AS "Age",
           loyalty_member AS "Loyalty member", orders AS "Orders",
           ROUND(revenue, 2) AS "Revenue", ROUND(profit, 2) AS "Profit",
           ROUND(avg_rating, 2) AS "Avg rating"
    FROM customers ORDER BY revenue DESC LIMIT 20
""")
st.dataframe(top, hide_index=True, width="stretch")
