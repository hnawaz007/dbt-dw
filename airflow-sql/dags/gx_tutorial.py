from airflow.decorators import dag, task
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import datetime
from airflow.utils.dates import timedelta
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator

postgres_conn_id='postgres'

@dag(schedule_interval="0 10 * * *", start_date=datetime(2022, 2, 15), catchup=False, tags=['test_gx_expec'])
def run_gx():
    gx_validate = GreatExpectationsOperator(
        task_id = "gx_validate_productcategory",
        conn_id = postgres_conn_id,
        data_context_root_dir="great_expectations",
        data_asset_name="public.dim_product_category",
        expectation_suite_name="adventureworks_suite",
        return_json_dict=True,
    )

#
tutorial_gx_dag = run_gx()