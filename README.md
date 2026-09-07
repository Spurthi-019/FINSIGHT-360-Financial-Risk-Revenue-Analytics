# 💳 FINSIGHT 360 – Enterprise Financial Risk & Revenue Analytics

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)
[![Power BI Dashboard](https://img.shields.io/badge/Power_BI-Dashboard_Report-F2C811?logo=powerbi&logoColor=black)](./FINSIGHT%20360.pbix)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Data_Model-Star_Schema-336791?logo=postgresql&logoColor=white)](./data/schema.sql)
[![DAX](https://img.shields.io/badge/DAX-Measures_Library-005BA1)](./powerbi/dax_measures.dax)

> **FINsight 360** is an end-to-end, enterprise-grade financial analytics and fraud intelligence platform. It ingests 300,000+ multi-channel transaction records into an optimized Star Schema, executes statistical hypothesis testing, delivers a 6-page Power BI executive intelligence suite, and provides a dark-mode Streamlit AI Copilot identifying **₹84.27M in revenue at risk** and **₹25.42M in recoverable GMV**.

---

## 🚀 Live Deliverables & Interactive Demos

| Deliverable | Technology Stack | Access / Download Link |
| :--- | :--- | :--- |
| **Streamlit AI Analyst Copilot** | Python 3.11, Gemini/OpenAI API, DuckDB, Plotly | [🚀 Launch Web App](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/) |
| **Power BI Interactive Report** | Power BI Desktop, DAX, Data Modeling | [📥 Download .pbix File](./FINSIGHT%20360.pbix) |
| **Star Schema DDL & SQL Engine** | SQL, PostgreSQL / DuckDB DDL | [🗄️ View Schema Script](./data/schema.sql) |

---

## 🔍 Core Financial Audit Findings

| Metric | Measured Value | Business Impact |
| :--- | :---: | :--- |
| **Total Gross Merchandise Value (GMV)** | **₹720.91M** (300,113 Txns) | Macro processing volume across all payment channels and acquirer gateways. |
| **Successful Settlement Volume** | **₹625.40M** (86.64%) | Baseline clean transaction processing conversion rate. |
| **Total Revenue at Risk (Failed)** | **₹84.27M** (35,232 Txns) | Total financial leakage across infrastructure timeouts and customer declines. |
| **Recoverable Baseline GMV** | **₹25.42M** (10,607 Txns) | **~30.2% of failed volume** addressable via dynamic multi-gateway failover routing. |
| **High-Value Account Exposure** | **1,735 Customers** (₹82.41M Spend) | High-spend accounts (> ₹25,000 spend) experiencing elevated failure rates ($\ge 20\%$). |
| **Off-Hours Fraud Surge** | **4.2x Escalation** (12 AM - 5 AM IST) | Heightened post-auth fraud frequency on transactions exceeding ₹5,000. |

---

## 🤖 AI Analyst Copilot (Streamlit App)

The repository includes a production-ready, dark-mode glassmorphic AI Copilot deployed live at **[finsight-360-financial-risk-revenue-analytics.streamlit.app](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)**.

* **💬 Executive Plain-English Summaries**: Automatically synthesizes complex analytical query results into 2–4 concise, actionable bullet points tailored for C-suite and VP stakeholders without technical SQL jargon.
* **🧠 Autonomous Natural Language to SQL**: Converts natural language prompts into validated SQL queries against the 5-table Star Schema. Integrates OpenAI GPT-4o, Google Gemini 2.0 Flash, and zero-config offline heuristics.
* **📊 Dynamic Plotly Visualizations**: Generates dark-themed interactive charts for volume aggregations, merchant loss distributions, and gateway failure rates.
* **📋 Detailed Data Tables & Export**: Interactive data inspection with one-click CSV export functionality.
* **🔍 Glassmorphic Technical Inspector**: Expandable SQL inspection container for data engineers and analytics teams.
* **🏛️ Star Schema Visualizer**: Sidebar metadata explorer displaying active table record counts, column types, and sample data previews.
* **🔒 Strict Enterprise Mode**: Read-only query security guard blocking mutation operations (`DROP`, `DELETE`, `UPDATE`, `INSERT`).

---

## 📊 Power BI 6-Page Executive Suite

The complete interactive Power BI model [`FINSIGHT 360.pbix`](./FINSIGHT%20360.pbix) (14.1 MB) delivers six dedicated analytics pages:

* **Page 1: Executive Performance Overview** — Macro financial KPIs, GMV trajectory, payment channel conversion waterfall, and global success/failure distributions.
<br><img width="673" height="380" alt="Executive Performance Overview" src="https://github.com/user-attachments/assets/2d0c2389-7c7f-419e-8be3-24a7fef85dda" />

* **Page 2: Payment Performance & Gateway Reliability** — SLA benchmarking across Razorpay, PayU, Cashfree, HDFC Direct, and Paytm Gateway with acquirer timeout root-cause drill-downs.
<br><img width="676" height="385" alt="Payment Performance and Gateway Reliability" src="https://github.com/user-attachments/assets/39566df6-0c2e-4df3-b579-0c1485b4eb86" />

* **Page 3: Fraud & Risk Analytics** — Clustering by risk scores, cross-border exposure, and nocturnal fraud spikes (4.2x surge between 12 AM and 5 AM IST).
<br><img width="678" height="383" alt="Fraud and Risk Analytics" src="https://github.com/user-attachments/assets/de886f80-22a0-4216-829d-cfa0035640cf" />

* **Page 4: Customer Intelligence & Segment Dynamics** — High-Value at-risk customer churn matrix, credit score band analysis, and KYC tier friction points.
<br><img width="677" height="383" alt="Customer Intelligence and Segment Dynamics" src="https://github.com/user-attachments/assets/c4a4bdb5-267b-4247-8e74-a4cef52662ee" />

* **Page 5: Revenue Risk & Pareto Concentration** — 80/20 loss distribution across 8,000 enterprise merchants and recoverable revenue opportunity via smart failover routing.
<br><img width="680" height="388" alt="Revenue Risk and Pareto Concentration" src="https://github.com/user-attachments/assets/57e478d8-d7d5-44a3-8bf6-0596aee7ac15" />

* **Page 6: Executive Recommendations & Strategic Roadmap** — Prescriptive action plan, dynamic routing ROI models, and automated risk throttling workflows.
<br><img width="679" height="383" alt="Executive Recommendations and Strategic Roadmap" src="https://github.com/user-attachments/assets/1239483e-ef5e-4688-be76-30957d7d29b4" />

---

## 🏗️ Architecture & Data Modeling

The underlying database implements a normalized Star Schema designed for high-performance OLAP analytical querying:

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

## 📐 Key DAX Measures & Logic

The data model features an enterprise DAX measure library in [`dax/`](./dax/) and [`powerbi/dax_measures.dax`](./powerbi/dax_measures.dax):

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

## 📂 Repository Structure

```
FINSIGHT-360-Financial-Risk-Revenue-Analytics/
│
├── .streamlit/
│   └── config.toml                             <-- (Dark Theme Glassmorphic Configuration)
├── .gitignore
├── requirements.txt                            <-- (Root Dependencies for Streamlit Cloud)
├── README.md
├── FINSIGHT 360.pbix                           <-- (Power BI Desktop Report - 14.1 MB)
│
├── app/
│   ├── app.py                                  <-- (Streamlit AI Copilot Interface)
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

## ⚡ Quickstart & Setup Guide

* **Step 1: Clone Repository**
  ```bash
  git clone https://github.com/Spurthi-019/FINSIGHT-360-Financial-Risk-Revenue-Analytics.git
  cd FINSIGHT-360-Financial-Risk-Revenue-Analytics
  ```

* **Step 2: Environment Setup & Local Streamlit Launch**
  ```bash
  python -m venv venv
  # Windows:
  venv\Scripts\activate
  # Linux/macOS:
  source venv/bin/activate

  pip install -r requirements.txt

  # Launch the Streamlit AI Analyst Copilot:
  streamlit run app/app.py
  ```

* **Step 3: Star Schema Build & Database Ingestion**
  ```bash
  # Transform raw data into normalized star schema CSVs:
  python python/build_star_schema.py

  # Ingest into local PostgreSQL instance (finsight360 database):
  python python/ingest_to_postgres.py

  # Execute SQL analytics and export query results:
  python python/run_sql_analytics.py

  # Run hypothesis testing (Two-Proportion Z-Test & Chi-Square):
  python python/statistical_validation.py
  ```

* **Step 4: Power BI Report Access**
  1. Open Microsoft Power BI Desktop.
  2. Click **File** $\rightarrow$ **Open** $\rightarrow$ select [`FINSIGHT 360.pbix`](./FINSIGHT%20360.pbix).
  3. *(Optional)* Update database connection under **Transform Data** $\rightarrow$ **Data source settings** to point to your live PostgreSQL database.

---

## 👨‍💻 Author & Attribution
* **Author**: Spurthi ([@Spurthi-019](https://github.com/Spurthi-019))
* **Project**: FINsight 360 – Enterprise Financial Risk & Revenue Analytics
* **Live Streamlit Copilot**: [FINsight 360 Web App](https://finsight-360-financial-risk-revenue-analytics.streamlit.app/)
* **Repository**: [FINSIGHT-360-Financial-Risk-Revenue-Analytics](https://github.com/Spurthi-019/FINSIGHT-360-Financial-Risk-Revenue-Analytics)
