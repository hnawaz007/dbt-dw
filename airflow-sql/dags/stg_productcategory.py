from airflow import DAG, task
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.operators.python import PythonOperator
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator


def transfer_source_to_target(**kwargs):
    """Get records from the Source and transfer to the Target database"""
    dest_table = kwargs.get('dest_table')
    sql = kwargs.get('sql')
    params = kwargs.get('params')

    source_hook = MsSqlHook(mssql_conn_id="sqlserver")
    #
    postgres_hook = PostgresHook(postgres_conn_id='postgres')
    engine = postgres_hook.get_sqlalchemy_engine()
    #
    df = source_hook.get_pandas_df(sql)
    df.to_sql(dest_table, engine, if_exists='replace', index=False)


with DAG(dag_id='stage_productcategory_dim',
         default_args={'owner': 'airflow'},
         schedule_interval=None,
         start_date=days_ago(2),
         template_searchpath='/opt/sql/',
         tags=['etl', 'analytics', 'product']) as dag:
    
    load_full_productcategory_data = PythonOperator(
    task_id='load_full_productcategory_data',
    python_callable=transfer_source_to_target,
    op_kwargs={
        'dest_table': 'stg_productcategory',
        'sql': 'select * from [dbo].[DimProductCategory]',
    })

    validate_productcategory_data = GreatExpectationsOperator(
        task_id = "gx_validate_productcategory",
        conn_id = 'postgres',
        data_context_root_dir="great_expectations",
        data_asset_name="public.stg_productcategory",
        expectation_suite_name="adventureworks_suite",
        return_json_dict=True,
    )

    load_full_productcategory_data >> validate_productcategory_data
