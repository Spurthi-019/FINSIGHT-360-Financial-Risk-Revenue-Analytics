import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from app/ or project root
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SYSTEM_PROMPT = """You are an expert Senior Analytics Engineer and SQL Specialist for FINsight 360.
Your task is to translate natural language user questions into clean, valid, standard SQL queries executable on our dimensional Star Schema.

### DATABASE STAR SCHEMA DEFINITIONS:

1. Table: fact_transactions (300,113 rows)
   - transaction_id (BIGINT, Primary Key)
   - customer_id (INT, Foreign Key -> dim_customers.customer_id)
   - merchant_id (INT, Foreign Key -> dim_merchants.merchant_id)
   - payment_method_id (INT, Foreign Key -> dim_payment_methods.payment_method_id)
   - failure_reason_id (INT, Foreign Key -> dim_failure_reasons.failure_reason_id)
   - transaction_timestamp (TIMESTAMP, format 'YYYY-MM-DD HH:MM:SS')
   - amount (NUMERIC, financial amount in INR)
   - device_type (VARCHAR: 'Mobile', 'Desktop', 'Tablet')
   - gateway (VARCHAR: 'Razorpay', 'PayU', 'Cashfree', 'HDFC Direct', 'Paytm Gateway')
   - risk_score (NUMERIC, range 0.0 to 100.0)
   - transaction_status (VARCHAR: 'SUCCESS', 'FAILED', 'FRAUD_BLOCKED')
   - is_international (INT: 0 or 1)
   - is_fraud (INT: 0 or 1)
   - failed_txn_count_24h (INT)

2. Table: dim_customers (39,983 rows)
   - customer_id (INT, Primary Key)
   - customer_name (VARCHAR: 'Customer_0', 'Customer_1', ...)
   - customer_segment (VARCHAR: 'Retail', 'Premium', 'Corporate', 'SMB')
   - city (VARCHAR: 'Mumbai', 'Bengaluru', 'Delhi NCR', 'Hyderabad', 'Chennai', 'Tier-2 Cities')
   - state (VARCHAR: 'Maharashtra', 'Karnataka', 'Delhi', 'Telangana', 'Tamil Nadu', 'Tier-2 Regions')
   - account_age_days (INT)
   - credit_score_band (INT: 1 to 5)
   - kyc_level (INT: 1 to 3)
   - avg_monthly_spend (NUMERIC)

3. Table: dim_merchants (8,000 rows)
   - merchant_id (INT, Primary Key)
   - merchant_name (VARCHAR: 'Merchant_0', 'Merchant_1', ...)
   - merchant_category (VARCHAR: 'E-commerce', 'Travel & Hospitality', 'Utilities', 'Gaming', 'Food & Dining', 'Financial Services')
   - city (VARCHAR)
   - state (VARCHAR)
   - merchant_risk_score (NUMERIC, range 0.0 to 1.0)

4. Table: dim_payment_methods (4 rows)
   - payment_method_id (INT, Primary Key: 1, 2, 3, 4)
   - payment_method_code (VARCHAR: 'card', 'upi', 'wallet', 'bank_transfer')
   - payment_method_name (VARCHAR: 'Credit/Debit Card', 'UPI Instant Pay', 'Digital Wallet', 'Net Banking Transfer')
   - category_type (VARCHAR: 'Card', 'Instant Pay', 'Prepaid', 'Direct Bank')

5. Table: dim_failure_reasons (7 rows)
   - failure_reason_id (INT, Primary Key: 0 to 6)
   - failure_reason_code (VARCHAR: 'SUCCESS', 'INSUFFICIENT_FUNDS', 'BANK_DECLINED', 'TECHNICAL_ERROR', 'GATEWAY_TIMEOUT', 'AUTHENTICATION_FAILED', 'RISK_BLOCKED')
   - failure_reason_description (VARCHAR)
   - failure_category (VARCHAR: 'None', 'Customer Side', 'Infrastructure', 'Risk & Compliance')

### BUSINESS METRIC RULES & CONSTRAINTS:
1. Return ONLY the raw SQL query. DO NOT include markdown formatting, backticks (```), explanations, or notes.
2. Gross Merchandise Value (GMV) / Total Volume = SUM(amount).
3. Revenue at Risk (Failed Volume) = SUM(amount) WHERE transaction_status = 'FAILED' (or failure_reason_id > 0).
4. Fraud Blocked Volume = SUM(amount) WHERE transaction_status = 'FRAUD_BLOCKED' (or is_fraud = 1).
5. Success Rate % = ROUND((COUNT(CASE WHEN transaction_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*)), 2).
6. Failure Rate % = ROUND((COUNT(CASE WHEN transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*)), 2).
7. When grouping or aggregating, use descriptive column aliases and sort results logically (usually ORDER BY metric DESC).
8. Use standard SQL syntax compatible with DuckDB, SQLite, and PostgreSQL.
"""

