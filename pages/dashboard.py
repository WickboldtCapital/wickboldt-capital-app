import streamlit as st
import pandas as pd
import sqlite3
import json
from db_ops import get_user_projects_df, get_project_milestones, get_project_budget

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# ==========================================
# 🔒 SECURITY GUARD
# ==========================================
role = st.session_state.get("role")
user_email = st.session_state.get("email")

if not role or not user_email:
    st.warning("⚠️ Access Restricted: Please log in to view the dashboard.")
    st.stop()

st.title("📊 Executive Command Center")
if role == "Admin":
    st.markdown("High-level portfolio overview of **all active developments** across Wickboldt Capital.")
else:
    st.markdown(f"High-level portfolio overview of **your authorized developments** (`{user_email}`).")
st.divider()

# Fetch projects filtered by user access level (Multi-Tenant safe via db_ops)
projects_df = get_user_projects_df(user_email, role)

if projects_df.empty:
    st.info("No active projects found for your account. Create a new development in the Project Control tab.")
    st.stop()

# ==========================================
# PORTFOLIO AGGREGATION ENGINE
# ==========================================
total_projects = len(projects_df)
total_budget = 0.0
total_milestones = 0
total_milestones_completed = 0
total_safety_talks = 0
total_vault_files = 0
total_lms_certs = 0
portfolio_data = []

# Analyze each authorized project
for _, proj in projects_df.iterrows():
    p_name = proj['project_name']
    p_phase = proj.get('phase', 'Active') # Safe fallback if phase column missing
    
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
    
    # 3. Safety, Vault, and LMS Metrics (Safely Extracted)
    toolbox_count = 0
    vault_count = 0
    lms_count = 0
    
    try:
        conn = sqlite3.connect("wickboldt_projects.db")
        
        # Extract JSON state data (Toolbox & Vault)
        table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
        if table_check:
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (p_name,)).fetchone()
            if row and row[0]:
                p_data = json.loads(row[0])
                # Toolbox
                toolbox_count = len(p_data.get("toolbox_talks", []))
                # Vault
                vault_docs = p_data.get("vault_docs", {})
                vault_count = sum(len(docs) for docs in vault_docs.values())
                
        # Extract LMS Compliance data
        lms_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lms_training_logs'").fetchone()
        if lms_check:
            lms_count = conn.execute("SELECT COUNT(*) FROM lms_training_logs WHERE project_name=?", (p_name,)).fetchone()[0]
            
        conn.close()
    except Exception:
        pass
        
    total_safety_talks += toolbox_count
    total_vault_files += vault_count
    total_lms_certs += lms_count
            
    # Append to Master List
    portfolio_data.append({
        "Project": p_name,
        "Current Phase": p_phase,
        "Schedule Progress": f"{progress_pct}% ({p_comp_m}/{p_total_m})",
        "Total Budget Logged": f"${p_budget:,.2f}",
        "Safety Audits": toolbox_count,
        "Vault Files": vault_count,
        "Active Certifications": lms_count
    })

# ==========================================
# TOP LEVEL AGGREGATE METRICS
# ==========================================
st.subheader("🌐 Global Portfolio Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Active Developments", total_projects)
col2.metric("Total Managed Budget", f"${total_budget:,.2f}")
overall_progress = int((total_milestones_completed / total_milestones) * 100) if total_milestones > 0 else 0
col3.metric("Portfolio Schedule Progress", f"{overall_progress}%")

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
col4.metric("Total Safety Audits", total_safety_talks)
col5.metric("Vault Documents Secured", total_vault_files)
col6.metric("Active Jobsite Certifications", total_lms_certs)

st.divider()

# ==========================================
# PORTFOLIO BREAKDOWN TABLE
# ==========================================
st.subheader("🏢 Master Portfolio Breakdown")
portfolio_df = pd.DataFrame(portfolio_data)
st.dataframe(portfolio_df, use_container_width=True, hide_index=True)

# ==========================================
# COMPLIANCE QUICK-VIEW
# ==========================================
st.divider()
st.subheader("🛡️ Recent Global Compliance (LMS)")
try:
    conn = sqlite3.connect("wickboldt_projects.db")
    lms_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lms_training_logs'").fetchone()
    
    if lms_check:
        auth_projects_list = projects_df['project_name'].tolist()
        placeholders = ','.join(['?'] * len(auth_projects_list))
        lms_query = f"""
            SELECT project_name, worker_name, trade_company, course_name, completion_date 
            FROM lms_training_logs 
            WHERE project_name IN ({placeholders}) 
            ORDER BY completion_date DESC LIMIT 5
        """
        recent_lms_df = pd.read_sql_query(lms_query, conn, params=auth_projects_list)
        
        if not recent_lms_df.empty:
            st.dataframe(recent_lms_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent training certifications logged across your authorized portfolio.")
    else:
        st.info("LMS Compliance module initializing...")
    conn.close()
except Exception:
    st.error("Unable to load recent compliance logs.")