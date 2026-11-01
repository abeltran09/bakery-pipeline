import dagster as dg
import pandas as pd

YES_NO_COLUMNS = ["loyalty_member", "weekend", "promotion_applied"]


@dg.asset(group_name="staging", kinds={"pandas", "duckdb"})
def stg_bakery_sales(raw_bakery_sales: pd.DataFrame) -> pd.DataFrame:
    """Raw sales with lowercase column names, real dates and Yes/No columns as booleans.

    Nulls in festival and promotion_type mean "none" and are kept as-is.
    """
    df = raw_bakery_sales.copy()
    df.columns = df.columns.str.lower()
    df["date"] = pd.to_datetime(df["date"])
    df[YES_NO_COLUMNS] = df[YES_NO_COLUMNS].eq("Yes")
    return df
