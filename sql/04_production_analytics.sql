-- ============================================================================
-- FINsight 360 - Production SQL Analytics Suite
-- Script: sql/04_production_analytics.sql
-- Database: PostgreSQL (finsight360)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: EXECUTIVE PERFORMANCE OVERVIEW
-- High-level financial KPIs: GMV, success/failure/fraud breakdowns, and conversion rates.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_gmv_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'SUCCESS') AS successful_txn_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'SUCCESS'), 2) AS successful_volume_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'FAILED') AS failed_txn_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'FAILED'), 2) AS revenue_at_risk_inr,
    COUNT(*) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED') AS fraud_blocked_count,
    ROUND(SUM(amount) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED'), 2) AS fraud_blocked_volume_inr,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'SUCCESS')::NUMERIC / COUNT(*)) * 100, 2) AS overall_success_rate_pct,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'FAILED')::NUMERIC / COUNT(*)) * 100, 2) AS overall_failure_rate_pct,
    ROUND((COUNT(*) FILTER (WHERE transaction_status = 'FRAUD_BLOCKED')::NUMERIC / COUNT(*)) * 100, 2) AS fraud_rate_pct
FROM fact_transactions;


-- ----------------------------------------------------------------------------
-- QUERY 2: FAILURE REASON DECOMPOSITION & REVENUE LEAKAGE
-- Granular breakdown of failure drivers ranked by total financial leakage.
-- ----------------------------------------------------------------------------
SELECT 
    dfr.failure_reason_code,
    dfr.failure_category,
    dfr.failure_reason_description,
    COUNT(ft.transaction_id) AS failed_txn_count,
    ROUND(SUM(ft.amount), 2) AS total_lost_amount_inr,
    ROUND(
        (SUM(ft.amount)::NUMERIC / SUM(SUM(ft.amount)) OVER ()) * 100, 
        2
    ) AS pct_share_lost_volume,
    DENSE_RANK() OVER (ORDER BY SUM(ft.amount) DESC) AS loss_rank
FROM fact_transactions ft
JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
WHERE ft.failure_reason_id > 0
GROUP BY dfr.failure_reason_code, dfr.failure_category, dfr.failure_reason_description
ORDER BY loss_rank ASC;


-- ----------------------------------------------------------------------------
-- QUERY 3: JULY EVENING PEAK-HOUR UPI ANOMALY (DEEP-DIVE)
-- Hourly diagnostic isolating infrastructure bottlenecks in Tier-2 Cities during July peak hours.
-- ----------------------------------------------------------------------------
SELECT 
    EXTRACT(HOUR FROM ft.transaction_timestamp)::INT AS hour_of_day,
    COUNT(ft.transaction_id) AS total_attempts,
    COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED') AS failed_attempts,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED')::NUMERIC / NULLIF(COUNT(ft.transaction_id), 0)) * 100,
        2
    ) AS failure_rate_pct,
    ROUND(
        COALESCE(SUM(ft.amount) FILTER (WHERE dfr.failure_reason_code = 'GATEWAY_TIMEOUT'), 0),
        2
    ) AS gateway_timeout_lost_revenue_inr
FROM fact_transactions ft
JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
JOIN dim_customers dc ON ft.customer_id = dc.customer_id
JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
WHERE EXTRACT(MONTH FROM ft.transaction_timestamp) = 7
  AND dpm.payment_method_code = 'upi'
  AND dc.city = 'Tier-2 Cities'
GROUP BY EXTRACT(HOUR FROM ft.transaction_timestamp)::INT
ORDER BY hour_of_day ASC;


