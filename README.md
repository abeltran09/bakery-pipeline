# 🥐 Bakery Sales Pipeline

An end-to-end data pipeline that turns a flat CSV of bakery sales into a queryable star schema and an interactive dashboard.

**Dagster** orchestrates the pipeline, **DuckDB** stores the warehouse, and **Streamlit** serves the dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Dagster](https://img.shields.io/badge/Dagster-1.13-4F43DD?logo=dagster&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-warehouse-FFF000?logo=duckdb&logoColor=black)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)

![Revenue dashboard](docs/images/dashboard-revenue.png)

## Highlights

- **Layered pipeline:** raw → staging → warehouse. Each step is a Dagster asset with lineage you can see in the UI.
- **Star schema in DuckDB:** 3 dimension tables and 2 fact tables, built from 19,321 order lines.
- **Data quality checks:** unique keys, row count reconciliation, and value range checks run after every build.
- **Automatic reruns:** a file sensor rebuilds everything when the source CSV changes.
- **Two-page dashboard:** revenue and customer breakdowns, with shared filters for date, store and category.

## Architecture

```mermaid
flowchart LR
    CSV[(bakery_sales_dataset.csv)] --> RAW[raw_bakery_sales]
    RAW --> STG[stg_bakery_sales]
    STG --> DC[dim_customer]
    STG --> DP[dim_product]
    STG --> DD[dim_date]
    STG --> FO[fact_orders]
    STG --> FI[fact_order_items]
    DC & DP & DD & FO & FI --> DB[(bakery.duckdb)]
    DB --> APP[Streamlit dashboard]
```

### Asset lineage in Dagster

![Dagster asset lineage graph](docs/images/dagster-lineage.png)

| Layer | Asset | What it does |
| --- | --- | --- |
| Raw | `raw_bakery_sales` | Loads the CSV as-is, one row per order line |
| Staging | `stg_bakery_sales` | Lowercases column names, parses dates, converts Yes/No columns to booleans |
| Warehouse | `dim_customer` | One row per customer (500) |
| | `dim_product` | One row per product (35) |
| | `dim_date` | One row per day (731), with weather and festivals |
| | `fact_orders` | One row per order (6,576) |
| | `fact_order_items` | One row per product within an order (19,321) |

Each asset returns a pandas DataFrame. Dagster's `DuckDBPandasIOManager` writes it to a DuckDB table of the same name, so the asset code contains no database code.

## Data model

```mermaid
erDiagram
    dim_customer ||--o{ fact_orders : places
    dim_date ||--o{ fact_orders : "happens on"
    fact_orders ||--|{ fact_order_items : contains
    dim_product ||--o{ fact_order_items : "sold as"

    dim_customer {
        string customer_id PK
        int customer_age
        string customer_gender
        string customer_segment
        bool loyalty_member
    }
    dim_product {
        string product PK
        string category
        string storage_type
        string perishability
    }
    dim_date {
        date date PK
        string day_of_week
        bool weekend
        string season
        string festival
        string weather
        float temperature
    }
    fact_orders {
        string order_id PK
        string customer_id FK
        date date FK
        string store_id
        int hour
        string payment_method
        bool promotion_applied
        int customer_rating
    }
    fact_order_items {
        string order_id FK
        string product FK
        int quantity
        float selling_price
        float total_bill
        float profit
        int units_produced
        int unsold_units
        float waste_pct
    }
```

## Data quality checks

Dagster asset checks run after each table is built and show pass/fail in the UI:

| Table | Check |
| --- | --- |
| `dim_customer`, `dim_product`, `dim_date`, `fact_orders` | Primary key is unique and never null |
| `fact_order_items` | Exactly one row per raw sales row |
| `fact_order_items` | Quantity is positive, `waste_pct` is between 0 and 100, no missing order IDs |
| `fact_orders` | `customer_rating` is between 1 and 5 |

## Dashboard

### Revenue

Headline numbers for revenue, profit, orders, average order value, rating and waste, plus monthly revenue, the most profitable and most wasteful products, and sales by hour and weekday.

![Revenue dashboard](docs/images/dashboard-revenue.png)

### Customers

Loyalty members compared with non-members, revenue per customer by segment and gender, age bands, order frequency, and a top customers table.

![Customers dashboard](docs/images/dashboard-customers.png)

## Getting started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs Python for you if needed)
- The [bakery sales dataset](LINK_TO_KAGGLE_DATASET) from Kaggle

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/bakery-pipeline.git
cd bakery-pipeline/bakery-dagster
uv sync
```

### 2. Add the dataset

Save the CSV as:

```
bakery-dagster/src/bakery_dagster/defs/data/bakery_sales_dataset.csv
```

### 3. Run the pipeline

```bash
uv run dg dev
```

Open http://localhost:3000, go to **Lineage**, and click **Materialize all**. This builds every table into `bakery-dagster/bakery.duckdb` and runs the data quality checks.

Optional: under **Automation**, turn on `bakery_csv_sensor` to rebuild automatically whenever the CSV changes.

### 4. Open the dashboard

In a second terminal, also inside `bakery-dagster`:

```bash
uv run streamlit run dashboard/app.py
```

Open http://localhost:8501.

### 5. Query the warehouse yourself (optional)

```python
import duckdb

con = duckdb.connect("bakery.duckdb", read_only=True)
con.sql("""
    SELECT p.category, ROUND(SUM(i.profit), 2) AS profit
    FROM fact_order_items i
    JOIN dim_product p USING (product)
    GROUP BY ALL
    ORDER BY profit DESC
""").show()
con.close()
```

> [!NOTE]
> DuckDB allows only one process to write to the database file at a time. Close any notebook connections before clicking **Materialize all**. The dashboard is safe to leave open: it opens a short read-only connection for each query.

## Project structure

```
bakery-pipeline/
├── docs/images/                 # README screenshots
└── bakery-dagster/
    ├── pyproject.toml
    ├── dashboard/
    │   ├── app.py               # entry point: page navigation and shared filters
    │   ├── common.py            # DuckDB queries and chart helpers
    │   ├── revenue.py           # Revenue page
    │   └── customers.py         # Customers page
    └── src/bakery_dagster/defs/
        ├── data/                # source CSV (not committed)
        ├── resources.py         # DuckDB IO manager
        ├── raw.py               # extract
        ├── staging.py           # clean and type
        ├── warehouse.py         # star schema
        ├── checks.py            # asset checks
        └── automation.py        # job and file sensor
```

## Tech stack

| Tool | Role |
| --- | --- |
| [Dagster](https://dagster.io/) | Orchestration, lineage, asset checks, sensors |
| [DuckDB](https://duckdb.org/) | Embedded analytical warehouse |
| [pandas](https://pandas.pydata.org/) | Transformations |
| [Streamlit](https://streamlit.io/) + [Altair](https://altair-viz.github.io/) | Dashboard and charts |
| [uv](https://docs.astral.sh/uv/) | Dependency and environment management |
