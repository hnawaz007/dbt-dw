"""
ETL Pipeline: AdventureWorks2019 (SQL Server) → PostgreSQL
One-time full load using SQLAlchemy + pandas
"""

import argparse
import pandas as pd
from sqlalchemy import create_engine, text
import logging
import sys

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Connection strings ─────────────────────────────────────────────────────────
MSSQL_CONN = (
    "mssql+pyodbc://etl:demopass@localhost:1433/AdventureWorks2019"
    "?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
)

PG_CONN = (
    "postgresql+psycopg2://etl:demopass@localhost:5432/adventureworks"
)

# ── Table mapping ──────────────────────────────────────────────────────────────
# Format: (source_schema, source_table, target_pg_table)
TABLE_MAP = [
    # schema            source table                   pg target table
    ("Person",          "Address",                     "address"),
    ("Sales",           "Customer",                    "customer"),
    ("Sales",           "SalesOrderDetail",            "salesorderdetail"),
    ("Sales",           "SalesOrderHeader",            "salesorderheader"),
    ("Sales",           "SalesOrderHeaderSalesReason", "salesorderheadersalesreason"),
    ("Person",          "CountryRegion",               "countryregion"),
    ("dbo",             "vw_person",                    "person"),
    ("Production",      "Product",                     "product"),
    ("Production",      "ProductCategory",             "productcategory"),
    ("Production",      "ProductSubcategory",          "productsubcategory"),
    ("Sales",           "SalesReason",                 "salesreason"),
    ("Sales",           "SalesTerritory",              "salesterritory"),
    ("Person",          "StateProvince",               "stateprovince"),
    ("Sales",           "Store",                       "store"),
    ("Sales",           "SalesOrderHeader",            "salesorderheader"),
    ("Person",          "BusinessEntityAddress",       "businessentityaddress"),
]

PG_SCHEMA = "source"   # target schema in PostgreSQL


# ── Geography column overrides ─────────────────────────────────────────────────
# SQL Server geography/geometry types (ODBC type -151) cannot be read directly.
# Map (schema, table) -> {column: cast_expression} to convert them to WKT text.
GEOGRAPHY_OVERRIDES = {
    ("Person", "Address"): {
        "SpatialLocation": "SpatialLocation.STAsText()"
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_engines():
    log.info("Connecting to SQL Server ...")
    src = create_engine(MSSQL_CONN, fast_executemany=True)
    log.info("Connecting to PostgreSQL ...")
    tgt = create_engine(PG_CONN)
    return src, tgt


def ensure_schema(engine, schema):
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    log.info(f"Schema '{schema}' ready.")


def build_select(engine, schema, table):
    """
    Build a SELECT that casts unsupported geography/geometry columns to WKT text.
    """
    overrides = GEOGRAPHY_OVERRIDES.get((schema, table), {})
    if not overrides:
        return f"SELECT * FROM [{schema}].[{table}]"

    col_query = text("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
        ORDER BY ORDINAL_POSITION
    """)
    with engine.connect() as conn:
        rows = conn.execute(col_query, {"schema": schema, "table": table}).fetchall()

    columns = []
    for (col,) in rows:
        if col in overrides:
            cast_expr = overrides[col]
            columns.append(f"{cast_expr} AS [{col}]")
            log.info(f"  -> Casting geography column [{col}] via STAsText()")
        else:
            columns.append(f"[{col}]")

    col_list = ",\n       ".join(columns)
    return f"SELECT {col_list}\nFROM [{schema}].[{table}]"


def extract(engine, schema, table):
    query = build_select(engine, schema, table)
    log.info(f"  Extracting [{schema}].[{table}] ...")
    df = pd.read_sql(query, engine)
    log.info(f"  -> {len(df):,} rows, {len(df.columns)} columns")
    return df


def sanitize_columns(df):
    """Lowercase column names to play nicely with PostgreSQL."""
    df.columns = [c.lower() for c in df.columns]
    return df


def load(df, engine, schema, table):
    log.info(f"  Loading -> {schema}.{table} ...")
    df.to_sql(
        name=table,
        con=engine,
        schema=schema,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )
    log.info(f"  OK Loaded {len(df):,} rows into {schema}.{table}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run(table_filter=None):
    src_engine, tgt_engine = get_engines()
    ensure_schema(tgt_engine, PG_SCHEMA)

    # Filter TABLE_MAP if --table args were provided (matches pg target name)
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
            df = extract(src_engine, src_schema, src_table)
            df = sanitize_columns(df)
            load(df, tgt_engine, PG_SCHEMA, pg_table)
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
        description="ETL: AdventureWorks2019 (SQL Server) -> PostgreSQL"
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
