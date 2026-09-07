-- ============================================================================
-- FINsight 360 - Exploratory Data Analysis & Financial Baseline Queries
-- Script: sql/01_exploratory_analysis.sql
-- Database: PostgreSQL (finsight360)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. MACRO FINANCIAL KPI SUMMARY
-- Calculates GMV, total transaction volume, and conversion rates across statuses.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_gmv_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'SUCCESS') AS successful_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS'), 2) AS successful_gmv_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'FAILED') AS failed_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'FAILED'), 2) AS revenue_at_risk_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED') AS fraud_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED'), 2) AS fraud_blocked_inr,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'SUCCESS')::NUMERIC / COUNT(*)) * 100, 2) AS success_rate_pct,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'FAILED')::NUMERIC / COUNT(*)) * 100, 2) AS failure_rate_pct,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED')::NUMERIC / COUNT(*)) * 100, 2) AS fraud_rate_pct
FROM fact_transactions;

-- ----------------------------------------------------------------------------
-- 2. PAYMENT CHANNEL PROCESSING PERFORMANCE
-- Evaluates throughput, ticket sizes, and failure rates per payment method.
-- ----------------------------------------------------------------------------
SELECT 
    dpm.payment_method_name,
    dpm.category_type,
    COUNT(ft.transaction_id) AS total_attempts,
    ROUND(SUM(ft.amount), 2) AS total_volume_inr,
    ROUND(AVG(ft.amount), 2) AS avg_ticket_size,
    COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'SUCCESS') AS success_count,
    COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED') AS failed_count,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'SUCCESS')::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS success_rate_pct,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED')::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS failure_rate_pct
FROM fact_transactions ft
JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
GROUP BY dpm.payment_method_name, dpm.category_type
ORDER BY total_volume_inr DESC;

-- ----------------------------------------------------------------------------
-- 3. CUSTOMER SEGMENT SPEND & CONVERSION MATRIX
-- Breakdown of customer segments by GMV contribution and technical friction.
-- ----------------------------------------------------------------------------
SELECT 
    dc.customer_segment,
    COUNT(DISTINCT dc.customer_id) AS total_customers,
    COUNT(ft.transaction_id) AS total_transactions,
    ROUND(SUM(ft.amount), 2) AS total_spend_inr,
    ROUND(AVG(ft.amount), 2) AS avg_txn_size,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED')::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS segment_failure_rate_pct
FROM fact_transactions ft
JOIN dim_customers dc ON ft.customer_id = dc.customer_id
GROUP BY dc.customer_segment
ORDER BY total_spend_inr DESC;
