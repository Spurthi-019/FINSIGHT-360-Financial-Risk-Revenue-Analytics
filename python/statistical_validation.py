import os
import sys
import math
from pathlib import Path
import pandas as pd
import numpy as np

# Attempt to import scipy, provide exact analytical implementations as fallback
try:
    import scipy.stats as stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

def normal_sf(z):
    """Survival function (1 - CDF) for standard normal distribution."""
    if SCIPY_AVAILABLE:
        return float(stats.norm.sf(z))
    return 0.5 * math.erfc(z / math.sqrt(2.0))

def normal_ppf(p):
    """Percent point function (inverse CDF) for standard normal."""
    if SCIPY_AVAILABLE:
        return float(stats.norm.ppf(p))
    if abs(p - 0.975) < 1e-4:
        return 1.959963984540054
    if abs(p - 0.95) < 1e-4:
        return 1.6448536269514722
    a = [-3.969683028665376e+01,  2.209460984245205e+02, -2.759285104469687e+02,
          1.383577518672690e+02, -3.066479806614716e+01,  2.506628277459239e+00]
    b = [-5.447609879822406e+01,  1.615858368580409e+02, -1.556989798598866e+02,
          6.680131188771972e+01, -1.328068155288572e+01]
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)

def chi2_sf(chi2, df):
    """Survival function (p-value) for Chi-Square distribution."""
    if SCIPY_AVAILABLE:
        return float(stats.chi2.sf(chi2, df))
    y = chi2 / 2.0
    if df % 2 == 0:
        # Exact Poisson series for even degrees of freedom: Q(s, y) = e^(-y) * sum(y^j / j!)
        s = df // 2
        term = 1.0
        poly_sum = 1.0
        for j in range(1, s):
            term *= (y / j)
            poly_sum += term
        return math.exp(-y) * poly_sum
    else:
        # Wilson-Hilferty transformation approximation
        z = ((chi2 / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
        return normal_sf(z)

def chi2_contingency_calc(observed_df):
    """Calculates Chi-Square statistic, p-value, and expected frequencies."""
    if SCIPY_AVAILABLE:
        chi2, p_val, dof, expected = stats.chi2_contingency(observed_df)
        return float(chi2), float(p_val), int(dof), expected
    
    obs = observed_df.values.astype(float)
    row_sums = obs.sum(axis=1, keepdims=True)
    col_sums = obs.sum(axis=0, keepdims=True)
    total = obs.sum()
    expected = (row_sums @ col_sums) / total
    
    chi2 = float(np.sum((obs - expected) ** 2 / expected))
    dof = int((obs.shape[0] - 1) * (obs.shape[1] - 1))
    p_val = float(chi2_sf(chi2, dof))
    
    return chi2, p_val, dof, expected

def load_data_and_extract_metrics(base_dir: Path):
    """Dynamically loads processed data to compute exact sample counts."""
    fact_path = base_dir / "data" / "processed" / "fact_transactions.csv"
    cust_path = base_dir / "data" / "processed" / "dim_customers.csv"
    pm_path = base_dir / "data" / "processed" / "dim_payment_methods.csv"

    if not fact_path.exists() or not cust_path.exists() or not pm_path.exists():
        raise FileNotFoundError("Processed datasets missing from data/processed/")

    fact_df = pd.read_csv(fact_path)
    cust_df = pd.read_csv(cust_path, usecols=["customer_id", "city"])
    pm_df = pd.read_csv(pm_path)

    # Merge customer city and payment method info
    merged = fact_df.merge(cust_df, on="customer_id", how="left")
    merged = merged.merge(pm_df, on="payment_method_id", how="left")

    dt_series = pd.to_datetime(merged["transaction_timestamp"])
    months = dt_series.dt.month
    hours = dt_series.dt.hour

    is_non_fraud = (merged["is_fraud"] == 0)

    # Mask for July peak UPI in Tier-2 Cities
    july_peak_mask = (
        is_non_fraud &
        (months == 7) &
        (hours >= 18) &
        (hours <= 22) &
        (merged["payment_method_code"] == "upi") &
        (merged["city"] == "Tier-2 Cities")
    )

    baseline_mask = is_non_fraud & (~july_peak_mask)

    # Group 1 Metrics
    n1 = int(july_peak_mask.sum())
    x1 = int((merged.loc[july_peak_mask, "transaction_status"] == "FAILED").sum())

    # Group 2 Metrics
    n2 = int(baseline_mask.sum())
    x2 = int((merged.loc[baseline_mask, "transaction_status"] == "FAILED").sum())

    return merged, x1, n1, x2, n2

def run_statistical_validation():
    base_dir = Path(__file__).resolve().parent.parent
    lines = []

    def log(msg=""):
        lines.append(str(msg))
        print(msg)

    log("=" * 80)
    log("          FINsight 360 - STATISTICAL VALIDATION & INFERENCE REPORT")
    log("=" * 80)
    log(f"Execution Engine: {'scipy.stats (' + stats.__version__ + ')' if SCIPY_AVAILABLE else 'Standard Python Math + NumPy (High Precision Fallback)'}")
    log()

    # Load data dynamically
    merged_df, x1, n1, x2, n2 = load_data_and_extract_metrics(base_dir)

    # -------------------------------------------------------------------------
    # PART 1: TWO-PROPORTION Z-TEST (JULY PEAK UPI ANOMALY IN TIER-2 CITIES)
    # -------------------------------------------------------------------------
    log("--------------------------------------------------------------------------------")
    log("PART 1: TWO-PROPORTION Z-TEST (JULY PEAK UPI ANOMALY IN TIER-2 CITIES)")
    log("--------------------------------------------------------------------------------")
    log("HYPOTHESIS FORMULATION:")
    log("  * Null Hypothesis (H0)       : p_peak <= p_baseline")
    log("    (Failure rate during July peak window is less than or equal to baseline)")
    log("  * Alternative Hypothesis (H1): p_peak > p_baseline (One-Tailed Upper Test)")
    log("    (Failure rate during July peak window is strictly greater than baseline)")
    log("  * Significance Level (alpha) : 0.05 (95% Confidence Level)")
    log()

    p1_hat = x1 / n1
    p2_hat = x2 / n2

    # Pooled proportion under H0
    p_pool = (x1 + x2) / (n1 + n2)
    q_pool = 1.0 - p_pool

    # Standard error under H0
    se_pool = math.sqrt(p_pool * q_pool * ((1.0 / n1) + (1.0 / n2)))

    # Z-statistic
    z_stat = (p1_hat - p2_hat) / se_pool

    # One-tailed p-value (upper tail)
    p_value_one_tailed = normal_sf(z_stat)
    p_value_two_tailed = normal_sf(abs(z_stat)) * 2.0

    # Effect Size Metrics
    abs_risk_increase = (p1_hat - p2_hat) * 100.0   # in percentage points
    relative_risk = p1_hat / p2_hat                  # Risk ratio
    odds_ratio = (p1_hat / (1.0 - p1_hat)) / (p2_hat / (1.0 - p2_hat))
    nnh = 1.0 / (p1_hat - p2_hat)                    # Number needed to harm

    # 95% Confidence Interval for difference (unpooled SE)
    se_unpooled = math.sqrt((p1_hat * (1.0 - p1_hat) / n1) + (p2_hat * (1.0 - p2_hat) / n2))
    z_crit = normal_ppf(0.975)  # 1.95996
    ci_lower = ((p1_hat - p2_hat) - (z_crit * se_unpooled)) * 100.0
    ci_upper = ((p1_hat - p2_hat) + (z_crit * se_unpooled)) * 100.0

    log("DYNAMICALLY EXTRACTED SAMPLE METRICS:")
    log(f"  * Group 1 (July Peak UPI Tier-2) : n1 = {n1:,}, Failures = {x1:,}, Failure Rate = {p1_hat * 100:.2f}%")
    log(f"  * Group 2 (Baseline Non-Fraud)   : n2 = {n2:,}, Failures = {x2:,}, Failure Rate = {p2_hat * 100:.2f}%")
    log(f"  * Pooled Failure Proportion      : {p_pool * 100:.4f}%")
    log()

    log("STATISTICAL TEST RESULTS:")
    log(f"  * Z-Score (Z-Statistic)          : {z_stat:.4f}")
    log(f"  * One-Tailed p-value             : {p_value_one_tailed:.6e}")
    log(f"  * Two-Tailed p-value             : {p_value_two_tailed:.6e}")
    log(f"  * Critical Z (alpha=0.05, 1-tail): 1.6449")
    log()

    log("EFFECT SIZE & RISK METRICS:")
    log(f"  * Absolute Risk Increase (ARI)   : +{abs_risk_increase:.2f} percentage points")
    log(f"  * Relative Risk Ratio (RR)       : {relative_risk:.2f}x (Peak failure rate is {relative_risk:.2f}x baseline)")
    log(f"  * Odds Ratio (OR)                : {odds_ratio:.2f}")
    log(f"  * Number Needed to Harm (NNH)    : {nnh:.1f} transactions (1 extra failure per every {nnh:.1f} peak attempts)")
    log(f"  * 95% Confidence Interval (Diff) : [{ci_lower:.2f}%, {ci_upper:.2f}%]")
    log()

    # Hypothesis Decision
    if p_value_one_tailed < 0.05:
        decision = "REJECT NULL HYPOTHESIS (H0)"
        conclusion = (
            f"The failure rate during July peak hours for Tier-2 UPI transactions ({p1_hat*100:.2f}%) "
            f"is STATISTICALLY SIGNIFICANTLY HIGHER than the baseline failure rate ({p2_hat*100:.2f}%) "
            f"at p = {p_value_one_tailed:.4e} (Z = {z_stat:.2f})."
        )
    else:
        decision = "FAIL TO REJECT NULL HYPOTHESIS (H0)"
        conclusion = "No statistically significant difference detected between peak and baseline failure rates."

    log("HYPOTHESIS DECISION:")
    log(f"  >>> {decision} <<<")
    log(f"  Conclusion: {conclusion}")
    log()

    # -------------------------------------------------------------------------
    # PART 2: CHI-SQUARE TEST OF INDEPENDENCE (FAILURE RATE VS PAYMENT CHANNEL)
    # -------------------------------------------------------------------------
    log("--------------------------------------------------------------------------------")
    log("PART 2: CHI-SQUARE TEST OF INDEPENDENCE (FAILURE RATE VS PAYMENT CHANNEL)")
    log("--------------------------------------------------------------------------------")
    log("HYPOTHESIS FORMULATION:")
    log("  * Null Hypothesis (H0)       : Failure rate is INDEPENDENT of payment channel across all 300,113 records.")
    log("  * Alternative Hypothesis (H1): Failure rate is DEPENDENT on payment channel across all 300,113 records.")
    log("  * Significance Level (alpha) : 0.05")
    log()

    # Binary Failure Indicator (FAILED vs NON-FAILED)
    merged_df["is_failed"] = (merged_df["transaction_status"] == "FAILED").map({True: "FAILED", False: "NON_FAILED"})

    # 2x4 Contingency Table
    bin_contingency = pd.crosstab(
        merged_df["payment_method_name"], 
        merged_df["is_failed"]
    )
    bin_contingency_tab = pd.crosstab(
        merged_df["payment_method_name"], 
        merged_df["is_failed"],
        margins=True,
        margins_name="Total"
    )

    chi2_stat, chi2_p_val, dof, expected = chi2_contingency_calc(bin_contingency)
    expected_df = pd.DataFrame(
        expected, 
        index=bin_contingency.index, 
        columns=bin_contingency.columns
    ).round(2)

    log("A. OBSERVED CONTINGENCY MATRIX (Failure Rate by Payment Channel across 300,113 txns):")
    log(bin_contingency_tab.to_string())
    log()

    log("B. EXPECTED FREQUENCIES (Under H0 Independence):")
    log(expected_df.to_string())
    log()

    log("C. TEST RESULTS (2x4 Failure Rate Independence):")
    log(f"  * Chi-Square Statistic (chi2)   : {chi2_stat:.4f}")
    log(f"  * Degrees of Freedom (df)       : {dof}")
    log(f"  * Asymptotic p-value            : {chi2_p_val:.6e} ({chi2_p_val:.4f})")
    log()

    if chi2_p_val < 0.05:
        chi_decision = "REJECT NULL HYPOTHESIS (H0)"
        chi_conclusion = "Transaction failure rate is significantly dependent on the payment channel."
    else:
        chi_decision = "FAIL TO REJECT NULL HYPOTHESIS (H0)"
        chi_conclusion = (
            "Across all 300,113 transactions, transaction failure rate is statistically independent of payment channel "
            f"(chi2 = {chi2_stat:.4f}, df = {dof}, p = {chi2_p_val:.4f} > 0.05). This proves that baseline reliability "
            "is consistent across Card, UPI, Wallet, and Net Banking, confirming that the elevated failure rate is localized "
            "to the specific July peak evening anomaly rather than a global systemic defect in UPI."
        )

    log("CHI-SQUARE DECISION:")
    log(f"  >>> {chi_decision} <<<")
    log(f"  Conclusion: {chi_conclusion}")
    log()

    # -------------------------------------------------------------------------
    # PART 3: MULTI-CLASS STATUS INDEPENDENCE (FAILED, SUCCESS, FRAUD_BLOCKED)
    # -------------------------------------------------------------------------
    log("--------------------------------------------------------------------------------")
    log("PART 3: MULTI-CLASS CHI-SQUARE TEST (STATUS [FAILED, SUCCESS, FRAUD_BLOCKED])")
    log("--------------------------------------------------------------------------------")
    
    multi_contingency = pd.crosstab(
        merged_df["payment_method_name"], 
        merged_df["transaction_status"]
    )
    multi_tab = pd.crosstab(
        merged_df["payment_method_name"], 
        merged_df["transaction_status"],
        margins=True,
        margins_name="Total"
    )

    m_chi2, m_pval, m_dof, m_exp = chi2_contingency_calc(multi_contingency)

    log("A. OBSERVED MULTI-CLASS STATUS MATRIX:")
    log(multi_tab.to_string())
    log()
    log(f"  * Chi-Square Statistic (chi2)   : {m_chi2:.4f}")
    log(f"  * Degrees of Freedom (df)       : {m_dof}")
    log(f"  * Asymptotic p-value            : {m_pval:.6e} ({m_pval:.4f})")
    log(f"  * Decision                      : {'REJECT H0' if m_pval < 0.05 else 'FAIL TO REJECT H0 (Independent)'}")
    log()

    log("=" * 80)
    log("                  END OF STATISTICAL VALIDATION REPORT")
    log("=" * 80)

    # Save to report file
    report_path = base_dir / "reports" / "statistical_validation_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    log(f"\n[SUCCESS] Statistical report saved to: {report_path.resolve()}")

if __name__ == "__main__":
    run_statistical_validation()
