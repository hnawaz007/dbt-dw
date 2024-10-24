from airflow import DAG, task
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.oracle.hooks.oracle import OracleHook
from airflow.operators.python import PythonOperator


def transfer_source_to_target():
    """Get records from the Source and transfer to the Target database"""
    # source db
    sql = "SELECT * FROM DBTESTER.EMPLOYEE"
    source_hook = OracleHook(oracle_conn_id="oracledb")
    df = source_hook.get_pandas_df(sql)
    # destination db
    postgres_hook = PostgresHook(postgres_conn_id='postgres')
    engine = postgres_hook.get_sqlalchemy_engine()
    df.to_sql("stg_employee", engine, if_exists='replace', index=False)


with DAG(dag_id='employee_dim_pipeline',
         default_args={'owner': 'airflow'},
         schedule_interval=None,
         start_date=days_ago(2),
         tags=['etl', 'analytics', 'employee']) as dag:

    load_full_employee_data = PythonOperator(
        task_id='load_full_employee',
        python_callable=transfer_source_to_target
        )

    load_full_employee_data
