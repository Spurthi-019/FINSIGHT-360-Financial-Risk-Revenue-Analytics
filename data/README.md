# FINsight 360 – Data Architecture & Schema Documentation

This directory contains the database schema specifications, ETL definitions, and relational models for **FINsight 360**.

---

## 🏛️ Star Schema Architecture

The data pipeline normalizes raw transaction logs into an optimized dimensional star schema in PostgreSQL:

```
                  +-----------------------------------+
                  |           dim_customers           |
                  +-----------------------------------+
                  | PK  customer_id (INT)             |
                  |     customer_name (VARCHAR)       |
                  |     customer_segment (VARCHAR)    |
                  |     city (VARCHAR)                |
                  |     state (VARCHAR)               |
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

## 📊 Table Specifications & Row Counts

| Table Name | Type | Primary Key | Record Count | Description |
| :--- | :--- | :--- | :---: | :--- |
| [`fact_transactions`](schema.sql#L43-L58) | Central Fact | `transaction_id` | **300,113** | Granular payment transactions, financial amounts, timestamps, gateways, risk scores, and statuses. |
| [`dim_customers`](schema.sql#L13-L23) | Dimension | `customer_id` | **39,983** | Customer demographic data, credit score bands, KYC status, and average spend tiers. |
| [`dim_merchants`](schema.sql#L25-L33) | Dimension | `merchant_id` | **8,000** | Merchant business categories, geographic locations, and merchant risk scores. |
| [`dim_payment_methods`](schema.sql#L35-L41) | Dimension | `payment_method_id` | **4** | Payment channels: Credit/Debit Card, UPI Instant Pay, Digital Wallet, Net Banking. |
| [`dim_failure_reasons`](schema.sql#L43-L49) | Dimension | `failure_reason_id` | **7** | Standardized error codes (e.g., `GATEWAY_TIMEOUT`, `INSUFFICIENT_FUNDS`, `BANK_DECLINED`, `RISK_BLOCKED`). |

---

## ⚙️ Reproducible Data Generation
To regenerate the processed dimensional CSV files locally:
```bash
python python/build_star_schema.py
```
To ingest into PostgreSQL:
```bash
python python/ingest_to_postgres.py
```
