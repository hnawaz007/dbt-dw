from datetime import datetime 
from datetime import timedelta
from pathlib import Path
from airflow import DAG
from dbt_airflow.core.config import DbtAirflowConfig
from dbt_airflow.core.config import DbtProfileConfig
from dbt_airflow.core.config import DbtProjectConfig
from dbt_airflow.core.task_group import DbtTaskGroup
from dbt_airflow.operators.execution import ExecutionOperator


with DAG(
    dag_id='dbt_workflow_orchestration',
    start_date=datetime(2024, 10, 18),
    catchup=False,
    tags=['dbt dag'],
    default_args={
        'owner': 'airflow',
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    
) as dag:


    run_dbt = DbtTaskGroup(
        group_id='transform',
        dbt_project_config=DbtProjectConfig(
            project_path=Path('/opt/dbt'),
            manifest_path=Path('/opt/dbt/target/manifest.json'),
        ),
        dbt_profile_config=DbtProfileConfig(
            profiles_path=Path('/opt/dbt'),
            target='dev',
        ),
        dbt_airflow_config=DbtAirflowConfig(
            execution_operator=ExecutionOperator.BASH,
        ),
    )

    run_dbt