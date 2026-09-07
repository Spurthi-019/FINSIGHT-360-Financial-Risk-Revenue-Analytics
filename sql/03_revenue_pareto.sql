-- ============================================================================
-- FINsight 360 - Revenue Pareto & Infrastructure Loss Concentration
-- Script: sql/03_revenue_pareto.sql
-- Database: PostgreSQL (finsight360)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. MERCHANT REVENUE LOSS PARETO (80/20 RULE)
-- Identifies top tier merchants contributing to 80% of technical loss.
-- ----------------------------------------------------------------------------
WITH merchant_loss_agg AS (
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
ranked_merchants AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) AS rank_pos,
        merchant_id,
        merchant_name,
        merchant_category,
        city,
        failed_txn_count,
        merchant_lost_revenue_inr,
        SUM(merchant_lost_revenue_inr) OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) AS cumulative_loss_inr,
        ROUND(
            (SUM(merchant_lost_revenue_inr) OVER (ORDER BY merchant_lost_revenue_inr DESC, merchant_id) / 
             SUM(merchant_lost_revenue_inr) OVER ()) * 100, 
            2
        ) AS cumulative_loss_pct
    FROM merchant_loss_agg
)
SELECT 
    rank_pos,
    merchant_id,
    merchant_name,
    merchant_category,
    city,
    failed_txn_count,
    merchant_lost_revenue_inr,
    cumulative_loss_inr,
    cumulative_loss_pct
FROM ranked_merchants
WHERE cumulative_loss_pct <= 80.0
ORDER BY rank_pos ASC;

-- ----------------------------------------------------------------------------
-- 2. RECOVERABLE INFRASTRUCTURE GMV (DYNAMIC ROUTING FAILOVER OPPORTUNITY)
-- Isolates technical errors and timeouts that are addressable via multi-gateway failover.
-- ----------------------------------------------------------------------------
SELECT 
    dfr.failure_reason_code,
    dfr.failure_category,
    COUNT(ft.transaction_id) AS recoverable_txn_count,
    ROUND(SUM(ft.amount), 2) AS recoverable_gmv_inr,
    ROUND(
        (SUM(ft.amount)::NUMERIC / (SELECT SUM(amount) FROM fact_transactions WHERE transaction_status = 'FAILED')) * 100,
        2
    ) AS pct_of_failed_volume
FROM fact_transactions ft
JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
WHERE dfr.failure_category = 'Infrastructure'
GROUP BY dfr.failure_reason_code, dfr.failure_category
ORDER BY recoverable_gmv_inr DESC;