def clean_sql_output(raw_text: str) -> str:
    """Strips markdown fences and whitespace from LLM response."""
    cleaned = raw_text.strip()
    # Remove markdown code blocks if present
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()

def rule_based_fallback_sql(question: str) -> str:
    """High-accuracy semantic pattern matcher for instant offline/demo analysis."""
    q = question.lower().strip()

    if any(k in q for k in ["macro", "kpi", "overview", "executive", "gmv", "total volume", "summary"]):
        return """
        SELECT 
            COUNT(*) AS total_transactions,
            ROUND(SUM(amount), 2) AS total_gmv_inr,
            ROUND(SUM(CASE WHEN transaction_status = 'SUCCESS' THEN amount ELSE 0 END), 2) AS successful_volume_inr,
            ROUND(SUM(CASE WHEN transaction_status = 'FAILED' THEN amount ELSE 0 END), 2) AS revenue_at_risk_inr,
            ROUND(SUM(CASE WHEN transaction_status = 'FRAUD_BLOCKED' THEN amount ELSE 0 END), 2) AS fraud_blocked_inr,
            ROUND(COUNT(CASE WHEN transaction_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
            ROUND(COUNT(CASE WHEN transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct,
            ROUND(COUNT(CASE WHEN transaction_status = 'FRAUD_BLOCKED' THEN 1 END) * 100.0 / COUNT(*), 2) AS fraud_rate_pct
        FROM fact_transactions
        """

    if any(k in q for k in ["failure reason", "leakage", "why did transactions fail", "top failures", "failure breakdown"]):
        return """
        SELECT 
            dfr.failure_reason_code,
            dfr.failure_category,
            dfr.failure_reason_description,
            COUNT(ft.transaction_id) AS failed_txn_count,
            ROUND(SUM(ft.amount), 2) AS total_lost_amount_inr,
            ROUND(COUNT(ft.transaction_id) * 100.0 / (SELECT COUNT(*) FROM fact_transactions WHERE failure_reason_id > 0), 2) AS pct_share_failed_count
        FROM fact_transactions ft
        JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
        WHERE ft.failure_reason_id > 0
        GROUP BY dfr.failure_reason_code, dfr.failure_category, dfr.failure_reason_description
        ORDER BY total_lost_amount_inr DESC
        """

    if any(k in q for k in ["gateway", "sla", "razorpay", "payu", "cashfree", "hdfc", "paytm", "acquirer"]):
        return """
        SELECT 
            ft.gateway,
            COUNT(ft.transaction_id) AS total_transactions,
            ROUND(SUM(ft.amount), 2) AS total_volume_inr,
            ROUND(COUNT(CASE WHEN ft.transaction_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
            COUNT(CASE WHEN dfr.failure_reason_code = 'GATEWAY_TIMEOUT' THEN 1 END) AS timeout_count,
            COUNT(CASE WHEN dfr.failure_reason_code = 'TECHNICAL_ERROR' THEN 1 END) AS technical_error_count,
            ROUND(SUM(CASE WHEN ft.transaction_status = 'FAILED' THEN ft.amount ELSE 0 END), 2) AS total_lost_volume_inr
        FROM fact_transactions ft
        JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
        GROUP BY ft.gateway
        ORDER BY total_lost_volume_inr DESC
        """

    if any(k in q for k in ["july", "peak", "tier-2", "tier 2", "evening", "upi anomaly", "hour"]):
        return """
        SELECT 
            CAST(SUBSTR(ft.transaction_timestamp, 12, 2) AS INT) AS hour_of_day,
            COUNT(ft.transaction_id) AS total_attempts,
            COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) AS failed_attempts,
            ROUND(COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct,
            ROUND(SUM(CASE WHEN dfr.failure_reason_code = 'GATEWAY_TIMEOUT' THEN ft.amount ELSE 0 END), 2) AS gateway_timeout_lost_inr
        FROM fact_transactions ft
        JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
        JOIN dim_customers dc ON ft.customer_id = dc.customer_id
        JOIN dim_failure_reasons dfr ON ft.failure_reason_id = dfr.failure_reason_id
        WHERE SUBSTR(ft.transaction_timestamp, 6, 2) = '07'
          AND dpm.payment_method_code = 'upi'
          AND dc.city = 'Tier-2 Cities'
        GROUP BY CAST(SUBSTR(ft.transaction_timestamp, 12, 2) AS INT)
        ORDER BY hour_of_day ASC
        """

    if any(k in q for k in ["merchant", "pareto", "top 5 merchant", "top 10 merchant", "highest loss merchant"]):
        return """
        SELECT 
            dm.merchant_id,
            dm.merchant_name,
            dm.merchant_category,
            dm.city,
            COUNT(ft.transaction_id) AS failed_txn_count,
            ROUND(SUM(ft.amount), 2) AS total_lost_revenue_inr
        FROM fact_transactions ft
        JOIN dim_merchants dm ON ft.merchant_id = dm.merchant_id
        WHERE ft.transaction_status = 'FAILED'
        GROUP BY dm.merchant_id, dm.merchant_name, dm.merchant_category, dm.city
        ORDER BY total_lost_revenue_inr DESC
        LIMIT 10
        """

    if any(k in q for k in ["customer", "churn", "high value", "high-value", "at-risk", "at risk", "segment"]):
        return """
        SELECT 
            dc.customer_id,
            dc.customer_name,
            dc.customer_segment,
            dc.city,
            ROUND(SUM(ft.amount), 2) AS total_attempted_spend_inr,
            COUNT(ft.transaction_id) AS total_attempts,
            COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) AS failed_attempts,
            ROUND(COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct
        FROM fact_transactions ft
        JOIN dim_customers dc ON ft.customer_id = dc.customer_id
        GROUP BY dc.customer_id, dc.customer_name, dc.customer_segment, dc.city
        HAVING SUM(ft.amount) >= 25000 
           AND (COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*)) >= 20.0
        ORDER BY total_attempted_spend_inr DESC
        LIMIT 15
        """

    if any(k in q for k in ["fraud", "nocturnal", "off-hours", "night", "international"]):
        return """
        SELECT 
            CASE 
                WHEN CAST(SUBSTR(ft.transaction_timestamp, 12, 2) AS INT) BETWEEN 0 AND 5 THEN 'Off-Hours (12 AM - 5 AM)'
                ELSE 'Standard Hours (6 AM - 11 PM)'
            END AS time_window,
            COUNT(*) AS total_transactions,
            ROUND(SUM(amount), 2) AS total_volume_inr,
            COUNT(CASE WHEN is_fraud = 1 THEN 1 END) AS fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) AS fraud_volume_inr,
            ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS fraud_rate_pct
        FROM fact_transactions ft
        GROUP BY CASE 
            WHEN CAST(SUBSTR(ft.transaction_timestamp, 12, 2) AS INT) BETWEEN 0 AND 5 THEN 'Off-Hours (12 AM - 5 AM)'
            ELSE 'Standard Hours (6 AM - 11 PM)'
        END
        ORDER BY fraud_rate_pct DESC
        """

    if any(k in q for k in ["payment method", "channel", "upi", "card", "wallet", "net banking"]):
        return """
        SELECT 
            dpm.payment_method_name,
            COUNT(ft.transaction_id) AS total_transactions,
            ROUND(SUM(ft.amount), 2) AS total_volume_inr,
            ROUND(AVG(ft.amount), 2) AS avg_ticket_size,
            ROUND(COUNT(CASE WHEN ft.transaction_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) AS success_rate_pct,
            ROUND(COUNT(CASE WHEN ft.transaction_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*), 2) AS failure_rate_pct
        FROM fact_transactions ft
        JOIN dim_payment_methods dpm ON ft.payment_method_id = dpm.payment_method_id
        GROUP BY dpm.payment_method_name
        ORDER BY total_volume_inr DESC
        """

    # Generic fallback
    return """
    SELECT 
        transaction_status,
        COUNT(*) AS transaction_count,
        ROUND(SUM(amount), 2) AS total_volume_inr,
        ROUND(AVG(amount), 2) AS avg_amount_inr
    FROM fact_transactions
    GROUP BY transaction_status
    ORDER BY total_volume_inr DESC
    """

def generate_sql(user_question: str, api_key: str = None, provider: str = "openai") -> str:
    """Generates SQL query from natural language user question using OpenAI, Gemini, or semantic fallback."""
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    gemini_key = api_key or os.environ.get("GEMINI_API_KEY")

    # 1. Try OpenAI
    if provider.lower() == "openai" and openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.0
            )
            raw_sql = response.choices[0].message.content
            return clean_sql_output(raw_sql)
        except Exception as e:
            print(f"[LLM Helper] OpenAI error: {e}. Trying fallback...")

    # 2. Try Google Gemini
    if (provider.lower() == "gemini" or not openai_key) and gemini_key:
        try:
            # Try new google-genai SDK or google.generativeai
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{SYSTEM_PROMPT}\n\nUser Question: {user_question}"
                )
                return clean_sql_output(response.text)
            except ImportError:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(user_question)
                return clean_sql_output(response.text)
        except Exception as e:
            print(f"[LLM Helper] Gemini error: {e}. Trying fallback...")

    # 3. Use Semantic Rule-Based Matcher
    return rule_based_fallback_sql(user_question).strip()
