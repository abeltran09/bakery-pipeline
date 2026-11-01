from pathlib import Path

import dagster as dg
import pandas as pd

CSV_PATH = Path(__file__).parent / "data" / "bakery_sales_dataset.csv"


@dg.asset(group_name="raw", kinds={"pandas", "duckdb"})
def raw_bakery_sales(context: dg.AssetExecutionContext) -> pd.DataFrame:
    """Bakery sales CSV loaded as-is, one row per order line."""
    # The file starts with a UTF-8 BOM; utf-8-sig strips it from the first column name.
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    context.add_output_metadata({"row_count": len(df)})
    return df
