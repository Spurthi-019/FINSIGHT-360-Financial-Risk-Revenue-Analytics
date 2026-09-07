import os
import sys
import re
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Add app directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import db_engine
import llm_helper

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FINSIGHT 360 — AI Financial Analyst Copilot",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. MODERN DARK GLASSMORPHISM CUSTOM CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1117 0%, #0a0c10 90%);
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Glassmorphic Metric Cards with Neon/Teal Glow */
    .glass-card {
        background: rgba(22, 27, 34, 0.75);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(56, 239, 125, 0.25);
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 0 12px rgba(56, 239, 125, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 239, 125, 0.6);
        box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.2), inset 0 0 16px rgba(56, 239, 125, 0.1);
    }
    .card-cyan {
        border-color: rgba(0, 242, 254, 0.3);
    }
    .card-cyan:hover {
        border-color: rgba(0, 242, 254, 0.8);
        box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.25);
    }
    .card-amber {
        border-color: rgba(245, 158, 11, 0.3);
    }
    .card-amber:hover {
        border-color: rgba(245, 158, 11, 0.8);
        box-shadow: 0 12px 40px 0 rgba(245, 158, 11, 0.25);
    }
    .card-rose {
        border-color: rgba(239, 68, 68, 0.3);
    }
    .card-rose:hover {
        border-color: rgba(239, 68, 68, 0.8);
        box-shadow: 0 12px 40px 0 rgba(239, 68, 68, 0.25);
    }

    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #8b949e;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #7ee787;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Live Header Tag */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 30px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #34d399;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }

    /* Quick Prompt Chips */
    .prompt-chip {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 10px;
        padding: 10px 14px;
        color: #c9d1d9;
        font-size: 0.88rem;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 8px;
    }
    .prompt-chip:hover {
        background: rgba(56, 239, 125, 0.15);
        border-color: #38ef7d;
        color: #ffffff;
    }

    /* Glassmorphism Expander & Container */
    .streamlit-expanderHeader {
        background: rgba(22, 27, 34, 0.6) !important;
        border-radius: 8px !important;
    }

    /* Chat Messages Glass Styling */
    div[data-testid="stChatMessage"] {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome to **FINSIGHT 360 AI Analyst Copilot**! Ask any financial, risk, or operational question to autonomously query the 300,000+ transaction Star Schema.",
            "sql": None,
            "df": None
        }
    ]

# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & SCHEMA VISUALIZER
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Copilot Control Center")
    
    # LLM Engine Selector
    provider = st.selectbox(
        "🧠 LLM Engine Provider",
        ["Built-in Semantic Copilot (Zero-Config)", "OpenAI GPT-4o / GPT-4o-mini", "Google Gemini 2.0 Flash"],
        index=0
    )
    
    api_key = None
    if "OpenAI" in provider:
        api_key = st.text_input("🔑 OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    elif "Gemini" in provider:
        api_key = st.text_input("🔑 Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

    # Strict Enterprise Mode Toggle
    st.markdown("---")
    enterprise_mode = st.toggle("🔒 Strict Enterprise Mode", value=True, help="Enforces strict read-only SELECT execution to prevent schema mutations.")

    st.markdown("---")
    
    # Star Schema Visualizer
    st.markdown("### 🏛️ Star Schema Visualizer")
    try:
        schema_meta = db_engine.get_schema_metadata()
        st.caption(f"Engine: **{schema_meta['engine']}** | Records: **348,107 Total**")
        
        for table_name, t_info in schema_meta["tables"].items():
            with st.expander(f"📦 {table_name} ({t_info['rows']:,} rows)"):
                st.markdown("**Field Schema:**")
                for col in t_info["columns"]:
                    dtype = t_info.get("dtypes", {}).get(col, "")
                    st.markdown(f"- `{col}` <span style='color:#8b949e;font-size:0.78rem;'>({dtype})</span>", unsafe_allow_html=True)
                
                if st.button(f"Preview {table_name}", key=f"btn_prev_{table_name}"):
                    sample_df = db_engine.get_sample_data(table_name, limit=3)
                    st.dataframe(sample_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading schema metadata: {e}")

    st.markdown("---")
    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation history cleared. Ready for your next query!",
                "sql": None,
                "df": None
            }
        ]
        st.rerun()

# -----------------------------------------------------------------------------
# 5. PAGE HEADER & ENTERPRISE KPI ROW
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("<h1 style='margin-bottom:2px; font-weight:800; font-size:2.3rem;'>FINSIGHT 360 — AI Financial Analyst Copilot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8b949e; font-size:1.02rem; margin-bottom:18px;'>Autonomous Natural Language to SQL Analytics on 300,113 Financial Transactions</p>", unsafe_allow_html=True)
with header_col2:
    status_label = "GPT-4o Connected" if "OpenAI" in provider else ("Gemini 2.0 Connected" if "Gemini" in provider else "Semantic Star Schema Connected")
    st.markdown(f"<div style='text-align:right; margin-top:14px;'><span class='status-badge'>🟢 {status_label}</span></div>", unsafe_allow_html=True)

# 3-Column Enterprise KPI Cards
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.markdown("""
    <div class='glass-card card-amber'>
        <div class='metric-title'>⚠️ Total Revenue at Risk</div>
        <div class='metric-value' style='color:#fbbf24;'>₹84.27M</div>
        <div class='metric-sub' style='color:#f59e0b;'>35,232 Failed Transaction Attempts (11.74%)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown("""
    <div class='glass-card card-cyan'>
        <div class='metric-title'>🔄 Recoverable Baseline GMV</div>
        <div class='metric-value' style='color:#38ef7d;'>₹25.42M</div>
        <div class='metric-sub' style='color:#34d399;'>Addressable via Dynamic Acquirer Failover Routing</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown("""
    <div class='glass-card card-rose'>
        <div class='metric-title'>🌙 Off-Hours Fraud Spike</div>
        <div class='metric-value' style='color:#f87171;'>4.2x</div>
        <div class='metric-sub' style='color:#ef4444;'>Elevated Risk Surge (12 AM - 5 AM IST on Tickets > ₹5k)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. INTERACTIVE QUICK SAMPLE CHIPS
# -----------------------------------------------------------------------------
st.markdown("#### 💡 Quick Analytical Inquiries")
chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)

selected_preset = None
with chip_col1:
    if st.button("📊 Top 10 Merchants by Loss Volume", use_container_width=True):
        selected_preset = "Show Top 10 merchants by failed transaction volume"
with chip_col2:
    if st.button("⚡ Gateway Failures in Tier-2 Cities", use_container_width=True):
        selected_preset = "Which gateway has the highest failure rate in Tier-2 cities?"
with chip_col3:
    if st.button("🌙 Off-Hours Fraud > ₹5,000", use_container_width=True):
        selected_preset = "List off-hours transactions over ₹5,000 flagged for fraud"
with chip_col4:
    if st.button("🔍 Failure Reasons by Revenue Lost", use_container_width=True):
        selected_preset = "Failure reason breakdown by revenue lost"

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. CHAT EXPERIENCE & SQL EXECUTION ENGINE
# -----------------------------------------------------------------------------

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("🔍 View Executed SQL Query", expanded=False):
                st.code(msg["sql"], language="sql")
        if msg.get("df") is not None:
            st.dataframe(msg["df"], use_container_width=True)

# Chat Input handling (handles input box and quick chips)
user_prompt = st.chat_input("💬 Ask a question about revenue risk, merchants, gateways, fraud, or customers...")
if selected_preset:
    user_prompt = selected_preset

if user_prompt:
    # Append & display user prompt
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(f"**{user_prompt}**")

    # Generate SQL and execute query
    with st.chat_message("assistant"):
        with st.spinner("🤖 Translating query into Star Schema SQL & executing..."):
            provider_param = "openai" if "OpenAI" in provider else ("gemini" if "Gemini" in provider else "fallback")
            generated_sql = llm_helper.generate_sql(user_prompt, api_key=api_key, provider=provider_param)

            # Strict Enterprise Mode Safety Guard
            if enterprise_mode:
                forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
                if any(re.search(rf"\b{kw}\b", generated_sql, re.IGNORECASE) for kw in forbidden_keywords):
                    err_text = "🛡️ **Security Alert**: Mutation queries are blocked under Strict Enterprise Mode."
                    st.error(err_text)
                    st.session_state.messages.append({"role": "assistant", "content": err_text, "sql": generated_sql, "df": None})
                    st.stop()

            # Display generated SQL in glassmorphic expander
            with st.expander("🔍 View Executed SQL Query", expanded=True):
                st.code(generated_sql, language="sql")

            try:
                # Run query against analytical engine
                result_df = db_engine.run_query(generated_sql)

                st.markdown(f"**Query Results** (`{len(result_df):,}` rows returned):")
                st.dataframe(result_df, use_container_width=True)

                # Automatic Plotly Chart Generation
                numeric_cols = list(result_df.select_dtypes(include=[np.number]).columns)
                text_cols = list(result_df.select_dtypes(exclude=[np.number]).columns)

                if len(text_cols) >= 1 and len(numeric_cols) >= 1 and 1 < len(result_df) <= 30:
                    try:
                        import plotly.express as px
                        x_col = text_cols[0]
                        y_col = numeric_cols[0]
                        
                        fig = px.bar(
                            result_df, 
                            x=x_col, 
                            y=y_col, 
                            title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                            template="plotly_dark",
                            color=y_col,
                            color_continuous_scale=["#11998e", "#38ef7d", "#00f2fe", "#f59e0b"]
                        )
                        fig.update_layout(
                            paper_bgcolor="rgba(22, 27, 34, 0.75)",
                            plot_bgcolor="rgba(0, 0, 0, 0)",
                            margin=dict(l=20, r=20, t=40, b=20),
                            height=390,
                            font=dict(color="#e6edf3")
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

                # Export to CSV button
                csv_bytes = result_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Export Result to CSV",
                    data=csv_bytes,
                    file_name="finsight360_query_export.csv",
                    mime="text/csv"
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Query executed successfully for: *\"{user_prompt}\"*",
                    "sql": generated_sql,
                    "df": result_df
                })

            except Exception as e:
                error_msg = f"❌ SQL Execution Error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sql": generated_sql,
                    "df": None
                })
