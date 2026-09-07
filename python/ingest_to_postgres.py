import os
import sys
import time
from pathlib import Path

# Dependency check
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("\n[ERROR] Missing required PostgreSQL driver 'psycopg2'.")
    print("Please install dependencies by running:")
    print("    pip install psycopg2-binary sqlalchemy pandas\n")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("\n[ERROR] Missing required library 'pandas'.")
    print("Please install dependencies by running:")
    print("    pip install pandas\n")
    sys.exit(1)

# Default DB Connection Parameters
DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "finsight360"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "Spurthi@123"),
}

def get_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent

def ensure_database_exists(config: dict):
    """Checks if the target database exists; if not, connects to 'postgres' db and creates it."""
    target_db = config["dbname"]
    admin_config = config.copy()
    admin_config["dbname"] = "postgres"

    print(f"[*] Checking PostgreSQL connection at {config['host']}:{config['port']} (user: {config['user']})...")
    try:
        conn = psycopg2.connect(**admin_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
            exists = cur.fetchone()
            if not exists:
                print(f"[*] Database '{target_db}' does not exist. Creating database '{target_db}'...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
                print(f"[+] Database '{target_db}' created successfully.")
            else:
                print(f"[+] Database '{target_db}' exists.")
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Could not connect to PostgreSQL server.")
        print(f"Details: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Verify that PostgreSQL server is running.")
        print(f"  2. Confirm credentials: Host={config['host']}, Port={config['port']}, User={config['user']}")
        print("  3. Set environment variables PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE to override defaults.")
        sys.exit(1)

def execute_schema_ddl(conn, ddl_path: Path):
    """Executes the DDL script to reset and create tables and indexes."""
    if not ddl_path.exists():
        raise FileNotFoundError(f"DDL script not found at {ddl_path}")

    print(f"[*] Executing DDL script: {ddl_path.name}...")
    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl_sql = f.read()

    with conn.cursor() as cur:
        cur.execute(ddl_sql)
    conn.commit()
    print("[+] Database schema created successfully (all tables, constraints, and indexes built).")

def ingest_tables(conn, base_dir: Path):
    """Ingests CSV files in strict star schema dependency order using fast COPY STDIN."""
    processed_dir = base_dir / "data" / "processed"
    
    ingestion_plan = [
        ("dim_customers", processed_dir / "dim_customers.csv"),
        ("dim_merchants", processed_dir / "dim_merchants.csv"),
        ("dim_payment_methods", processed_dir / "dim_payment_methods.csv"),
        ("dim_failure_reasons", processed_dir / "dim_failure_reasons.csv"),
        ("fact_transactions", processed_dir / "fact_transactions.csv"),
    ]

    csv_counts = {}
    print("\n[*] Starting bulk data ingestion into PostgreSQL...")
    print("-" * 80)

    for table_name, csv_path in ingestion_plan:
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Count CSV rows (excluding header)
        start_time = time.time()
        print(f"  -> Ingesting {table_name:<22} from {csv_path.name}...", end=" ", flush=True)

        with open(csv_path, "r", encoding="utf-8") as f:
            # First line header count check
            line_count = sum(1 for _ in f) - 1
            csv_counts[table_name] = line_count

        with open(csv_path, "r", encoding="utf-8") as f:
            with conn.cursor() as cur:
                copy_query = f"COPY {table_name} FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',')"
                cur.copy_expert(copy_query, f)
        
        conn.commit()
        elapsed = time.time() - start_time
        print(f"Done! Ingested {line_count:,} rows in {elapsed:.2f}s")

    return csv_counts

def run_post_ingestion_audit(conn, csv_counts: dict):
    """Validates row counts between CSVs and DB tables, then checks foreign key integrity."""
    print("\n" + "=" * 80)
    print("                    POST-INGESTION VALIDATION AUDIT")
    print("=" * 80)

    # 1. Row count comparison
    tables = [
        "dim_customers",
        "dim_merchants",
        "dim_payment_methods",
        "dim_failure_reasons",
        "fact_transactions"
    ]

    print(f"{'Table Name':<25} {'CSV Rows':<15} {'Postgres Rows':<15} {'Status':<10}")
    print("-" * 70)

    all_matched = True
    with conn.cursor() as cur:
        for t in tables:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(t)))
            db_row_count = cur.fetchone()[0]
            csv_row_count = csv_counts.get(t, 0)
            
            is_match = (db_row_count == csv_row_count)
            status = "MATCH (OK)" if is_match else "MISMATCH"
            if not is_match:
                all_matched = False
            print(f"{t:<25} {csv_row_count:<15,} {db_row_count:<15,} {status:<10}")

    print("-" * 70)
    if all_matched:
        print("[+] Row count audit PASSED: All 5 tables match 100% with processed CSV files.")
    else:
        print("[!] Row count audit FAILED: Row count mismatches detected.")

    # 2. Foreign Key Integrity Check
    print("\n[*] Running Foreign Key Integrity Audit (Orphan Records Check)...")
    fk_check_sql = """
    SELECT 
        COUNT(ft.transaction_id) AS total_fact_records,
        COUNT(ft.transaction_id) FILTER (WHERE dc.customer_id IS NULL) AS orphan_customers,
        COUNT(ft.transaction_id) FILTER (WHERE dm.merchant_id IS NULL) AS orphan_merchants,
        COUNT(ft.transaction_id) FILTER (WHERE dpm.payment_method_id IS NULL) AS orphan_payment_methods,
        COUNT(ft.transaction_id) FILTER (WHERE dfr.failure_reason_id IS NULL) AS orphan_failure_reasons
    FROM fact_transactions ft
    LEFT JOIN dim_customers dc ON ft.customer_id = dc.customer_id
    LEFT JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
    LEFT JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
    LEFT JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id;
    """

    with conn.cursor() as cur:
        cur.execute(fk_check_sql)
        row = cur.fetchone()
        total_facts, orph_cust, orph_merch, orph_pm, orph_fr = row

    print(f"  - Total Transactions Verified : {total_facts:,}")
    print(f"  - Orphan Customer References  : {orph_cust:,}")
    print(f"  - Orphan Merchant References  : {orph_merch:,}")
    print(f"  - Orphan Payment Method Refs  : {orph_pm:,}")
    print(f"  - Orphan Failure Reason Refs  : {orph_fr:,}")

    total_orphans = orph_cust + orph_merch + orph_pm + orph_fr
    if total_orphans == 0:
        print("\n[+] Referential Integrity Audit PASSED: 0 Orphan records found.")
    else:
        print(f"\n[!] Referential Integrity Audit FAILED: {total_orphans} orphan records detected.")

    print("=" * 80)
    print("            DATABASE INGESTION & AUDIT COMPLETED SUCCESSFULLY")
    print("=" * 80)

def main():
    base_dir = get_base_dir()
    ddl_path = base_dir / "sql" / "01_schema_ddl.sql"

    print("=" * 80)
    print("        FINsight 360 - POSTGRESQL DATABASE INGESTION PIPELINE")
    print("=" * 80)

    # Step 1: Ensure database exists
    ensure_database_exists(DB_CONFIG)

    # Step 2: Connect to target database
    print(f"[*] Connecting to database '{DB_CONFIG['dbname']}'...")
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Step 3: Run DDL schema setup
        execute_schema_ddl(conn, ddl_path)

        # Step 4: Ingest 5 tables via fast bulk copy
        csv_counts = ingest_tables(conn, base_dir)

        # Step 5: Post-ingestion audit
        run_post_ingestion_audit(conn, csv_counts)

    finally:
        conn.close()
        print("\n[*] Database connection closed.")

if __name__ == "__main__":
    main()
