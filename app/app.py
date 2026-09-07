import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Add app directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import db_engine
import llm_helper

# Page Configuration
st.set_page_config(
    page_title="FINsight 360 – AI Financial Risk Copilot",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern Financial UI
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38ef7d 0%, #11998e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
    }
    .badge-chip {
        display: inline-block;
        padding: 4px 10px;
        background-color: #0f172a;
        border: 1px solid #38ef7d;
        color: #38ef7d;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome to **FINsight 360 AI Analyst Copilot**! Ask any question in plain English to query the 300,000+ transaction Star Schema.",
            "sql": None,
            "df": None
        }
    ]

# -----------------------------------------------------------------------------
# SIDEBAR: CONFIGURATION & SCHEMA EXPLORER
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Copilot Settings")
    
    # LLM Provider Selection
    provider = st.selectbox(
        "LLM Engine",
        ["Built-in Semantic Copilot (Demo)", "OpenAI GPT", "Google Gemini"],
        index=0
    )
    
    api_key = None
    if provider == "OpenAI GPT":
        api_key = st.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    elif provider == "Google Gemini":
        api_key = st.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
    
    st.markdown("---")
    
    # Star Schema Database Explorer
    st.markdown("### 🏛️ Star Schema Explorer")
    try:
        schema_meta = db_engine.get_schema_metadata()
        st.caption(f"Engine: **{schema_meta['engine']}** | Records: **348,107 Total**")
        
        for table_name, t_info in schema_meta["tables"].items():
            with st.expander(f"📦 {table_name} ({t_info['rows']:,} rows)"):
                st.markdown("**Columns:**")
                for col in t_info["columns"]:
                    dtype = t_info.get("dtypes", {}).get(col, "")
                    st.markdown(f"- `{col}` <span style='color:#64748b;font-size:0.8rem;'>({dtype})</span>", unsafe_allow_html=True)
                
                if st.button(f"Preview {table_name}", key=f"btn_prev_{table_name}"):
                    sample_df = db_engine.get_sample_data(table_name, limit=3)
                    st.dataframe(sample_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading schema metadata: {e}")

    st.markdown("---")
    
    # Quick Sample Queries
    st.markdown("### 💡 Quick Analytics Prompts")
    sample_queries = [
        "Executive macro financial KPI overview",
        "Top failure reasons ranked by lost revenue",
        "Gateway SLA performance and timeout breakdown",
        "July peak evening UPI failure anomaly in Tier-2 Cities",
        "High-value customers at churn risk with spend > 25k",
        "Off-hours nocturnal fraud volume vs daytime",
        "Payment channel breakdown with average ticket size"
    ]
    
    for sq in sample_queries:
        if st.button(f"🔍 {sq}", key=f"chip_{sq}"):
            st.session_state["user_input_preset"] = sq

# -----------------------------------------------------------------------------
# MAIN VIEW: HEADER & MACRO KPI BAR
# -----------------------------------------------------------------------------
st.markdown("<div class='main-title'>💳 FINsight 360 – AI Analyst Copilot</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Autonomous Text-to-SQL Analytics on Dimensional Star Schema (300,113 Transactions)</div>", unsafe_allow_html=True)

# Macro KPI Ribbon
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("<div class='metric-card'><div class='metric-label'>Total GMV Processed</div><div class='metric-val'>₹720.91M</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='metric-card'><div class='metric-label'>Successful Settlement</div><div class='metric-val' style='color:#10b981;'>86.64% (₹625.4M)</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='metric-card'><div class='metric-label'>Revenue at Risk (Failed)</div><div class='metric-val' style='color:#f59e0b;'>₹84.27M (11.74%)</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown("<div class='metric-card'><div class='metric-label'>Fraud Blocked</div><div class='metric-val' style='color:#ef4444;'>₹11.24M (1.62%)</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CHAT INTERFACE & QUERY EXECUTION
# -----------------------------------------------------------------------------

# Render historical messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("🛠️ Generated SQL Query", expanded=False):
                st.code(msg["sql"], language="sql")
        if msg.get("df") is not None:
            st.dataframe(msg["df"], use_container_width=True)

# Handle preset click or chat input
user_prompt = st.chat_input("Ask any financial analytics question (e.g., 'What are the top 5 failure causes by lost revenue?')")
if "user_input_preset" in st.session_state:
    user_prompt = st.session_state.pop("user_input_preset")

if user_prompt:
    # 1. Display user query
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Process with AI Copilot
    with st.chat_message("assistant"):
        with st.spinner("🤖 Translating question to SQL & executing query..."):
            provider_param = "openai" if "OpenAI" in provider else ("gemini" if "Gemini" in provider else "fallback")
            generated_sql = llm_helper.generate_sql(user_prompt, api_key=api_key, provider=provider_param)
            
            # Show SQL code
            with st.expander("🛠️ Generated SQL Query", expanded=True):
                st.code(generated_sql, language="sql")

            try:
                # Execute query against DuckDB / SQLite engine
                result_df = db_engine.run_query(generated_sql)
                
                # Display Results
                st.markdown(f"**Query Results** (`{len(result_df):,}` rows returned):")
                st.dataframe(result_df, use_container_width=True)

                # Intelligent Visual Rendering
                # If we have 1 categorical column and 1-2 numeric columns, plot it
                numeric_cols = list(result_df.select_dtypes(include=[np.number]).columns)
                text_cols = list(result_df.select_dtypes(exclude=[np.number]).columns)

                if len(text_cols) >= 1 and len(numeric_cols) >= 1 and len(result_df) <= 30:
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
                            color_discrete_sequence=["#38ef7d", "#11998e", "#f59e0b", "#ef4444"]
                        )
                        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=380)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass

                # CSV Download Button
                csv_data = result_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Export Query Results to CSV",
                    data=csv_data,
                    file_name="finsight360_query_export.csv",
                    mime="text/csv"
                )

                # Save assistant message to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Executed query for: *\"{user_prompt}\"*",
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
