import streamlit as st
import pandas as pd
import sqlite3
import json
from db_ops import get_user_projects_df, get_project_milestones, get_project_budget

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# --- SECURITY GUARD ---
role = st.session_state.get("role")
user_email = st.session_state.get("email")

if not role or not user_email:
    st.warning("⚠️ Access Restricted: Please log in to view the dashboard.")
    st.stop()

st.title("📊 Executive Command Center")
if role == "Admin":
    st.markdown("High-level portfolio overview of **all active developments** across Wickboldt Capital.")
else:
    st.markdown(f"High-level portfolio overview of **your active developments** (`{user_email}`).")
st.divider()

# Fetch projects filtered by user access level
projects_df = get_user_projects_df(user_email, role)

if projects_df.empty:
    st.info("No active projects found for your account. Create a new development in the Project Control tab.")
    st.stop()

# Initialize Portfolio Aggregates
total_projects = len(projects_df)
total_budget = 0.0
total_milestones = 0
total_milestones_completed = 0
portfolio_data = []

# Analyze each project
for _, proj in projects_df.iterrows():
    p_name = proj['project_name']
    p_phase = proj['phase']
    
    # 1. Schedule Metrics
    m_df = get_project_milestones(p_name)
    p_total_m = len(m_df)
    p_comp_m = len(m_df[m_df['is_complete'] == 1]) if not m_df.empty else 0
    
    total_milestones += p_total_m
    total_milestones_completed += p_comp_m
    progress_pct = int((p_comp_m / p_total_m) * 100) if p_total_m > 0 else 0
    
    # 2. Budget Metrics
    b_df = get_project_budget(p_name)
    if not b_df.empty and 'total_cost' in b_df.columns:
        p_budget = b_df['total_cost'].sum()
    else:
        p_budget = 0.0
    total_budget += p_budget
    
    # 3. Safety & QC Metrics (Safely Extracted from JSON state)
    toolbox_count = 0
    try:
        conn = sqlite3.connect("wickboldt_projects.db")
        table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
        if table_check:
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (p_name,)).fetchone()
            if row and row[0]:
                p_data = json.loads(row[0])
                toolbox_count = len(p_data.get("toolbox_talks", []))
        conn.close()
    except Exception:
        pass
            
    # Append to Master List
    portfolio_data.append({
        "Project": p_name,
        "Current Phase": p_phase,
        "Schedule Progress": f"{progress_pct}% ({p_comp_m}/{p_total_m})",
        "Total Budget Logged": f"${p_budget:,.2f}",
        "Safety Talks Logged": toolbox_count
    })

# ==========================================
# TOP LEVEL AGGREGATE METRICS
# ==========================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Developments", total_projects)

overall_progress = int((total_milestones_completed / total_milestones) * 100) if total_milestones > 0 else 0
c2.metric("Portfolio Schedule Progress", f"{overall_progress}%")

c3.metric("Total Managed Budget", f"${total_budget:,.2f}")

total_safety = sum([d["Safety Talks Logged"] for d in portfolio_data])
c4.metric("Total Safety Audits", total_safety)

st.divider()

# ==========================================
# PORTFOLIO BREAKDOWN TABLE
# ==========================================
st.subheader("🏢 Master Portfolio Breakdown")
portfolio_df = pd.DataFrame(portfolio_data)
st.dataframe(portfolio_df, use_container_width=True, hide_index=True)