-- ----------------------------------------------------------------------------
-- QUERY 4: PARETO ANALYSIS ON MERCHANT LOSS CONCENTRATION (80/20 RULE)
-- Identification of merchant accounts that accumulate the top 80% of technical loss.
-- ----------------------------------------------------------------------------
WITH merchant_losses AS (
    SELECT 
        dm.merchant_id,
        dm.merchant_name,
        dm.merchant_category,
        dm.city,
        COUNT(ft.transaction_id) AS failed_txn_count,
        ROUND(SUM(ft.amount), 2) AS merchant_lost_revenue_inr
    FROM fact_transactions ft
    JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
    WHERE ft.transaction_status = 'FAILED'
    GROUP BY dm.merchant_id, dm.merchant_name, dm.merchant_category, dm.city
),
cumulative_calc AS (
    SELECT 
        merchant_id,
        merchant_name,
        merchant_category,
        city,
        failed_txn_count,
        merchant_lost_revenue_inr,
        SUM(merchant_lost_revenue_inr) OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) AS running_lost_revenue_inr,
        SUM(merchant_lost_revenue_inr) OVER () AS total_global_loss_inr,
        ROUND(
            (SUM(merchant_lost_revenue_inr) OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) / 
             SUM(merchant_lost_revenue_inr) OVER ()) * 100,
            2
        ) AS cumulative_loss_pct,
        ROW_NUMBER() OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) AS merchant_rank
    FROM merchant_losses
)
SELECT 
    merchant_rank,
    merchant_id,
    merchant_name,
    merchant_category,
    city,
    failed_txn_count,
    merchant_lost_revenue_inr,
    running_lost_revenue_inr,
    cumulative_loss_pct
FROM cumulative_calc
WHERE cumulative_loss_pct <= 80.0
ORDER BY merchant_rank ASC;


-- ----------------------------------------------------------------------------
-- QUERY 5: HIGH-VALUE CUSTOMER CHURN RISK ANALYSIS
-- Identifies premium & high-spend customers experiencing severe failure rates.
-- ----------------------------------------------------------------------------
WITH customer_txn_summary AS (
    SELECT 
        dc.customer_id,
        dc.customer_name,
        dc.customer_segment,
        dc.city,
        dc.avg_monthly_spend,
        COUNT(ft.transaction_id) AS total_attempts,
        COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'SUCCESS') AS successful_txns,
        COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED') AS failed_txns,
        ROUND(SUM(ft.amount), 2) AS total_attempted_spend_inr,
        ROUND(SUM(ft.amount) FILTER (WHERE ft.transaction_status = 'SUCCESS'), 2) AS total_successful_spend_inr,
        ROUND(
            (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'FAILED')::NUMERIC / COUNT(ft.transaction_id)) * 100, 
            2
        ) AS failure_rate_pct
    FROM fact_transactions ft
    JOIN dim_customers dc ON ft.customer_id = dc.customer_id
    GROUP BY dc.customer_id, dc.customer_name, dc.customer_segment, dc.city, dc.avg_monthly_spend
)
SELECT 
    customer_id,
    customer_name,
    customer_segment,
    city,
    total_attempted_spend_inr,
    total_attempts,
    failed_txns,
    failure_rate_pct,
    CASE 
        WHEN total_attempted_spend_inr >= 50000 AND failure_rate_pct >= 30.0 THEN 'Tier 1 - Critical Churn Risk'
        WHEN total_attempted_spend_inr >= 35000 AND failure_rate_pct >= 25.0 THEN 'Tier 2 - Severe Churn Risk'
        ELSE 'Tier 3 - Moderate Churn Risk'
    END AS risk_tier
FROM customer_txn_summary
WHERE total_attempted_spend_inr > 25000 
  AND failure_rate_pct >= 20.0
ORDER BY total_attempted_spend_inr DESC, failure_rate_pct DESC;


-- ----------------------------------------------------------------------------
-- QUERY 6: GATEWAY PERFORMANCE & SLA COMPLIANCE BENCHMARKING
-- Multi-gateway performance matrix evaluating success rates and technical error volumes.
-- ----------------------------------------------------------------------------
SELECT 
    ft.gateway,
    dpm.payment_method_name,
    COUNT(ft.transaction_id) AS total_transactions,
    ROUND(SUM(ft.amount), 2) AS total_processing_volume_inr,
    ROUND(
        (COUNT(ft.transaction_id) FILTER (WHERE ft.transaction_status = 'SUCCESS')::NUMERIC / COUNT(ft.transaction_id)) * 100,
        2
    ) AS success_rate_pct,
    COUNT(ft.transaction_id) FILTER (WHERE dfr.failure_reason_code = 'GATEWAY_TIMEOUT') AS gateway_timeout_count,
    COUNT(ft.transaction_id) FILTER (WHERE dfr.failure_reason_code = 'TECHNICAL_ERROR') AS technical_error_count,
    ROUND(
        COALESCE(SUM(ft.amount) FILTER (WHERE ft.transaction_status = 'FAILED'), 0),
        2
    ) AS total_financial_volume_lost_inr
FROM fact_transactions ft
JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
GROUP BY ft.gateway, dpm.payment_method_name
ORDER BY total_financial_volume_lost_inr DESC;
