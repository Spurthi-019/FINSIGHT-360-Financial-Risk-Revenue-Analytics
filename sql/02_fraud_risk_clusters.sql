-- ============================================================================
-- FINsight 360 - Fraud & Risk Analytics Cluster Queries
-- Script: sql/02_fraud_risk_clusters.sql
-- Database: PostgreSQL (finsight360)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. OFF-HOURS FRAUD SURGE ANALYSIS (12 AM - 5 AM IST vs Daytime)
-- Quantifies the 4.2x elevated risk during nocturnal hours on high-value tickets.
-- ----------------------------------------------------------------------------
WITH hourly_risk AS (
    SELECT 
        EXTRACT(HOUR FROM transaction_timestamp)::INT AS txn_hour,
        CASE 
            WHEN EXTRACT(HOUR FROM transaction_timestamp)::INT BETWEEN 0 AND 5 THEN 'Off-Hours (12 AM - 5 AM)'
            ELSE 'Standard Operating Hours (6 AM - 11 PM)'
        END AS time_window,
        amount,
        is_fraud,
        risk_score
    FROM fact_transactions
)
SELECT 
    time_window,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_volume_inr,
    COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_count,
    ROUND(SUM(amount) FILTER (WHERE is_fraud = 1), 2) AS fraud_volume_inr,
    ROUND((COUNT(*) FILTER (WHERE is_fraud = 1)::NUMERIC / COUNT(*)) * 100, 2) AS fraud_rate_pct,
    ROUND(AVG(risk_score), 1) AS mean_risk_score,
    COUNT(*) FILTER (WHERE is_fraud = 1 AND amount > 5000) AS high_ticket_fraud_count
FROM hourly_risk
GROUP BY time_window
ORDER BY fraud_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- 2. CROSS-BORDER vs DOMESTIC RISK DEVIATION
-- Analyzes risk score profiles and fraud rates on international payment flows.
-- ----------------------------------------------------------------------------
SELECT 
    CASE WHEN ft.is_international = 1 THEN 'International' ELSE 'Domestic' END AS corridor_type,
    COUNT(ft.transaction_id) AS total_transactions,
    ROUND(SUM(ft.amount), 2) AS total_gmv_inr,
    COUNT(ft.transaction_id) FILTER (WHERE ft.is_fraud = 1) AS fraud_txns,
    ROUND(SUM(ft.amount) FILTER (WHERE ft.is_fraud = 1), 2) AS fraud_gmv_inr,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.is_fraud = 1)::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS fraud_rate_pct,
    ROUND(AVG(ft.risk_score), 1) AS avg_post_auth_risk_score
FROM fact_transactions ft
GROUP BY ft.is_international
ORDER BY total_transactions DESC;

-- ----------------------------------------------------------------------------
-- 3. MERCHANT CATEGORY FRAUD CONCENTRATION
-- Identifies industry verticals most vulnerable to post-authorization fraud.
-- ----------------------------------------------------------------------------
SELECT 
    dm.merchant_category,
    COUNT(ft.transaction_id) AS total_attempts,
    COUNT(ft.transaction_id) FILTER (WHERE ft.is_fraud = 1) AS fraud_incidents,
    ROUND(SUM(ft.amount) FILTER (WHERE ft.is_fraud = 1), 2) AS fraud_loss_inr,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.is_fraud = 1)::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS category_fraud_rate_pct
FROM fact_transactions ft
JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
GROUP BY dm.merchant_category
ORDER BY fraud_loss_inr DESC;
