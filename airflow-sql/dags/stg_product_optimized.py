import json
from datetime import datetime
from airflow import DAG, task
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.hooks.base_hook import BaseHook
from sqlalchemy import create_engine

def transfer_source_to_target(dest_table, sql):
    """Get records from the Source and transfer to the Target database"""
    print("sql query received " + sql)
    print("dest table received " + dest_table)
    source_hook = MsSqlHook(mssql_conn_id="sqlserver")
    #
    conn = BaseHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    #
    df = source_hook.get_pandas_df(sql)
    df.to_sql(dest_table, engine, if_exists='replace', index=False)
    
def process_tbls():
    with open('/opt/sql/config.json') as json_file:
        data = json.load(json_file)
        configs = data['product']
        #print(len(data['tables']))
        for i in configs:
            print(i['dest_table'])
            dest_table = i['dest_table']
            print(i['src_sql'])
            sql = i['src_sql']
            transfer_source_to_target(dest_table, sql)
    return configs

default_args = {
    "owner": "hnawaz",
    "start_date": datetime(2023, 4, 13),
    'email': ['hnawaz@localmail.com'],
    'email_on_failure': True,
}


with DAG(dag_id='products_dim_optimized',
         default_args=default_args,
         schedule_interval="@once",
         template_searchpath='/opt/sql/',
         tags=['etl', 'analytics', 'product']) as dag:

    load_full_products_data = PythonOperator(
        task_id='load_full_products',
        python_callable=process_tbls
        )

    join_products_tables = PostgresOperator(
        task_id='join_products_tables',
        postgres_conn_id='postgres',
        sql='stg_denornamlized_product.sql'
    )

    load_full_products_data >> join_products_tables