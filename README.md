# 💳 FINsight 360 – Enterprise Financial Risk & Revenue Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![DAX](https://img.shields.io/badge/DAX-Measures-005BA1)](https://learn.microsoft.com/en-us/dax/)
[![SQL](https://img.shields.io/badge/SQL-Analytics-CC292B)](https://www.postgresql.org/docs/)

> **FINsight 360** is an end-to-end, enterprise-grade financial analytics and fraud intelligence platform. It ingests 300,000+ multi-channel transaction records into an optimized PostgreSQL Star Schema, executes advanced statistical hypothesis testing, delivers an executive Power BI intelligence suite, and provides a dark-mode Streamlit AI Copilot identifying **₹84.27M in revenue at risk** and **₹25.42M in recoverable GMV**.

---

## 🌟 Core Live Deliverables

| Deliverable | Access Link | Description |
| :--- | :--- | :--- |
| 🤖 **Live Streamlit AI Analyst Copilot** | [**Launch Live Copilot Web App**](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/) | Text-to-SQL copilot with executive plain-language summaries, Plotly visual charts, and Star Schema visualizer. |
| 📊 **Power BI Interactive Dashboard** | [**📥 Download FINSIGHT 360 Power BI Dashboard (14.1 MB)**](./FINSIGHT%20360.pbix) | Complete 6-page production `.pbix` desktop report with custom DAX measures and dimensional model. |

---

## 📥 Power BI Report Download

Download the complete interactive Power BI Desktop report (`FINSIGHT 360.pbix`, 14.1 MB) directly from this repository:

👉 **[📥 Download FINSIGHT 360 Power BI Dashboard](./FINSIGHT%20360.pbix)**

*To view and interact with the data model, KPIs, and dashboards, open this file in [Microsoft Power BI Desktop](https://powerbi.microsoft.com/desktop/).*

---

## 🤖 Phase 6: Streamlit AI Financial Analyst Copilot

The repository includes a production-ready, dark-mode glassmorphic AI Analyst Copilot deployed live at **[finsight-360-financial-risk-revenue-analytics.streamlit.app](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)**.

### Copilot Features & Architecture:
- 💬 **Executive Plain-English Summaries**: Automatically synthesizes complex query results into 2–4 actionable bullet points for C-suite and VP stakeholders without technical jargon.
- 🧠 **Autonomous Natural Language to SQL**: Translates user questions into validated standard SQL matching the 5-table Star Schema. Supports OpenAI GPT-4o, Google Gemini 2.0 Flash, and zero-config semantic offline heuristics.
- 📊 **Dynamic Plotly Visualizations**: Automatically generates interactive dark-themed charts for metric aggregations, merchant loss distributions, and gateway failure rates.
- 📋 **Detailed Data Tables**: Rendered directly in `st.dataframe` with CSV export capabilities.
- 🔍 **Glassmorphic SQL Expander**: Expandable technical inspector allowing data engineers to review generated SQL queries and execution logic.
- 🏛️ **Star Schema Visualizer**: Sidebar metadata explorer displaying active table row counts, column data types, and instant sample previews.
- 🔒 **Strict Enterprise Mode**: Read-only query security guard blocking mutation keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`).

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

The Power BI model [`FINSIGHT 360.pbix`](./FINSIGHT%20360.pbix) comprises 6 executive views:

### Page 1: Executive Performance Overview
*Macro Financial KPIs, GMV trajectory, channel conversion waterfall, and global success/failure metrics.*
<img width="673" height="380" alt="Screenshot 2026-09-07 151257" src="https://github.com/user-attachments/assets/2d0c2389-7c7f-419e-8be3-24a7fef85dda" />


### Page 2: Payment Performance & Gateway Reliability
*SLA benchmarking across Razorpay, PayU, Cashfree, HDFC Direct, and Paytm Gateway with timeout drill-downs.*
<img width="676" height="385" alt="Screenshot 2026-09-07 151318" src="https://github.com/user-attachments/assets/39566df6-0c2e-4df3-b579-0c1485b4eb86" />


### Page 3: Fraud & Risk Analytics
*Clustering by risk scores, cross-border exposure, and time-of-day fraud spikes (12 AM - 5 AM nocturnal surge).*
<img width="678" height="383" alt="Screenshot 2026-09-07 151330" src="https://github.com/user-attachments/assets/de886f80-22a0-4216-829d-cfa0035640cf" />


### Page 4: Customer Intelligence & Segment Dynamics
*High-Value at-risk customer churn matrix, credit score band analysis, and KYC friction points.*
<img width="677" height="383" alt="Screenshot 2026-09-07 151342" src="https://github.com/user-attachments/assets/c4a4bdb5-267b-4247-8e74-a4cef52662ee" />


### Page 5: Revenue Risk & Pareto Concentration
*80/20 loss distribution across 8,000 merchants and recoverable revenue opportunity via failover routing.*
<img width="680" height="388" alt="Screenshot 2026-09-07 151354" src="https://github.com/user-attachments/assets/57e478d8-d7d5-44a3-8bf6-0596aee7ac15" />


### Page 6: Executive Recommendations & Strategic Roadmap
*Prescriptive action plan, dynamic routing ROI model, and automated risk throttling workflows.*
<img width="679" height="383" alt="Screenshot 2026-09-07 151404" src="https://github.com/user-attachments/assets/1239483e-ef5e-4688-be76-30957d7d29b4" />


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

### 2. Set Up Python Environment & Run Streamlit App
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run the AI Analyst Copilot:
streamlit run app/app.py
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
2. Click **File** $\rightarrow$ **Open** $\rightarrow$ select [`FINSIGHT 360.pbix`](./FINSIGHT%20360.pbix).
3. Update database credentials under **Transform Data** $\rightarrow$ **Data source settings** to point to your PostgreSQL instance.

---

## 📂 Repository Structure

```
FINSIGHT-360-Financial-Risk-Revenue-Analytics/
│
├── .streamlit/
│   └── config.toml                             <-- (Dark Theme Glassmorphic Configuration)
├── .gitignore
├── requirements.txt                            <-- (Deployment Dependencies)
├── README.md
├── FINSIGHT 360.pbix                           <-- (Power BI Desktop Report - 14.1 MB)
│
├── app/
│   ├── app.py                                  <-- (Streamlit Copilot Interface)
│   ├── db_engine.py                            <-- (DuckDB & SQLite Analytical Engine)
│   ├── llm_helper.py                           <-- (Text-to-SQL & Executive Summary Generator)
│   ├── requirements.txt                        <-- (App-level Dependencies)
│   └── .env.example                            <-- (Environment Config Template)
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
└── screenshots/
    └── README.md                               <-- (Report Page Previews)
```

---

## 👨‍💻 Author & Attribution
- **Author**: Spurthi ([@Spurthi-019](https://github.com/Spurthi-019))
- **Project**: FINsight 360 – Enterprise Financial Risk & Revenue Analytics
- **Live Streamlit Copilot**: [FINsight 360 Web App](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)
- **Repository**: [FINSIGHT-360-Financial-Risk-Revenue-Analytics](https://github.com/Spurthi-019/FINSIGHT-360-Financial-Risk-Revenue-Analytics)
