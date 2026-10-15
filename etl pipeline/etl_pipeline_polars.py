"""
ETL Pipeline: AdventureWorks2019 (SQL Server) -> PostgreSQL
Full load using connectorx (extract) + Polars (transform) + ADBC (bulk load)

Same TABLE_MAP contract as etl_pipeline.py (the pandas
version) so it's a drop-in swap for the --table CLI flag and log format
etl_ui.py expects.
"""

import argparse
import logging
import sys

import connectorx as cx
import polars as pl
from adbc_driver_postgresql import dbapi as adbc_pg

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Connection strings ─────────────────────────────────────────────────────────
MSSQL_CONN = (
    "mssql://etl:demopass@localhost:1433/AdventureWorks2019"
    "?encrypt=false&trust_server_certificate=true"
)

PG_CONN = "postgresql://etl:demopass@localhost:5432/adventureworks"

# ── Table mapping ──────────────────────────────────────────────────────────────
# Format: (source_schema, source_table, target_pg_table)
TABLE_MAP = [
    ("Person",          "Address",                     "address"),
    ("Sales",           "Customer",                    "customer"),
    ("Sales",           "SalesOrderDetail",            "salesorderdetail"),
    ("Sales",           "SalesOrderHeader",            "salesorderheader"),
    ("Sales",           "SalesOrderHeaderSalesReason", "salesorderheadersalesreason"),
    ("Person",          "CountryRegion",               "countryregion"),
    ("dbo",             "vw_person",                   "person"),
    ("Production",      "Product",                     "product"),
    ("Production",      "ProductCategory",              "productcategory"),
    ("Production",      "ProductSubcategory",           "productsubcategory"),
    ("Sales",           "SalesReason",                 "salesreason"),
    ("Sales",           "SalesTerritory",               "salesterritory"),
    ("Person",          "StateProvince",                "stateprovince"),
    ("Sales",           "Store",                        "store"),
    ("Person",          "BusinessEntityAddress",        "businessentityaddress"),
]

PG_SCHEMA = "source"   # target schema in PostgreSQL


# ── Unsupported-type column overrides ──────────────────────────────────────────
# connectorx hard-panics (crashes the whole process, not just the one table) on
# SQL Server geography/geometry/xml columns. Map (schema, table) -> {column: cast
# expression} to convert them to a type it can read.
TYPE_OVERRIDES = {
    ("Person", "Address"): {
        "SpatialLocation": "SpatialLocation.STAsText()"
    },
    ("Sales", "Store"): {
        "Demographics": "CAST(Demographics AS NVARCHAR(MAX))"
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def ensure_schema(schema):
    conn = adbc_pg.connect(PG_CONN)
    try:
        cur = conn.cursor()
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        conn.commit()
        cur.close()
    finally:
        conn.close()
    log.info(f"Schema '{schema}' ready.")


def get_columns(schema, table):
    query = (
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}' "
        "ORDER BY ORDINAL_POSITION"
    )
    df = cx.read_sql(MSSQL_CONN, query, return_type="polars")
    return df["COLUMN_NAME"].to_list()


def build_select(schema, table):
    """
    Build a SELECT that casts unsupported geography/geometry columns to WKT text.
    """
    overrides = TYPE_OVERRIDES.get((schema, table), {})
    if not overrides:
        return f"SELECT * FROM [{schema}].[{table}]"

    columns = get_columns(schema, table)
    parts = []
    for col in columns:
        if col in overrides:
            parts.append(f"{overrides[col]} AS [{col}]")
            log.info(f"  -> Casting unsupported column [{col}]: {overrides[col]}")
        else:
            parts.append(f"[{col}]")

    col_list = ",\n       ".join(parts)
    return f"SELECT {col_list}\nFROM [{schema}].[{table}]"


def extract(schema, table):
    query = build_select(schema, table)
    log.info(f"  Extracting [{schema}].[{table}] ...")
    df = cx.read_sql(MSSQL_CONN, query, return_type="polars")
    log.info(f"  -> {df.height:,} rows, {df.width} columns")
    return df


def sanitize_columns(df):
    """Lowercase column names to play nicely with PostgreSQL."""
    df.columns = [c.lower() for c in df.columns]
    return df


def load(df, schema, table):
    log.info(f"  Loading -> {schema}.{table} ...")
    n = df.write_database(
        table_name=f"{schema}.{table}",
        connection=PG_CONN,
        if_table_exists="replace",
        engine="adbc",
    )
    log.info(f"  OK Loaded {n:,} rows into {schema}.{table}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run(table_filter=None):
    ensure_schema(PG_SCHEMA)

    if table_filter:
        normalized = [t.lower() for t in table_filter]
        tables_to_run = [
            entry for entry in TABLE_MAP
            if entry[2].lower() in normalized
        ]
        if not tables_to_run:
            log.error(
                f"No matching tables found for: {table_filter}\n"
                f"Available pg targets: {[e[2] for e in TABLE_MAP]}"
            )
            sys.exit(1)
        log.info(f"Running {len(tables_to_run)} table(s): {[e[2] for e in tables_to_run]}")
    else:
        tables_to_run = TABLE_MAP
        log.info(f"Running all {len(tables_to_run)} tables.")

    success, failed = [], []

    for src_schema, src_table, pg_table in tables_to_run:
        label = f"[{src_schema}].[{src_table}] -> {PG_SCHEMA}.{pg_table}"
        log.info(f"-- {label}")
        try:
            df = extract(src_schema, src_table)
            df = sanitize_columns(df)
            load(df, PG_SCHEMA, pg_table)
            success.append(label)
        except Exception as e:
            log.error(f"  FAILED: {e}")
            failed.append((label, str(e)))

    # ── Summary ────────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info(f"ETL complete.  OK {len(success)} succeeded  FAILED {len(failed)} failed")
    if failed:
        log.warning("Failed tables:")
        for label, err in failed:
            log.warning(f"  - {label}: {err}")
    log.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ETL: AdventureWorks2019 (SQL Server) -> PostgreSQL (connectorx + polars + adbc)"
    )
    parser.add_argument(
        "--table",
        nargs="+",
        metavar="TABLE",
        help=(
            "One or more PostgreSQL target table names to run (case-insensitive). "
            "Omit to run all tables. "
            "Example: --table address vw_person customer"
        ),
    )
    args = parser.parse_args()
    run(table_filter=args.table)
