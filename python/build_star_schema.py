import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def build_star_schema():
    print("=" * 80)
    print("        FINsight 360 - STAR SCHEMA ETL & DERIVATION PIPELINE")
    print("=" * 80)
    print()

    # Set random seed for numpy reproducibility
    RANDOM_SEED = 42
    np.random.seed(RANDOM_SEED)
    rng = np.random.default_rng(RANDOM_SEED)

    # 1. Resolve paths
    base_dir = Path(__file__).resolve().parent.parent
    raw_path = base_dir / "data" / "raw" / "transactions_train.csv"
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw transaction file not found at: {raw_path}")

    print(f"[1/7] Loading raw data from: {raw_path}")
    raw_df = pd.read_csv(raw_path)
    print(f"      Loaded {len(raw_df):,} rows and {len(raw_df.columns)} columns.\n")

    # City-state mapping shared between entities
    city_state_map = {
        "Mumbai": "Maharashtra",
        "Bengaluru": "Karnataka",
        "Delhi NCR": "Delhi",
        "Hyderabad": "Telangana",
        "Chennai": "Tamil Nadu",
        "Tier-2 Cities": "Tier-2 Regions"
    }

    # 2. Build dim_customers.csv
    print("[2/7] Building dim_customers.csv...")
    cust_agg = raw_df.groupby("customer_id", as_index=False).agg({
        "account_age_days": "first",
        "credit_score_band": "first",
        "kyc_level": "first",
        "avg_monthly_spend": "first"
    }).sort_values("customer_id").reset_index(drop=True)

    num_customers = len(cust_agg)
    cust_agg["customer_name"] = "Customer_" + cust_agg["customer_id"].astype(str)

    # Customer Segments: Retail (50%), Premium (20%), Corporate (10%), SMB (20%)
    segment_choices = ["Retail", "Premium", "Corporate", "SMB"]
    segment_weights = [0.50, 0.20, 0.10, 0.20]
    cust_agg["customer_segment"] = rng.choice(segment_choices, size=num_customers, p=segment_weights)

    # City: Mumbai (25%), Bengaluru (25%), Delhi NCR (20%), Hyderabad (12%), Chennai (8%), Tier-2 Cities (10%)
    city_choices = ["Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Chennai", "Tier-2 Cities"]
    city_weights = [0.25, 0.25, 0.20, 0.12, 0.08, 0.10]
    cust_agg["city"] = rng.choice(city_choices, size=num_customers, p=city_weights)
    cust_agg["state"] = cust_agg["city"].map(city_state_map)
    cust_agg["avg_monthly_spend"] = cust_agg["avg_monthly_spend"].round(2)

    cust_cols = [
        "customer_id", "customer_name", "customer_segment", 
        "city", "state", "account_age_days", 
        "credit_score_band", "kyc_level", "avg_monthly_spend"
    ]
    dim_customers = cust_agg[cust_cols]
    cust_out = processed_dir / "dim_customers.csv"
    dim_customers.to_csv(cust_out, index=False)
    print(f"      Saved {len(dim_customers):,} customers to {cust_out}\n")

    # 3. Build dim_merchants.csv
    print("[3/7] Building dim_merchants.csv...")
    merch_agg = raw_df.groupby("merchant_id", as_index=False).agg({
        "merchant_risk_score": "first"
    }).sort_values("merchant_id").reset_index(drop=True)

    num_merchants = len(merch_agg)
    merch_agg["merchant_name"] = "Merchant_" + merch_agg["merchant_id"].astype(str)

    # Merchant Category: Equal probability across 6 categories
    category_choices = [
        "E-commerce", "Travel & Hospitality", "Utilities", 
        "Gaming", "Food & Dining", "Financial Services"
    ]
    merch_agg["merchant_category"] = rng.choice(category_choices, size=num_merchants)

    # Merchant City: Equal probability across 5 cities
    merch_city_choices = ["Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Chennai"]
    merch_agg["city"] = rng.choice(merch_city_choices, size=num_merchants)
    merch_agg["state"] = merch_agg["city"].map(city_state_map)
    merch_agg["merchant_risk_score"] = merch_agg["merchant_risk_score"].round(4)

    merch_cols = ["merchant_id", "merchant_name", "merchant_category", "city", "state", "merchant_risk_score"]
    dim_merchants = merch_agg[merch_cols]
    merch_out = processed_dir / "dim_merchants.csv"
    dim_merchants.to_csv(merch_out, index=False)
    print(f"      Saved {len(dim_merchants):,} merchants to {merch_out}\n")

    # 4. Build dim_payment_methods.csv
    print("[4/7] Building dim_payment_methods.csv...")
    payment_methods_data = [
        {"payment_method_id": 1, "payment_method_code": "card", "payment_method_name": "Credit/Debit Card", "category_type": "Card"},
        {"payment_method_id": 2, "payment_method_code": "upi", "payment_method_name": "UPI Instant Pay", "category_type": "Instant Pay"},
        {"payment_method_id": 3, "payment_method_code": "wallet", "payment_method_name": "Digital Wallet", "category_type": "Prepaid"},
        {"payment_method_id": 4, "payment_method_code": "bank_transfer", "payment_method_name": "Net Banking Transfer", "category_type": "Direct Bank"}
    ]
    dim_payment_methods = pd.DataFrame(payment_methods_data)
    pm_out = processed_dir / "dim_payment_methods.csv"
    dim_payment_methods.to_csv(pm_out, index=False)
    print(f"      Saved {len(dim_payment_methods)} payment methods to {pm_out}\n")

    # 5. Build dim_failure_reasons.csv
    print("[5/7] Building dim_failure_reasons.csv...")
    failure_reasons_data = [
        {"failure_reason_id": 0, "failure_reason_code": "SUCCESS", "failure_reason_description": "Transaction Successful", "failure_category": "None"},
        {"failure_reason_id": 1, "failure_reason_code": "INSUFFICIENT_FUNDS", "failure_reason_description": "Insufficient Customer Account Balance", "failure_category": "Customer Side"},
        {"failure_reason_id": 2, "failure_reason_code": "BANK_DECLINED", "failure_reason_description": "Declined by Issuing Bank", "failure_category": "Customer Side"},
        {"failure_reason_id": 3, "failure_reason_code": "TECHNICAL_ERROR", "failure_reason_description": "Gateway/Switch Technical Exception", "failure_category": "Infrastructure"},
        {"failure_reason_id": 4, "failure_reason_code": "GATEWAY_TIMEOUT", "failure_reason_description": "Acquirer Latency Timeout", "failure_category": "Infrastructure"},
        {"failure_reason_id": 5, "failure_reason_code": "AUTHENTICATION_FAILED", "failure_reason_description": "OTP / 3DS Auth Failed", "failure_category": "Risk & Compliance"},
        {"failure_reason_id": 6, "failure_reason_code": "RISK_BLOCKED", "failure_reason_description": "Blocked by Fraud Risk Engine", "failure_category": "Risk & Compliance"}
    ]
    dim_failure_reasons = pd.DataFrame(failure_reasons_data)
    fr_out = processed_dir / "dim_failure_reasons.csv"
    dim_failure_reasons.to_csv(fr_out, index=False)
    print(f"      Saved {len(dim_failure_reasons)} failure reasons to {fr_out}\n")

    # 6. Build fact_transactions.csv
    print("[6/7] Building fact_transactions.csv...")
    fact_df = raw_df.copy()

    # Map payment_method_id
    channel_map = {"card": 1, "upi": 2, "wallet": 3, "bank_transfer": 4}
    fact_df["payment_method_id"] = fact_df["payment_channel"].map(channel_map)

    # Format timestamp as YYYY-MM-DD HH:MM:SS
    dt_series = pd.to_datetime(fact_df["transaction_time"])
    fact_df["transaction_timestamp"] = dt_series.dt.strftime("%Y-%m-%d %H:%M:%S")

    # Rename & round amount
    fact_df["amount"] = fact_df["transaction_amount"].round(2)

    # Capitalize device_type
    fact_df["device_type"] = fact_df["device_type"].astype(str).str.capitalize()

    # Assign gateway
    gateway_choices = ["Razorpay", "PayU", "Cashfree", "HDFC Direct", "Paytm Gateway"]
    gateway_weights = [0.35, 0.25, 0.15, 0.15, 0.10]
    fact_df["gateway"] = rng.choice(gateway_choices, size=len(fact_df), p=gateway_weights)

    # Scale risk score (0-1 -> 0.0-100.0)
    fact_df["risk_score"] = (fact_df["post_auth_risk_score"] * 100.0).round(1)

    # Map customer city for conditional failure simulation
    cust_city_lookup = dim_customers.set_index("customer_id")["city"]
    customer_cities = fact_df["customer_id"].map(cust_city_lookup)

    months = dt_series.dt.month
    hours = dt_series.dt.hour
    is_fraud_mask = (fact_df["is_fraud"] == 1)

    # Condition: Month == 7 (July) AND Hour between 18 and 22 AND payment_channel == 'upi' AND Customer City == 'Tier-2 Cities'
    july_upi_tier2_mask = (
        (~is_fraud_mask) & 
        (months == 7) & 
        (hours >= 18) & 
        (hours <= 22) & 
        (fact_df["payment_channel"] == "upi") & 
        (customer_cities == "Tier-2 Cities")
    )

    baseline_mask = (~is_fraud_mask) & (~july_upi_tier2_mask)

    # Pre-allocate status and failure_reason_id
    status_arr = np.empty(len(fact_df), dtype=object)
    reason_arr = np.zeros(len(fact_df), dtype=np.int64)

    # 1) Fraud Blocked
    status_arr[is_fraud_mask] = "FRAUD_BLOCKED"
    reason_arr[is_fraud_mask] = 6

    # 2) July Peak UPI Tier-2: 35% FAILED (reason 4 GATEWAY_TIMEOUT), 65% SUCCESS (reason 0)
    num_july_tier2 = int(july_upi_tier2_mask.sum())
    if num_july_tier2 > 0:
        july_random_draw = rng.random(size=num_july_tier2)
        july_failed = july_random_draw < 0.35
        
        july_status = np.where(july_failed, "FAILED", "SUCCESS")
        july_reasons = np.where(july_failed, 4, 0)
        
        status_arr[july_upi_tier2_mask] = july_status
        reason_arr[july_upi_tier2_mask] = july_reasons

    # 3) Baseline: 88% SUCCESS, 12% FAILED (reasons 1,2,3,4,5 with [0.35, 0.25, 0.18, 0.12, 0.10])
    num_baseline = int(baseline_mask.sum())
    if num_baseline > 0:
        base_random_draw = rng.random(size=num_baseline)
        base_failed = base_random_draw >= 0.88  # 12% failed
        
        base_status = np.where(base_failed, "FAILED", "SUCCESS")
        
        # Reasons for failed baseline transactions
        failure_code_choices = [1, 2, 3, 4, 5]
        failure_code_weights = [0.35, 0.25, 0.18, 0.12, 0.10]
        
        num_base_failed = int(base_failed.sum())
        sampled_reasons = rng.choice(failure_code_choices, size=num_base_failed, p=failure_code_weights)
        
        base_reasons = np.zeros(num_baseline, dtype=np.int64)
        base_reasons[base_failed] = sampled_reasons
        
        status_arr[baseline_mask] = base_status
        reason_arr[baseline_mask] = base_reasons

    fact_df["transaction_status"] = status_arr
    fact_df["failure_reason_id"] = reason_arr

    # Select and order final fact columns matching specification
    fact_cols = [
        "transaction_id",
        "customer_id",
        "merchant_id",
        "payment_method_id",
        "failure_reason_id",
        "transaction_timestamp",
        "amount",
        "device_type",
        "gateway",
        "risk_score",
        "transaction_status",
        "is_international",
        "is_fraud",
        "failed_txn_count_24h"
    ]
    fact_transactions = fact_df[fact_cols]
    fact_out = processed_dir / "fact_transactions.csv"
    fact_transactions.to_csv(fact_out, index=False)
    print(f"      Saved {len(fact_transactions):,} fact records to {fact_out}\n")

    # 7. Execution & Verification Report
    print("[7/7] VERIFICATION & INTEGRITY AUDIT")
    print("-" * 80)
    print("A. TABLE ROW COUNTS:")
    print(f"   - dim_customers.csv        : {len(dim_customers):>8,} rows")
    print(f"   - dim_merchants.csv        : {len(dim_merchants):>8,} rows")
    print(f"   - dim_payment_methods.csv  : {len(dim_payment_methods):>8,} rows")
    print(f"   - dim_failure_reasons.csv  : {len(dim_failure_reasons):>8,} rows")
    print(f"   - fact_transactions.csv    : {len(fact_transactions):>8,} rows")
    print()

    print("B. TRANSACTION STATUS DISTRIBUTION (fact_transactions):")
    status_counts = fact_transactions["transaction_status"].value_counts()
    for st, cnt in status_counts.items():
        pct = (cnt / len(fact_transactions)) * 100
        print(f"   - {st:<16}: {cnt:>8,} ({pct:>5.2f}%)")
    print()

    print("C. FAILURE REASON ID DISTRIBUTION (fact_transactions):")
    reason_lookup = dim_failure_reasons.set_index("failure_reason_id")["failure_reason_code"].to_dict()
    reason_counts = fact_transactions["failure_reason_id"].value_counts().sort_index()
    for rid, cnt in reason_counts.items():
        pct = (cnt / len(fact_transactions)) * 100
        code = reason_lookup.get(rid, "UNKNOWN")
        print(f"   - ID {rid} ({code:<22}): {cnt:>8,} ({pct:>5.2f}%)")
    print()

    print("D. SPECIFIC SCENARIO VERIFICATION (July Peak UPI in Tier-2 Cities vs Overall Baseline):")
    july_tier2_txns = fact_transactions[july_upi_tier2_mask]
    july_tier2_failed = (july_tier2_txns["transaction_status"] == "FAILED").sum()
    july_tier2_total = len(july_tier2_txns)
    july_tier2_fail_rate = (july_tier2_failed / july_tier2_total * 100) if july_tier2_total > 0 else 0.0

    baseline_txns = fact_transactions[baseline_mask]
    baseline_failed = (baseline_txns["transaction_status"] == "FAILED").sum()
    baseline_total = len(baseline_txns)
    baseline_fail_rate = (baseline_failed / baseline_total * 100) if baseline_total > 0 else 0.0

    non_fraud_txns = fact_transactions[~is_fraud_mask]
    non_fraud_failed = (non_fraud_txns["transaction_status"] == "FAILED").sum()
    non_fraud_fail_rate = (non_fraud_failed / len(non_fraud_txns) * 100)

    print(f"   * July Peak UPI Tier-2 Txns   : {july_tier2_total:,} total | {july_tier2_failed:,} failed ({july_tier2_fail_rate:.2f}% failure rate)")
    print(f"   * Baseline Non-Fraud Txns     : {baseline_total:,} total | {baseline_failed:,} failed ({baseline_fail_rate:.2f}% failure rate)")
    print(f"   * Overall Non-Fraud Fail Rate : {non_fraud_fail_rate:.2f}%")
    print()
    print("=" * 80)
    print("           STAR SCHEMA ETL PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    build_star_schema()
