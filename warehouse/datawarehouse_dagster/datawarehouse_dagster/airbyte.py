
from dagster_airbyte import  airbyte_resource, load_assets_from_airbyte_instance

from .constants import AIRBYTE_CONFIG

airbyte_instance = airbyte_resource.configured(AIRBYTE_CONFIG)

airbyte_assets = load_assets_from_airbyte_instance( airbyte_instance,  key_prefix=["src_postgres"])