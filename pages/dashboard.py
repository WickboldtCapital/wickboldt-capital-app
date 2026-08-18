import streamlit as st
import pandas as pd
import sqlite3
import json
import os
from db_ops import get_user_projects_df, get_project_milestones, get_project_budget

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# --- ENTERPRISE PERSISTENT STORAGE ROUTING ---
if os.path.exists("/app/data"):
    DB_FILE = "/app/data/wickboldt_projects.db"
else:
    DB_FILE = "wickboldt_projects.db"

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

# 1. Fetch raw projects from Postgres to find unique portfolios
raw_projects_df = get_user_projects_df(user_email, role)

if raw_projects_df.empty:
    st.info("No active projects found for your account. Create a new development in the Project Control tab.")
    st.stop()

# 2. Extract Portfolios and create a dropdown filter
available_portfolios = sorted(raw_projects_df['portfolio_name'].unique().tolist()) if 'portfolio_name' in raw_projects_df.columns else ["Master Portfolio"]
col_p, _ = st.columns([1, 2])
selected_portfolio = col_p.selectbox("📁 Select Portfolio View", ["All Portfolios"] + available_portfolios)

# Filter the dataframe BEFORE doing the heavy math
if selected_portfolio != "All Portfolios":
    filtered_projects_df = raw_projects_df[raw_projects_df['portfolio_name'] == selected_portfolio] if 'portfolio_name' in raw_projects_df.columns else raw_projects_df
else:
    filtered_projects_df = raw_projects_df

# ==========================================
# ⚡ HIGH-SPEED CACHED AGGREGATION ENGINE
# ==========================================
# Now the cache is bound directly to the filtered dataframe. It only calculates the projects you asked to see!
@st.cache_data(ttl=60, show_spinner="Aggregating enterprise metrics...")
def compile_portfolio_metrics(projects_df):
    if projects_df.empty:
        return None
        
    t_projects = len(projects_df)
    t_budget, t_milestones, t_comp_milestones, t_safety, t_vault, t_lms = 0.0, 0, 0, 0, 0, 0
    p_data_list = []
    
    for _, proj in projects_df.iterrows():
        p_name = proj['project_name']
        p_phase = proj.get('phase', 'Active')
        
        # 1. Schedule Metrics
        m_df = get_project_milestones(p_name)
        p_total_m = len(m_df)
        p_comp_m = len(m_df[m_df['is_complete'] == 1]) if not m_df.empty else 0
        
        t_milestones += p_total_m
        t_comp_milestones += p_comp_m
        progress_pct = int((p_comp_m / p_total_m) * 100) if p_total_m > 0 else 0
        
        # 2. Budget Metrics
        b_df = get_project_budget(p_name)
        p_budget = b_df['total_cost'].sum() if not b_df.empty and 'total_cost' in b_df.columns else 0.0
        t_budget += p_budget
        
        # 3. Local JSON Metrics
        toolbox_count, vault_count, lms_count, comp_dd = 0, 0, 0, 0
        total_dd_items = 12 
        
        conn = None  # Setup connection variable outside try block
        try:
            # Added a 10-second timeout so it never freezes infinitely
            conn = sqlite3.connect(DB_FILE, timeout=10)
            table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
            if table_check:
                row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (p_name,)).fetchone()
                if row and row[0]:
                    try:
                        p_data = json.loads(row[0])
                        toolbox_count = len(p_data.get("toolbox_talks", []))
                        vault_count = sum(len(docs) for docs in p_data.get("vault_docs", {}).values())
                        dd_checklists = p_data.get("dd_checklists", {})
                        if dd_checklists:
                            comp_dd = sum(sum(items.values()) for items in dd_checklists.values() if isinstance(items, dict))
                    except json.JSONDecodeError:
                        pass # Ignore corrupted JSON rows without crashing
            
            lms_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lms_training_logs'").fetchone()
            if lms_check:
                lms_count = conn.execute("SELECT COUNT(*) FROM lms_training_logs WHERE project_name=?", (p_name,)).fetchone()[0]
        except Exception:
            pass
        finally:
            # THIS IS THE VITAL FIX: It guarantees the database lock is released!
            if conn:
                conn.close()
            
        t_safety += toolbox_count
        t_vault += vault_count
        t_lms += lms_count
        dd_progress_pct = int((comp_dd / total_dd_items) * 100)
                
        p_data_list.append({
            "Project": p_name,
            "Current Phase": p_phase,
            "DD Readiness": f"{dd_progress_pct}%",
            "Schedule Progress": f"{progress_pct}% ({p_comp_m}/{p_total_m})",
            "Total Budget Logged": f"${p_budget:,.2f}",
            "Safety Audits": toolbox_count,
            "Vault Files": vault_count,
            "Active Certifications": lms_count
        })
        
    return {
        "projects_df": projects_df,
        "portfolio_data": p_data_list,
        "metrics": (t_projects, t_budget, t_milestones, t_comp_milestones, t_safety, t_vault, t_lms)
    }

compiled_data = compile_portfolio_metrics(filtered_projects_df)

if not compiled_data:
    st.info("No data found for the selected portfolio.")
    st.stop()

# Unpack Data
projects_df = compiled_data["projects_df"]
portfolio_data = compiled_data["portfolio_data"]
total_projects, total_budget, total_milestones, total_milestones_completed, total_safety_talks, total_vault_files, total_lms_certs = compiled_data["metrics"]


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

# Reorder columns to put DD Readiness next to Schedule Progress
cols = ["Project", "Current Phase", "DD Readiness", "Schedule Progress", "Total Budget Logged", "Safety Audits", "Vault Files", "Active Certifications"]
portfolio_df = portfolio_df[cols]

st.dataframe(portfolio_df, use_container_width=True, hide_index=True)

# ==========================================
# COMPLIANCE QUICK-VIEW
# ==========================================
st.divider()
st.subheader("🛡️ Recent Global Compliance (LMS)")
conn = None
try:
    # Also added timeout and finally block here for ultimate safety
    conn = sqlite3.connect(DB_FILE, timeout=10)
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
except Exception:
    st.error("Unable to load recent compliance logs.")
finally:
    if conn:
        conn.close()