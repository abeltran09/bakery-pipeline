import dagster as dg
import pandas as pd


def key_is_unique_and_present(df: pd.DataFrame, key: str) -> dg.AssetCheckResult:
    nulls = int(df[key].isna().sum())
    duplicates = int(df[key].duplicated().sum())
    return dg.AssetCheckResult(
        passed=nulls == 0 and duplicates == 0,
        metadata={"null_keys": nulls, "duplicate_keys": duplicates},
    )


@dg.asset_check(asset="dim_customer")
def customer_id_is_unique(dim_customer: pd.DataFrame) -> dg.AssetCheckResult:
    return key_is_unique_and_present(dim_customer, "customer_id")


@dg.asset_check(asset="dim_product")
def product_is_unique(dim_product: pd.DataFrame) -> dg.AssetCheckResult:
    return key_is_unique_and_present(dim_product, "product")


@dg.asset_check(asset="dim_date")
def date_is_unique(dim_date: pd.DataFrame) -> dg.AssetCheckResult:
    return key_is_unique_and_present(dim_date, "date")


@dg.asset_check(asset="fact_orders")
def order_id_is_unique(fact_orders: pd.DataFrame) -> dg.AssetCheckResult:
    return key_is_unique_and_present(fact_orders, "order_id")


@dg.asset_check(asset="fact_orders")
def customer_rating_in_range(fact_orders: pd.DataFrame) -> dg.AssetCheckResult:
    out_of_range = int((~fact_orders["customer_rating"].between(1, 5)).sum())
    return dg.AssetCheckResult(passed=out_of_range == 0, metadata={"out_of_range": out_of_range})


@dg.asset_check(
    asset="fact_order_items",
    additional_ins={"raw_bakery_sales": dg.AssetIn("raw_bakery_sales")},
)
def order_items_match_raw(
    fact_order_items: pd.DataFrame, raw_bakery_sales: pd.DataFrame
) -> dg.AssetCheckResult:
    """Every raw sales row should become exactly one order item."""
    return dg.AssetCheckResult(
        passed=len(fact_order_items) == len(raw_bakery_sales) > 0,
        metadata={"order_items": len(fact_order_items), "raw_rows": len(raw_bakery_sales)},
    )


@dg.asset_check(asset="fact_order_items")
def order_item_values_in_range(fact_order_items: pd.DataFrame) -> dg.AssetCheckResult:
    bad_quantity = int((fact_order_items["quantity"] <= 0).sum())
    bad_waste_pct = int((~fact_order_items["waste_pct"].between(0, 100)).sum())
    missing_order_ids = int(fact_order_items["order_id"].isna().sum())
    return dg.AssetCheckResult(
        passed=bad_quantity == bad_waste_pct == missing_order_ids == 0,
        metadata={
            "non_positive_quantity": bad_quantity,
            "waste_pct_outside_0_100": bad_waste_pct,
            "missing_order_ids": missing_order_ids,
        },
    )
