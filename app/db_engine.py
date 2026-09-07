import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd

# Check for DuckDB
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

# Global database connection cache
_DB_CONN = None
_DB_TYPE = None

def get_data_dir() -> Path:
    """Resolves data/processed directory from various run contexts."""
    current_dir = Path(__file__).resolve().parent
    candidates = [
        current_dir.parent / "data" / "processed",
        current_dir / "data" / "processed",
        Path("data/processed"),
        Path("../data/processed"),
    ]
    for p in candidates:
        if p.exists() and (p / "fact_transactions.csv").exists():
            return p.resolve()
    # Fallback to root data/processed
    return (current_dir.parent / "data" / "processed").resolve()

def initialize_database():
    """Initializes in-memory database (DuckDB or SQLite) and registers star schema tables."""
    global _DB_CONN, _DB_TYPE
    
    if _DB_CONN is not None:
        return _DB_CONN, _DB_TYPE

    data_dir = get_data_dir()
    tables = [
        "dim_customers",
        "dim_merchants",
        "dim_payment_methods",
        "dim_failure_reasons",
        "fact_transactions"
    ]

    if DUCKDB_AVAILABLE:
        conn = duckdb.connect(database=":memory:", read_only=False)
        for t in tables:
            csv_path = data_dir / f"{t}.csv"
            if csv_path.exists():
                # Register table in DuckDB
                conn.execute(f"CREATE TABLE {t} AS SELECT * FROM read_csv_auto('{csv_path.as_posix()}', header=True);")
            else:
                print(f"[WARNING] CSV missing for table {t} at {csv_path}")
        _DB_CONN = conn
        _DB_TYPE = "DuckDB"
    else:
        # High performance in-memory SQLite fallback
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        for t in tables:
            csv_path = data_dir / f"{t}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df.to_sql(t, conn, if_exists="replace", index=False)
            else:
                print(f"[WARNING] CSV missing for table {t} at {csv_path}")
        _DB_CONN = conn
        _DB_TYPE = "SQLite"

    return _DB_CONN, _DB_TYPE

def run_query(sql_query: str) -> pd.DataFrame:
    """Executes a SQL query against the database and returns a pandas DataFrame."""
    conn, db_type = initialize_database()
    
    # Sanitize query: strip whitespace and trailing semicolons
    cleaned_sql = sql_query.strip()
    if cleaned_sql.endswith(";"):
        cleaned_sql = cleaned_sql[:-1].strip()

    try:
        if db_type == "DuckDB":
            return conn.execute(cleaned_sql).df()
        else:
            return pd.read_sql_query(cleaned_sql, conn)
    except Exception as e:
        raise RuntimeError(f"Query execution error ({db_type}): {e}")

def get_schema_metadata() -> dict:
    """Returns database schema metadata including table names, row counts, and column lists."""
    conn, db_type = initialize_database()
    data_dir = get_data_dir()
    tables = [
        "dim_customers",
        "dim_merchants",
        "dim_payment_methods",
        "dim_failure_reasons",
        "fact_transactions"
    ]
    
    metadata = {"engine": db_type, "tables": {}}
    for t in tables:
        try:
            count_df = run_query(f"SELECT COUNT(*) AS total_rows FROM {t}")
            row_count = int(count_df.iloc[0]["total_rows"])
            sample_df = run_query(f"SELECT * FROM {t} LIMIT 1")
            metadata["tables"][t] = {
                "rows": row_count,
                "columns": list(sample_df.columns),
                "dtypes": {col: str(sample_df[col].dtype) for col in sample_df.columns}
            }
        except Exception:
            metadata["tables"][t] = {"rows": 0, "columns": []}
            
    return metadata

def get_sample_data(table_name: str, limit: int = 5) -> pd.DataFrame:
    """Returns top N sample records from a table."""
    return run_query(f"SELECT * FROM {table_name} LIMIT {int(limit)}")
