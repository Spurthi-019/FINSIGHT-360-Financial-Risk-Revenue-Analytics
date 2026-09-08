import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

# Try importing streamlit for resource caching
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Try importing DuckDB
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False


def get_project_root() -> Path:
    """Dynamically resolves the absolute project root directory."""
    current_dir = Path(__file__).resolve().parent
    if (current_dir.parent / "data").exists() or (current_dir.parent / "requirements.txt").exists():
        return current_dir.parent
    return current_dir


def get_data_dir() -> Path:
    """Resolves data/processed directory from various run contexts."""
    root = get_project_root()
    candidates = [
        root / "data" / "processed",
        root / "data",
        Path(__file__).resolve().parent / "data" / "processed",
        Path("data/processed"),
    ]
    for p in candidates:
        if p.exists() and (p / "fact_transactions.csv").exists():
            return p.resolve()
    return (root / "data" / "processed").resolve()


def generate_synthetic_star_schema() -> dict:
    """Generates realistic synthetic Star Schema DataFrames when CSVs are not present on cloud."""
    np.random.seed(42)
    
    # 1. dim_payment_methods
    payment_methods_data = [
        {"payment_method_id": 1, "payment_method_code": "card", "payment_method_name": "Credit/Debit Card", "category_type": "Card"},
        {"payment_method_id": 2, "payment_method_code": "upi", "payment_method_name": "UPI Instant Pay", "category_type": "Instant Pay"},
        {"payment_method_id": 3, "payment_method_code": "wallet", "payment_method_name": "Digital Wallet", "category_type": "Prepaid"},
        {"payment_method_id": 4, "payment_method_code": "bank_transfer", "payment_method_name": "Net Banking Transfer", "category_type": "Direct Bank"}
    ]
    df_pm = pd.DataFrame(payment_methods_data)

    # 2. dim_failure_reasons
    failure_reasons_data = [
        {"failure_reason_id": 0, "failure_reason_code": "SUCCESS", "failure_reason_description": "Transaction completed successfully", "failure_category": "None"},
        {"failure_reason_id": 1, "failure_reason_code": "INSUFFICIENT_FUNDS", "failure_reason_description": "Customer account balance inadequate", "failure_category": "Customer Side"},
        {"failure_reason_id": 2, "failure_reason_code": "BANK_DECLINED", "failure_reason_description": "Issuing bank declined transaction", "failure_category": "Customer Side"},
        {"failure_reason_id": 3, "failure_reason_code": "TECHNICAL_ERROR", "failure_reason_description": "Processing switch or gateway network error", "failure_category": "Infrastructure"},
        {"failure_reason_id": 4, "failure_reason_code": "GATEWAY_TIMEOUT", "failure_reason_description": "Acquirer response latency exceeded SLA limit", "failure_category": "Infrastructure"},
        {"failure_reason_id": 5, "failure_reason_code": "AUTHENTICATION_FAILED", "failure_reason_description": "OTP or 3D-Secure 2.0 verification failed", "failure_category": "Customer Side"},
        {"failure_reason_id": 6, "failure_reason_code": "RISK_BLOCKED", "failure_reason_description": "Fraud rule engine or anomaly detection trigger", "failure_category": "Risk & Compliance"}
    ]
    df_fr = pd.DataFrame(failure_reasons_data)

    # 3. dim_customers (1,000 sample customers)
    n_cust = 1000
    cities = ["Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Chennai", "Tier-2 Cities"]
    states = ["Maharashtra", "Karnataka", "Delhi", "Telangana", "Tamil Nadu", "Tier-2 Regions"]
    segments = ["Retail", "Premium", "Corporate", "SMB"]
    
    cust_city_idx = np.random.choice(len(cities), n_cust, p=[0.22, 0.20, 0.18, 0.12, 0.10, 0.18])
    df_cust = pd.DataFrame({
        "customer_id": np.arange(1, n_cust + 1),
        "customer_name": [f"Customer_{i}" for i in range(1, n_cust + 1)],
        "customer_segment": np.random.choice(segments, n_cust, p=[0.55, 0.25, 0.08, 0.12]),
        "city": [cities[i] for i in cust_city_idx],
        "state": [states[i] for i in cust_city_idx],
        "account_age_days": np.random.randint(30, 2000, n_cust),
        "credit_score_band": np.random.choice([1, 2, 3, 4, 5], n_cust, p=[0.05, 0.15, 0.40, 0.25, 0.15]),
        "kyc_level": np.random.choice([1, 2, 3], n_cust, p=[0.20, 0.50, 0.30]),
        "avg_monthly_spend": np.round(np.random.exponential(12000, n_cust) + 1500, 2)
    })

    # 4. dim_merchants (200 sample merchants)
    n_merch = 200
    categories = ["E-commerce", "Travel & Hospitality", "Utilities", "Gaming", "Food & Dining", "Financial Services"]
    df_merch = pd.DataFrame({
        "merchant_id": np.arange(1, n_merch + 1),
        "merchant_name": [f"Merchant_{i}" for i in range(1, n_merch + 1)],
        "merchant_category": np.random.choice(categories, n_merch),
        "city": np.random.choice(cities, n_merch),
        "state": np.random.choice(states, n_merch),
        "merchant_risk_score": np.round(np.random.beta(2, 8, n_merch), 3)
    })

    # 5. fact_transactions (15,000 realistic synthetic transactions)
    n_txns = 15000
    gateways = ["Razorpay", "PayU", "Cashfree", "HDFC Direct", "Paytm Gateway"]
    devices = ["Mobile", "Desktop", "Tablet"]
    
    # Status distribution: ~86.6% SUCCESS, ~11.7% FAILED, ~1.7% FRAUD_BLOCKED
    status_choices = ["SUCCESS", "FAILED", "FRAUD_BLOCKED"]
    statuses = np.random.choice(status_choices, n_txns, p=[0.8664, 0.1174, 0.0162])
    
    failure_ids = []
    is_frauds = []
    for st_val in statuses:
        if st_val == "SUCCESS":
            failure_ids.append(0)
            is_frauds.append(0)
        elif st_val == "FRAUD_BLOCKED":
            failure_ids.append(6)
            is_frauds.append(1)
        else:
            # FAILED: reason 1 to 5
            fid = np.random.choice([1, 2, 3, 4, 5], p=[0.35, 0.22, 0.18, 0.15, 0.10])
            failure_ids.append(fid)
            is_frauds.append(0)

    # Timestamps throughout 2026
    start_ts = pd.Timestamp("2026-01-01 00:00:00")
    random_seconds = np.random.randint(0, 240 * 86400, n_txns)
    timestamps = [start_ts + pd.Timedelta(seconds=int(s)) for s in random_seconds]

    # Amounts: lognormal distribution centered around ~₹2,400 with high tickets
    amounts = np.round(np.random.lognormal(mean=7.2, sigma=1.0, size=n_txns), 2)
    amounts = np.clip(amounts, 10.0, 150000.0)

    df_fact = pd.DataFrame({
        "transaction_id": np.arange(10000001, 10000001 + n_txns),
        "customer_id": np.random.choice(df_cust["customer_id"], n_txns),
        "merchant_id": np.random.choice(df_merch["merchant_id"], n_txns),
        "payment_method_id": np.random.choice([1, 2, 3, 4], n_txns, p=[0.38, 0.44, 0.12, 0.06]),
        "failure_reason_id": failure_ids,
        "transaction_timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
        "amount": amounts,
        "device_type": np.random.choice(devices, n_txns, p=[0.72, 0.22, 0.06]),
        "gateway": np.random.choice(gateways, n_txns, p=[0.32, 0.24, 0.18, 0.16, 0.10]),
        "risk_score": np.round(np.random.uniform(5.0, 95.0, n_txns), 1),
        "transaction_status": statuses,
        "is_international": np.random.choice([0, 1], n_txns, p=[0.94, 0.06]),
        "is_fraud": is_frauds,
        "failed_txn_count_24h": np.random.poisson(0.3, n_txns)
    })

    return {
        "dim_payment_methods": df_pm,
        "dim_failure_reasons": df_fr,
        "dim_customers": df_cust,
        "dim_merchants": df_merch,
        "fact_transactions": df_fact
    }


