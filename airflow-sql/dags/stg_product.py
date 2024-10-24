from airflow import DAG, task
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator


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


with DAG(dag_id='products_dim_pipeline',
         default_args={'owner': 'airflow'},
         schedule_interval=None,
         start_date=days_ago(2),
         template_searchpath='/opt/sql/',
         tags=['etl', 'analytics', 'product']) as dag:

    load_full_products_data = PythonOperator(
        task_id='load_full_products',
        python_callable=transfer_source_to_target,
        op_kwargs={
            'dest_table': 'stg_products',
            'sql': 'select * from Production.Product',
        })
    
    load_full_productsubcategory_data = PythonOperator(
    task_id='load_full_productsubcategory_data',
    python_callable=transfer_source_to_target,
    op_kwargs={
        'dest_table': 'stg_productsubcategory',
        'sql': 'select * from Production.ProductSubcategory',
    })
    
    load_full_productcategory_data = PythonOperator(
    task_id='load_full_productcategory_data',
    python_callable=transfer_source_to_target,
    op_kwargs={
        'dest_table': 'stg_productcategory',
        'sql': 'select * from Production.ProductCategory',
    })

    join_products_tables = PostgresOperator(
        task_id='join_products_tables',
        postgres_conn_id='target',
        sql='stg_denormalized_product.sql'
    )

    load_full_products_data >> load_full_productsubcategory_data >> load_full_productcategory_data >> join_products_tables
