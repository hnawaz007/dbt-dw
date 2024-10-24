from pendulum import datetime

from airflow import DAG
from airflow_dbt.operators.dbt_operator import (
    DbtSeedOperator,
    DbtSnapshotOperator,
    DbtRunOperator,
    DbtTestOperator,
    DbtDepsOperator
)

# We're hardcoding this value here for the purpose of the demo, but in a production environment this
# would probably come from a config file and/or environment variables!
DBT_PROJECT_DIR = "/opt/dbt"
DBT_PROFILE_DIR = "/opt/dbt/profiles"

with DAG(
    "dbt_operator_dag",
    start_date=datetime(2023, 4, 13),
    description="A sample Airflow DAG to invoke dbt runs using dbt operator",
    schedule_interval=None,
    catchup=False,
    default_args={
    },
) as dag:
  
    dbt_deps = DbtDepsOperator(
        task_id="dbt_deps",
        dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILE_DIR,
    )

    dbt_seed = DbtSeedOperator(
        task_id="dbt_seed",
        dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILE_DIR,
    )
    
    dbt_run = dbt_run = DbtRunOperator(
        task_id="dbt_run",
        dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILE_DIR,
        full_refresh=True,
        )
    
    dbt_test = DbtTestOperator(
        task_id="dbt_test",
        dir=DBT_PROJECT_DIR,
        profiles_dir=DBT_PROFILE_DIR,
    )

    dbt_deps >> dbt_seed >> dbt_run >> dbt_test