def _create_and_seed_db():
    """Internal core engine initialization function."""
    data_dir = get_data_dir()
    tables = [
        "dim_customers",
        "dim_merchants",
        "dim_payment_methods",
        "dim_failure_reasons",
        "fact_transactions"
    ]

    # Check if local CSV files exist
    all_csvs_exist = all((data_dir / f"{t}.csv").exists() for t in tables)

    if DUCKDB_AVAILABLE:
        conn = duckdb.connect(database=":memory:", read_only=False)
        if all_csvs_exist:
            for t in tables:
                csv_path = (data_dir / f"{t}.csv").as_posix()
                conn.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM read_csv_auto('{csv_path}', header=True);")
        else:
            # Seed synthetic Star Schema in DuckDB
            schema_dfs = generate_synthetic_star_schema()
            for t_name, df_data in schema_dfs.items():
                conn.register(f"temp_{t_name}", df_data)
                conn.execute(f"CREATE OR REPLACE TABLE {t_name} AS SELECT * FROM temp_{t_name};")
                conn.unregister(f"temp_{t_name}")
        return conn, "DuckDB"
    else:
        # SQLite In-memory Fallback
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        if all_csvs_exist:
            for t in tables:
                df = pd.read_csv(data_dir / f"{t}.csv")
                df.to_sql(t, conn, if_exists="replace", index=False)
        else:
            schema_dfs = generate_synthetic_star_schema()
            for t_name, df_data in schema_dfs.items():
                df_data.to_sql(t_name, conn, if_exists="replace", index=False)
        return conn, "SQLite"


# Cached initialization for Streamlit
if HAS_STREAMLIT:
    @st.cache_resource(show_spinner=False)
    def init_db():
        """Initializes and returns cached database connection for Streamlit session."""
        return _create_and_seed_db()
else:
    _STANDALONE_CONN = None
    _STANDALONE_TYPE = None
    def init_db():
        global _STANDALONE_CONN, _STANDALONE_TYPE
        if _STANDALONE_CONN is None:
            _STANDALONE_CONN, _STANDALONE_TYPE = _create_and_seed_db()
        return _STANDALONE_CONN, _STANDALONE_TYPE


def run_query(sql_query: str) -> pd.DataFrame:
    """Executes a SQL query against the seeded Star Schema database and returns a pandas DataFrame."""
    conn, db_type = init_db()

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
    conn, db_type = init_db()
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
