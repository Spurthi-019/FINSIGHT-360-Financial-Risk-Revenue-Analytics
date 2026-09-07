-- ============================================================================
-- FINsight 360 - Database Schema DDL (PostgreSQL Star Schema)
-- Script: sql/01_schema_ddl.sql
-- ============================================================================

-- 1. Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS fact_transactions CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_merchants CASCADE;
DROP TABLE IF EXISTS dim_payment_methods CASCADE;
DROP TABLE IF EXISTS dim_failure_reasons CASCADE;

-- 2. Create Dimension: dim_customers
CREATE TABLE dim_customers (
    customer_id         INT PRIMARY KEY,
    customer_name       VARCHAR(100) NOT NULL,
    customer_segment    VARCHAR(50)  NOT NULL,
    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(100) NOT NULL,
    account_age_days    INT          NOT NULL,
    credit_score_band   INT          NOT NULL,
    kyc_level           INT          NOT NULL,
    avg_monthly_spend   NUMERIC(12, 2) NOT NULL
);

-- 3. Create Dimension: dim_merchants
CREATE TABLE dim_merchants (
    merchant_id         INT PRIMARY KEY,
    merchant_name       VARCHAR(100) NOT NULL,
    merchant_category   VARCHAR(100) NOT NULL,
    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(100) NOT NULL,
    merchant_risk_score NUMERIC(6, 4) NOT NULL
);

-- 4. Create Dimension: dim_payment_methods
CREATE TABLE dim_payment_methods (
    payment_method_id   INT PRIMARY KEY,
    payment_method_code VARCHAR(50)  NOT NULL,
    payment_method_name VARCHAR(100) NOT NULL,
    category_type       VARCHAR(50)  NOT NULL
);

-- 5. Create Dimension: dim_failure_reasons
CREATE TABLE dim_failure_reasons (
    failure_reason_id          INT PRIMARY KEY,
    failure_reason_code        VARCHAR(50)  NOT NULL,
    failure_reason_description VARCHAR(255) NOT NULL,
    failure_category           VARCHAR(50)  NOT NULL
);

-- 6. Create Fact Table: fact_transactions
CREATE TABLE fact_transactions (
    transaction_id         BIGINT PRIMARY KEY,
    customer_id            INT NOT NULL REFERENCES dim_customers(customer_id),
    merchant_id            INT NOT NULL REFERENCES dim_merchants(merchant_id),
    payment_method_id      INT NOT NULL REFERENCES dim_payment_methods(payment_method_id),
    failure_reason_id      INT NOT NULL REFERENCES dim_failure_reasons(failure_reason_id),
    transaction_timestamp  TIMESTAMP NOT NULL,
    amount                 NUMERIC(12, 2) NOT NULL,
    device_type            VARCHAR(50),
    gateway                VARCHAR(50),
    risk_score             NUMERIC(5, 1),
    transaction_status     VARCHAR(50) NOT NULL,
    is_international       INT DEFAULT 0,
    is_fraud               INT DEFAULT 0,
    failed_txn_count_24h   INT DEFAULT 0
);

-- 7. Performance & Analytical Indexes on fact_transactions
CREATE INDEX idx_fact_txns_timestamp ON fact_transactions(transaction_timestamp);
CREATE INDEX idx_fact_txns_status ON fact_transactions(transaction_status);
CREATE INDEX idx_fact_txns_cust_merch ON fact_transactions(customer_id, merchant_id);
CREATE INDEX idx_fact_txns_payment_method ON fact_transactions(payment_method_id);
CREATE INDEX idx_fact_txns_failure_reason ON fact_transactions(failure_reason_id);
