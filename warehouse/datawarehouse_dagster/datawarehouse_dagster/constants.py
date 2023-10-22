import os
from pathlib import Path

from dagster_dbt import DbtCliResource
from dagster._utils import file_relative_path

dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
dbt = DbtCliResource(project_dir=os.fspath(dbt_project_dir))

# If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at runtime.
# Otherwise, we expect a manifest to be present in the project's target directory.
if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"):
    dbt_parse_invocation = dbt.cli(["parse"], manifest={}).wait()
    dbt_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
else:
    dbt_manifest_path = dbt_project_dir.joinpath("target", "manifest.json")

# Airbyte configs
AIRBYTE_CONNECTION_ID = os.environ.get("AIRBYTE_CONNECTION_ID", "dfe6eae2-7fd3-4114-8ffc-5c78d6757446")


AIRBYTE_CONFIG = {
    "host": os.environ.get("AIRBYTE_HOST", "localhost"),
    "port": os.environ.get("AIRBYTE_PORT", "8000"),
    "username":  "airbyte", 
    "password":  "password",
}

#
DBT_PROJECT_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../../dbt_project")
DBT_CONFIG = {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}