import dagster as dg

from bakery_dagster.defs.raw import CSV_PATH

bakery_pipeline_job = dg.define_asset_job(
    name="bakery_pipeline_job",
    selection=dg.AssetSelection.all(),
    description="Rebuild every table in bakery.duckdb from the sales CSV and run all asset checks.",
)


@dg.sensor(job=bakery_pipeline_job, minimum_interval_seconds=30)
def bakery_csv_sensor(context: dg.SensorEvaluationContext) -> dg.SensorResult | dg.SkipReason:
    """Rebuild the pipeline whenever the sales CSV is replaced or edited."""
    if not CSV_PATH.exists():
        return dg.SkipReason(f"{CSV_PATH.name} not found")

    # The cursor stores the modification time of the last file version we ran for.
    modified_at = str(CSV_PATH.stat().st_mtime)
    if modified_at == context.cursor:
        return dg.SkipReason(f"{CSV_PATH.name} unchanged since last run")

    return dg.SensorResult(
        run_requests=[dg.RunRequest(run_key=modified_at)],
        cursor=modified_at,
    )
