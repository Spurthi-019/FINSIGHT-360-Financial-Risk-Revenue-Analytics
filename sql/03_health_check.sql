-- ============================================================================
-- FINsight 360 - Database Health Check & Analytical Integrity Audit
-- Script: sql/03_health_check.sql
-- ============================================================================

\echo '======================================================================'
\echo 'FINsight 360 - DATABASE HEALTH CHECK & INTEGRITY REPORT'
\echo '======================================================================'

-- ----------------------------------------------------------------------------
-- AUDIT QUERY 1: Total Volume and Count by Transaction Status
-- ----------------------------------------------------------------------------
\echo '----------------------------------------------------------------------'
\echo '1. TRANSACTION VOLUME & REVENUE SUMMARY BY STATUS'
\echo '----------------------------------------------------------------------'

SELECT 
    ft.transaction_status,
    COUNT(*) AS transaction_count,
    ROUND((COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100, 2) AS count_pct,
    ROUND(SUM(ft.amount), 2) AS total_volume_inr,
    ROUND((SUM(ft.amount)::NUMERIC / SUM(SUM(ft.amount)) OVER ()) * 100, 2) AS volume_pct,
    ROUND(AVG(ft.amount), 2) AS avg_ticket_size,
    ROUND(AVG(ft.risk_score), 1) AS avg_risk_score
FROM fact_transactions ft
GROUP BY ft.transaction_status
ORDER BY transaction_count DESC;


-- ----------------------------------------------------------------------------
-- AUDIT QUERY 2: Top 5 Failure Reasons by Revenue Lost
-- ----------------------------------------------------------------------------
\echo '----------------------------------------------------------------------'
\echo '2. TOP 5 FAILURE REASONS BY REVENUE LOST'
\echo '----------------------------------------------------------------------'

SELECT 
    dfr.failure_reason_id,
    dfr.failure_reason_code,
    dfr.failure_category,
    COUNT(ft.transaction_id) AS failed_txns_count,
    ROUND(SUM(ft.amount), 2) AS lost_volume_inr,
    ROUND((SUM(ft.amount)::NUMERIC / SUM(SUM(ft.amount)) OVER ()) * 100, 2) AS pct_of_failed_volume,
    ROUND(AVG(ft.amount), 2) AS avg_lost_ticket_size
FROM fact_transactions ft
JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
WHERE ft.transaction_status IN ('FAILED', 'FRAUD_BLOCKED') 
   OR ft.failure_reason_id > 0
GROUP BY dfr.failure_reason_id, dfr.failure_reason_code, dfr.failure_category
ORDER BY lost_volume_inr DESC
LIMIT 5;


-- ----------------------------------------------------------------------------
-- AUDIT QUERY 3: Foreign Key Integrity Check (Orphan Records Detection)
-- ----------------------------------------------------------------------------
\echo '----------------------------------------------------------------------'
\echo '3. REFERENTIAL INTEGRITY AUDIT (ORPHAN RECORD CHECKS)'
\echo '----------------------------------------------------------------------'

SELECT 
    COUNT(ft.transaction_id) AS total_fact_records,
    COUNT(ft.transaction_id) FILTER (WHERE dc.customer_id IS NULL) AS orphan_customers,
    COUNT(ft.transaction_id) FILTER (WHERE dm.merchant_id IS NULL) AS orphan_merchants,
    COUNT(ft.transaction_id) FILTER (WHERE dpm.payment_method_id IS NULL) AS orphan_payment_methods,
    COUNT(ft.transaction_id) FILTER (WHERE dfr.failure_reason_id IS NULL) AS orphan_failure_reasons,
    CASE 
        WHEN COUNT(ft.transaction_id) FILTER (
            WHERE dc.customer_id IS NULL 
               OR dm.merchant_id IS NULL 
               OR dpm.payment_method_id IS NULL 
               OR dfr.failure_reason_id IS NULL
        ) = 0 THEN 'PASSED (0 Orphan Records)'
        ELSE 'FAILED (Orphans Detected)'
    END AS foreign_key_integrity_status
FROM fact_transactions ft
LEFT JOIN dim_customers dc ON ft.customer_id = dc.customer_id
LEFT JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
LEFT JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
LEFT JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id;
