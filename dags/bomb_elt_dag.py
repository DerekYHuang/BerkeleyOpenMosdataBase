"""
bomb_elt_dag.py
---------------
Apache Airflow DAG orchestrating the full BOMB ELT pipeline:
  1. Validate raw HDF5 data in S3
  2. Convert HDF5 → Parquet
  3. Upload Parquet to S3 processed zone
  4. Trigger dbt transformations
  5. Run dbt data quality tests
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="bomb_transistor_elt_pipeline",
    description="ELT pipeline for UC Berkeley BOMB transistor dataset",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@weekly",   # BOMB is a static dataset; weekly reruns for testing
    catchup=False,
    tags=["semiconductor", "elt", "bomb", "dbt"],
) as dag:

    def validate_raw_data(**kwargs):
        """Check that the BOMB HDF5 file exists in S3 raw zone."""
        import boto3, os
        s3 = boto3.client("s3")
        bucket = os.getenv("S3_BUCKET_NAME", "bomb-transistor-pipeline")
        key = "raw/bomb/Technology_A_data.hdf5"
        try:
            s3.head_object(Bucket=bucket, Key=key)
            print(f"✅ Raw file confirmed in S3: s3://{bucket}/{key}")
        except Exception as e:
            raise FileNotFoundError(f"Raw file not found in S3: {e}")

    def convert_hdf5_to_parquet(**kwargs):
        """Load HDF5 from S3, flatten, and write Parquet to processed zone."""
        import boto3, os, tempfile
        from ingestion.download_bomb import SimData
        from ingestion.hdf5_to_parquet import flatten_bomb_to_dataframe, add_thermal_stability_flag, save_to_parquet

        s3 = boto3.client("s3")
        bucket = os.getenv("S3_BUCKET_NAME", "bomb-transistor-pipeline")

        with tempfile.TemporaryDirectory() as tmpdir:
            local_hdf5 = os.path.join(tmpdir, "Technology_A_data.hdf5")
            s3.download_file(bucket, "raw/bomb/Technology_A_data.hdf5", local_hdf5)

            sim = SimData.load(local_hdf5)
            df = flatten_bomb_to_dataframe(sim)
            df = add_thermal_stability_flag(df)

            local_parquet = os.path.join(tmpdir, "bomb_transistor_flat.parquet")
            save_to_parquet(df, local_parquet)

            s3.upload_file(local_parquet, bucket, "processed/bomb/bomb_transistor_flat.parquet")
            print(f"✅ Parquet uploaded to S3: {len(df):,} rows")

    task_validate_raw = PythonOperator(
        task_id="validate_raw_data",
        python_callable=validate_raw_data,
    )

    task_convert_parquet = PythonOperator(
        task_id="convert_hdf5_to_parquet",
        python_callable=convert_hdf5_to_parquet,
    )

    task_dbt_run = BashOperator(
        task_id="dbt_run_transformations",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir . --target prod",
    )

    task_dbt_test = BashOperator(
        task_id="dbt_test_data_quality",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir . --target prod",
    )

    # DAG dependency chain
    task_validate_raw >> task_convert_parquet >> task_dbt_run >> task_dbt_test
