-- ============================================================================
-- FINsight 360 - Bulk Data Ingestion Script (PostgreSQL \copy)
-- Script: sql/02_bulk_load.sql
-- ============================================================================

-- Execute from workspace root using: psql -U <user> -d <database> -f sql/02_bulk_load.sql

\echo '----------------------------------------------------------------------'
\echo 'Starting bulk load into FINsight 360 Star Schema tables...'
\echo '----------------------------------------------------------------------'

-- 1. Ingest dim_customers
\echo 'Loading dim_customers...'
\copy dim_customers FROM 'data/processed/dim_customers.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- 2. Ingest dim_merchants
\echo 'Loading dim_merchants...'
\copy dim_merchants FROM 'data/processed/dim_merchants.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- 3. Ingest dim_payment_methods
\echo 'Loading dim_payment_methods...'
\copy dim_payment_methods FROM 'data/processed/dim_payment_methods.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- 4. Ingest dim_failure_reasons
\echo 'Loading dim_failure_reasons...'
\copy dim_failure_reasons FROM 'data/processed/dim_failure_reasons.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- 5. Ingest fact_transactions
\echo 'Loading fact_transactions...'
\copy fact_transactions FROM 'data/processed/fact_transactions.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

\echo '----------------------------------------------------------------------'
\echo 'Bulk load complete. Validating row counts across all 5 tables:'
\echo '----------------------------------------------------------------------'

-- Record count validation query
SELECT 'dim_customers' AS table_name, COUNT(*) AS loaded_rows FROM dim_customers
UNION ALL
SELECT 'dim_merchants' AS table_name, COUNT(*) AS loaded_rows FROM dim_merchants
UNION ALL
SELECT 'dim_payment_methods' AS table_name, COUNT(*) AS loaded_rows FROM dim_payment_methods
UNION ALL
SELECT 'dim_failure_reasons' AS table_name, COUNT(*) AS loaded_rows FROM dim_failure_reasons
UNION ALL
SELECT 'fact_transactions' AS table_name, COUNT(*) AS loaded_rows FROM fact_transactions;
