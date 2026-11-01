from pathlib import Path

import dagster as dg
from dagster_duckdb_pandas import DuckDBPandasIOManager

# bakery-dagster/bakery.duckdb, regardless of the working directory Dagster runs from
DATABASE_PATH = Path(__file__).parents[3] / "bakery.duckdb"


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            "io_manager": DuckDBPandasIOManager(
                database=str(DATABASE_PATH),
                # Not "bakery": that name is already taken by the database file's catalog.
                schema="main",
            ),
        }
    )
