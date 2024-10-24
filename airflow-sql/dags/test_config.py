import json
import time
from datetime import datetime
from airflow.decorators import dag, task
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from sqlalchemy import create_engine
from airflow.hooks.base_hook import BaseHook


def transfer_source_to_target(dest_table, sql):
    """Get records from the Source and transfer to the Target database"""
    print("sql query received " + sql)
    print("dest table received " + dest_table)
    source_hook = MsSqlHook(mssql_conn_id="source")
    # = PostgresHook(postgres_conn_id='target')
    #
    postgres_hook = PostgresHook(postgres_conn_id='target')
    engine = postgres_hook.get_sqlalchemy_engine()
    #
    df = source_hook.get_pandas_df(sql)
    #data_extracted = source_hook.get_records(sql=sql, parameters=params)
    #postgres_hook.insert_rows(dest_table, data_extracted, commit_every=1000)
    df.to_sql(dest_table, engine, if_exists='replace', index=False)
    
def execute_sql(sql):
    postgres_hook = PostgresHook(postgres_conn_id='target')
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()
    #
    sql = sql
    cursor.execute(sql)

    cursor.close()
    conn.commit()



@dag(schedule_interval="0 10 * * *", start_date=datetime(2022, 2, 15), catchup=False, template_searchpath='/opt/sql/', tags=['test_etl_cong'])
def test_etl_cong():
    @task()
    def get_configs():
        with open('/opt/sql/config.json') as json_file:
            data = json.load(json_file)
            configs = data['tables']
            #print(len(data['tables']))
            return configs
            #for i in data['tables']:
                #print(i['dest_table'])
                #print(i['sql'])
    #
    @task()
    def process_table(tbl_dict: dict):
        for i in tbl_dict:
            print(i['dest_table'])
            dest_table = i['dest_table']
            print(i['sql'])
            sql = i['sql']
            transfer_source_to_target(dest_table, sql)
            return tbl_dict
    
    @task()
    def denormalize_tbl(tbl_dict: dict):
        sqlfile='/opt/sql/stg_denormalized_product.sql'
        sql = open(sqlfile, mode='r', encoding='utf-8-sig').read()
        print(sql)
        execute_sql(sql)

    tbl_dict = get_configs()
    tbl_process = process_table(tbl_dict)
    denor_tbl = denormalize_tbl(tbl_process)
#
tutorial_etl_dag = test_etl_cong()
