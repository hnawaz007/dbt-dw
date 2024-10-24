import time
from datetime import datetime
from airflow.models.dag import DAG
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.base_hook import BaseHook
import pandas as pd
from sqlalchemy import create_engine

#extract tasks
@task()
def load_src_data():
    conn = BaseHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    #
    rows_imported = 0
    tbl = "src_taskflowlarge_dataset"
    sql = f'select * FROM dbo.large_dataset'
    hook = MsSqlHook(mssql_conn_id="sqlserver")
    df = hook.get_pandas_df(sql)
    print(f'importing rows {0} to { rows_imported +  len(df)}... for table {tbl} ')
    df.to_sql(tbl, engine, if_exists='replace', index=False)
    rows_imported += len(df)
    print("Data imported successful")
    return tbl
	
	
#Transformation tasks
@task()
def transform_src_data(tbl):
    con = PostgresHook(postgres_conn_id='postgres')
    conn = BaseHook.get_connection('postgres')
    rows_imported = 0
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pdf = con.get_pandas_df(f'SELECT * FROM public.{tbl} ')
    # Rename columns with rename function
    stg_tbl = "stg_taskflow_large_dataset"
    revised = pdf.rename(columns={"Index": "Symbol"})
    revised.to_sql(stg_tbl, engine, if_exists='replace', index=False)
    print(f'importing rows {0} to { rows_imported +  len(revised)}... for table {stg_tbl} ')
    return stg_tbl


#load
@task()
def load_table(tbl):
    rows_imported = 0
    con = PostgresHook(postgres_conn_id='postgres')
    conn = BaseHook.get_connection('postgres')
    engine = create_engine(f'postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}')
    pc = con.get_pandas_df(f'SELECT * FROM public.{tbl} ')
    #
    prd_tbl = "taskflow_large_dataset"
    pc.to_sql(prd_tbl, engine, if_exists='replace', index=False)
    print(f'importing rows {0} to { rows_imported +  len(pc)}... for table {prd_tbl} ')
    return {f"{prd_tbl} table processed ": "Data imported successful"}

# [START DAG]
with DAG(dag_id="relatively_large_dag_taskflow",schedule_interval="0 9 * * *", start_date=datetime(2022, 4, 12),catchup=False,  tags=["dataset_model"]) as dag:

    src_tbl = load_src_data()
    stg_tbl = transform_src_data(src_tbl)
    prd_model = load_table(stg_tbl)