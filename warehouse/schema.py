#import needed libraries
from sqlalchemy import create_engine
import pyodbc
import pandas as pd
import os
import psycopg2

#get password from environmnet var
pwd = os.environ['PGPASS']
uid = os.environ['PGUID']
#sql db details
database = "adventureworks"

# query formatting
def format_query(tbl, col, description):
    query = f"""
    - name: stg_{tbl}
      columns:
       {col}
       {description}    
"""
    return query 

#extract data from sql server
def extract():
    try:
        conn_string = f"host='localhost' dbname={database} user={uid} password={pwd}"
        src_conn = psycopg2.connect(conn_string)
        src_cursor = src_conn.cursor()
        # execute query
        src_cursor.execute(""" SELECT table_name FROM information_schema.tables 
                            WHERE table_schema = 'source' """)
        src_tables = src_cursor.fetchall()
        for tbl in src_tables:
            #query and load save data to dataframe
            #print(tbl[0])
            src_cursor.execute(f""" SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'source'
                            AND table_name   = '{tbl[0]}' """)
            src_columns = src_cursor.fetchall()
                #print(col[0])
            cols = []
            description = []
            for col in src_columns:
                cols.append("- name: " + col[0].lower())
                cols.append("  description: ' ' " )
            #
            columns = "\n       ".join(cols)
            descrip = "\n       ".join(description)
                #print(col[0])
            query = format_query(tbl[0], columns, descrip)
            print(query)
            file_name = 'schema.yml'
            f = open(file_name, 'a')  # open file in write mode
            #f.write("version: 2")
            #f.write("\n")
            #f.write("models:")
            f.write(query)
            f.close()
            #load(df, tbl[0])
    except Exception as e:
        print("Data extract error: " + str(e))
    finally:
        src_conn.close()

#load data to postgres

try:
    #call extract function
    extract()
except Exception as e:
    print("Error while extracting data: " + str(e))