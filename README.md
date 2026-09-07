# 💳 FINsight 360 – Enterprise Financial Risk & Revenue Analytics

[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DAX](https://img.shields.io/badge/DAX-Measures-005BA1)](https://learn.microsoft.com/en-us/dax/)
[![SQL](https://img.shields.io/badge/SQL-Analytics-CC292B)](https://www.postgresql.org/docs/)

> **FINsight 360** is an end-to-end, enterprise-grade financial analytics and fraud intelligence platform. It ingests 300,000+ multi-channel transaction records into an optimized PostgreSQL Star Schema, executes advanced statistical hypothesis testing, and delivers an executive Power BI intelligence suite identifying **₹84.27M in revenue at risk** and **₹25.42M in recoverable GMV**.

---

## 📥 Power BI Report Download

Download the complete interactive Power BI Desktop report (`.pbix`) directly from this repository:

👉 **[📥 Download FINSIGHT_360_Financial_Risk_Analytics.pbix](./FINSIGHT_360_Financial_Risk_Analytics.pbix)**

*To view and interact with the data model, KPIs, and dashboards, open this file in [Microsoft Power BI Desktop](https://powerbi.microsoft.com/desktop/).*

---

## 🔍 Executive Summary & Core Financial Findings

| Metric | Measured Value | Business Impact |
| :--- | :---: | :--- |
| **Total Gross Merchandise Value (GMV)** | **₹720.91M** (300,113 Txns) | Macro processing volume across all channels & gateways. |
| **Successful Settlement Volume** | **₹625.40M** (86.64%) | Baseline clean transaction processing conversion. |
| **Total Revenue at Risk (Failed)** | **₹84.27M** (35,232 Txns) | Total financial leakage across infrastructure & customer declines. |
| **Recoverable Baseline GMV** | **₹25.42M** (10,607 Txns) | **~30.2% of failed volume** addressable via dynamic multi-gateway failover routing. |
| **High-Value Account Exposure** | **1,735 Customers** (₹82.41M Spend) | High-spend accounts (> ₹25k spend) facing severe failure rates ($\ge 20\%$). |
| **Off-Hours Fraud Surge** | **4.2x Escalation** (12 AM - 5 AM IST) | Heightened post-auth fraud frequency on transactions exceeding ₹5,000. |

---

## 🏛️ Architecture & Data Modeling (Star Schema)

The underlying PostgreSQL database implements a normalized Star Schema designed for high-performance OLAP analytical querying:

```
                  +-----------------------------------+
                  |           dim_customers           |
                  +-----------------------------------+
                  | PK  customer_id (INT)             |
                  |     customer_name (VARCHAR)       |
                  |     customer_segment (VARCHAR)    |
                  |     city, state (VARCHAR)         |
                  |     avg_monthly_spend (NUMERIC)   |
                  +-----------------+-----------------+
                                    | 1
                                    |
                                    | N
+-----------------------------+     |     +-----------------------------+
|        dim_merchants        |     |     |     dim_payment_methods     |
+-----------------------------+     |     +-----------------------------+
| PK  merchant_id (INT)       |     |     | PK  payment_method_id (INT) |
|     merchant_name (VARCHAR) |     |     |     payment_method_code     |
|     merchant_category       |     |     |     payment_method_name     |
|     city, state             +--+  |  +--+     category_type           |
+-----------------------------+  |  |  |  +-----------------------------+
                                 |  |  |
                               N |  |  | N
                  +--------------+--+--+--------------+
                  |             fact_transactions     |
                  +-----------------------------------+
                  | PK  transaction_id (BIGINT)       |
                  | FK  customer_id (INT)             |
                  | FK  merchant_id (INT)             |
                  | FK  payment_method_id (INT)       |
                  | FK  failure_reason_id (INT)       |
                  |     transaction_timestamp (TS)    |
                  |     amount (NUMERIC 12,2)         |
                  |     device_type, gateway          |
                  |     risk_score (NUMERIC 5,1)      |
                  |     transaction_status (VARCHAR)  |
                  |     is_fraud, is_international    |
                  +-----------------+-----------------+
                                    | N
                                    |
                                    | 1
                  +-----------------+-----------------+
                  |        dim_failure_reasons        |
                  +-----------------------------------+
                  | PK  failure_reason_id (INT)       |
                  |     failure_reason_code (VARCHAR) |
                  |     failure_reason_description    |
                  |     failure_category (VARCHAR)    |
                  +-----------------------------------+
```

---

## 📊 6-Page Interactive Power BI Report Structure

The Power BI model [`FINSIGHT_360_Financial_Risk_Analytics.pbix`](./FINSIGHT_360_Financial_Risk_Analytics.pbix) comprises 6 executive views:

### Page 1: Executive Performance Overview
*Macro Financial KPIs, GMV trajectory, channel conversion waterfall, and global success/failure metrics.*
![Page 1 - Executive Overview](screenshots/page1_executive_overview.png)

### Page 2: Payment Performance & Gateway Reliability
*SLA benchmarking across Razorpay, PayU, Cashfree, HDFC Direct, and Paytm Gateway with timeout drill-downs.*
![Page 2 - Payment Performance](screenshots/page2_payment_performance.png)

### Page 3: Fraud & Risk Analytics
*Clustering by risk scores, cross-border exposure, and time-of-day fraud spikes (12 AM - 5 AM nocturnal surge).*
![Page 3 - Fraud & Risk Analytics](screenshots/page3_fraud_risk_analytics.png)

### Page 4: Customer Intelligence & Segment Dynamics
*High-Value at-risk customer churn matrix, credit score band analysis, and KYC friction points.*
![Page 4 - Customer Intelligence](screenshots/page4_customer_intelligence.png)

### Page 5: Revenue Risk & Pareto Concentration
*80/20 loss distribution across 8,000 merchants and recoverable revenue opportunity via failover routing.*
![Page 5 - Revenue Risk & Pareto](screenshots/page5_revenue_risk_pareto.png)

### Page 6: Executive Recommendations & Strategic Roadmap
*Prescriptive action plan, dynamic routing ROI model, and automated risk throttling workflows.*
![Page 6 - Executive Recommendations](screenshots/page6_executive_recommendations.png)

---

## 📐 Key DAX Measures

The data model features a modular DAX measure library in [`dax/`](./dax/) and [`powerbi/dax_measures.dax`](./powerbi/dax_measures.dax):

```dax
/// Revenue at Risk from Failed Transactions
Revenue at Risk (Failed) = 
CALCULATE(
    [Total Gross Volume GMV],
    fact_transactions[transaction_status] = "FAILED"
)

/// Failure Rate %
Failure Rate % = 
DIVIDE(
    [Failed Transactions],
    [Total Transactions],
    0
)

/// Top 20 Merchant Loss Share % (Pareto Concentration)
Top 20 Merchant Loss Share % = 
VAR TotalGlobalFailedVolume = 
    CALCULATE([Revenue at Risk (Failed)], ALL(dim_merchants))
VAR Top20MerchantsFailedVolume = 
    CALCULATE(
        [Revenue at Risk (Failed)],
        TOPN(
            20,
            ALL(dim_merchants[merchant_id]),
            [Revenue at Risk (Failed)],
            DESC
        )
    )
RETURN
DIVIDE(Top20MerchantsFailedVolume, TotalGlobalFailedVolume, 0)

/// High-Value At-Risk Customer Spend
At-Risk Customer Spend = 
CALCULATE(
    [Total Gross Volume GMV],
    FILTER(
        VALUES(dim_customers[customer_id]),
        [Failure Rate %] >= 0.20 && [Total Gross Volume GMV] >= 25000
    )
)
```

---

## 🚀 Quickstart & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Spurthi-019/FINSIGHT-360-Financial-Risk-Revenue-Analytics.git
cd FINSIGHT-360-Financial-Risk-Revenue-Analytics
```

### 2. Set Up Python Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install pandas numpy psycopg2-binary sqlalchemy scipy
```

### 3. Build Star Schema & Ingest into PostgreSQL
```bash
# 1. Transform raw data into normalized star schema CSVs:
python python/build_star_schema.py

# 2. Ingest into local PostgreSQL instance (finsight360 database):
python python/ingest_to_postgres.py

# 3. Execute production analytics and export CSV reports:
python python/run_sql_analytics.py

# 4. Run statistical hypothesis validation (Z-Test & Chi-Square):
python python/statistical_validation.py
```

### 4. Open the Power BI Dashboard
1. Open Microsoft Power BI Desktop.
2. Click **File** $\rightarrow$ **Open** $\rightarrow$ select [`FINSIGHT_360_Financial_Risk_Analytics.pbix`](./FINSIGHT_360_Financial_Risk_Analytics.pbix).
3. Update database credentials under **Transform Data** $\rightarrow$ **Data source settings** to point to your PostgreSQL instance.

---

## 📂 Repository Structure

```
FINSIGHT-360-Financial-Risk-Revenue-Analytics/
│
├── .gitignore
├── README.md
├── FINSIGHT_360_Financial_Risk_Analytics.pbix  <-- (Power BI Desktop Report)
│
├── data/
│   ├── schema.sql                              <-- (PostgreSQL DDL Star Schema)
│   └── README.md                               <-- (Data Dictionary & Model Specs)
│
├── sql/
│   ├── 01_exploratory_analysis.sql             <-- (Baseline Financial KPIs)
│   ├── 02_fraud_risk_clusters.sql              <-- (Off-Hours & Cross-Border Fraud)
│   ├── 03_revenue_pareto.sql                   <-- (80/20 Merchant Loss & Recoverability)
│   └── 04_production_analytics.sql             <-- (Full 6-Query Production Suite)
│
├── dax/
│   ├── core_kpis.dax                           <-- (GMV, Success/Failure Rates)
│   ├── fraud_analytics.dax                     <-- (Fraud Rates, Nocturnal Surge)
│   └── pareto_share.dax                        <-- (Top 20 Loss Share, At-Risk Spend)
│
├── python/
│   ├── inspect_raw_dataset.py                  <-- (Raw Dataset Profiler)
│   ├── build_star_schema.py                    <-- (ETL & Dimension Derivation)
│   ├── ingest_to_postgres.py                   <-- (Fast Bulk DB Ingestion)
│   ├── run_sql_analytics.py                    <-- (SQL Execution & CSV Export)
│   └── statistical_validation.py               <-- (Two-Proportion Z-Test & Chi-Square)
│
├── reports/
│   ├── raw_data_profile.txt
│   ├── statistical_validation_report.txt
│   └── sql_outputs/                            <-- (Exported Query CSVs)
│
├── screenshots/
│   └── README.md                               <-- (Report Page Previews)
│
└── app/
    └── .gitkeep                                <-- (Phase 6 Streamlit Copilot Placeholder)
```

---

## 👨‍💻 Author & Attribution
- **Author**: Spurthi ([@Spurthi-019](https://github.com/Spurthi-019))
- **Project**: FINsight 360 – Enterprise Financial Risk & Revenue Analytics
- **Repository**: [FINSIGHT-360-Financial-Risk-Revenue-Analytics](https://github.com/Spurthi-019/FINSIGHT-360-Financial-Risk-Revenue-Analytics)
