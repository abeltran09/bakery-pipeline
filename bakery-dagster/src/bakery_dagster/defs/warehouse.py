import dagster as dg
import pandas as pd

WAREHOUSE = {"group_name": "warehouse", "kinds": {"pandas", "duckdb"}}


@dg.asset(**WAREHOUSE)
def dim_customer(stg_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """One row per customer."""
    return (stg_bakery_sales[["customer_id", "customer_age", "customer_gender",
                              "customer_segment", "loyalty_member"]]
            .drop_duplicates("customer_id"))


@dg.asset(**WAREHOUSE)
def dim_product(stg_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """One row per product. shelf_life_days varies per sale, so it lives on fact_order_items."""
    return (stg_bakery_sales[["product", "category", "storage_type", "perishability"]]
            .drop_duplicates("product"))


@dg.asset(**WAREHOUSE)
def dim_date(stg_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """One row per calendar date, including that day's weather and festival."""
    return (stg_bakery_sales[["date", "year", "month", "day", "day_of_week", "weekend",
                              "season", "festival", "weather", "temperature"]]
            .drop_duplicates("date"))


@dg.asset(**WAREHOUSE)
def fact_orders(stg_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """One row per order."""
    return (stg_bakery_sales[["order_id", "customer_id", "store_id", "date", "hour", "time",
                              "payment_method", "promotion_applied", "promotion_type",
                              "customer_rating"]]
            .drop_duplicates("order_id"))


@dg.asset(**WAREHOUSE)
def fact_order_items(stg_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """One row per product within an order."""
    return stg_bakery_sales[["order_id", "product", "quantity", "unit_price", "cost_price",
                             "discount_percentage", "selling_price", "total_bill", "profit",
                             "shelf_life_days", "units_produced", "units_sold", "unsold_units",
                             "stock_available", "waste_pct"]]
