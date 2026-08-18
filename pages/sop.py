import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

st.set_page_config(page_title="Standard Operating Procedures (SOP)", layout="wide")

# ==========================================
# 🔒 SECURITY & CONTEXT GUARDS
# ==========================================
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Access Restricted: Please log in.")
    st.stop()

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load an authorized project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"
role = st.session_state.get("role", "Viewer")

# --- DB HELPERS (GLOBAL TABLES) ---
def init_sop_db():
    conn = sqlite3.connect(DB_FILE)
    # Global SOP table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_sops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            content TEXT,
            last_updated TEXT
        )
    """)
    # Global Sign-Offs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sop_signoffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sop_id INTEGER,
            project_name TEXT,
            target_person TEXT,
            role TEXT,
            signoff_date TEXT,
            FOREIGN KEY(sop_id) REFERENCES company_sops(id)
        )
    """)
    conn.commit()
    
    # Seed initial Wickboldt Capital SOPs if empty
    cursor = conn.execute("SELECT COUNT(*) FROM company_sops")
    if cursor.fetchone()[0] == 0:
        initial_sops = [
            ("Structural Framing Standard", "Engineering & Architecture", "All residential and build-to-rent structures MUST strictly adhere to a maximum structural footprint width of 26 feet. Primary suite hallway routing must preserve contiguous square footage without bisection. Advanced Framing (OVE) at 24-inch O.C. is standard unless otherwise specified.", str(date.today())),
            ("HVAC Engineering Protocol", "Engineering & Architecture", "All HVAC systems must be explicitly designed utilizing ACCA Manual J (Load), Manual S (Equipment Selection), and Manual D (Duct Design). No rule-of-thumb sizing is permitted. Systems must integrate Brushless Direct Current (BLDC) ceiling fans in living areas for load offset.", str(date.today())),
            ("Jobsite PPE & OSHA Compliance", "Safety & Operations", "100% hard hat and safety glass utilization is required during active framing, roofing, and heavy machinery operation. Fall protection is strictly required for roof pitches exceeding 6:12 or any work above 6 feet.", str(date.today()))
        ]
        conn.executemany("INSERT INTO company_sops (title, category, content, last_updated) VALUES (?, ?, ?, ?)", initial_sops)
        conn.commit()
    conn.close()

init_sop_db()

def get_sops():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM company_sops ORDER BY category, title", conn)
    conn.close()
    return df

def get_signoffs():
    conn = sqlite3.connect(DB_FILE)
    
    # MULTI-TENANT ISOLATION LOGIC
    if role in ["Admin", "Manager"]:
        # Admins/Managers see all sign-offs across the portfolio
        query = """
            SELECT s.title AS SOP_Title, o.project_name AS Project, o.target_person AS Name, o.role AS Role, o.signoff_date AS Date 
            FROM sop_signoffs o
            JOIN company_sops s ON o.sop_id = s.id
            ORDER BY o.signoff_date DESC
        """
        df = pd.read_sql_query(query, conn)
    else:
        # Standard users only see sign-offs for their currently authorized active project
        query = """
            SELECT s.title AS SOP_Title, o.project_name AS Project, o.target_person AS Name, o.role AS Role, o.signoff_date AS Date 
            FROM sop_signoffs o
            JOIN company_sops s ON o.sop_id = s.id
            WHERE o.project_name = ?
            ORDER BY o.signoff_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(active_project,))
        
    conn.close()
    return df

st.header("📘 Master SOP & Training Library")
st.markdown("Centralize Wickboldt Capital standard operating procedures, field guidelines, and compliance sign-offs.")
st.divider()

# ==========================================
# ENTERPRISE WORKFLOW TABS
# ==========================================
tab_library, tab_lms, tab_admin = st.tabs([
    "1. 📚 SOP Knowledge Base", 
    "2. ✍️ Training & Compliance Sign-Offs", 
    "3. ⚙️ SOP Administration"
])

# ==========================================
# TAB 1: SOP KNOWLEDGE BASE
# ==========================================
with tab_library:
    st.subheader("Company Playbook & Guidelines")
    st.markdown("Review structural constraints, engineering protocols, and operational workflows.")
    
    sops_df = get_sops()
    if not sops_df.empty:
        categories = sops_df['category'].unique()
        for cat in categories:
            st.markdown(f"#### {cat}")
            cat_sops = sops_df[sops_df['category'] == cat]
            for _, row in cat_sops.iterrows():
                with st.expander(f"📄 {row['title']} (Updated: {row['last_updated']})"):
                    st.write(row['content'])
    else:
        st.info("No Standard Operating Procedures found.")

# ==========================================
# TAB 2: TRAINING & COMPLIANCE SIGN-OFFS (LMS)
# ==========================================
with tab_lms:
    st.subheader("Subcontractor & Employee Acknowledgments")
    st.markdown(f"Log training completion and protocol acknowledgment securely for **{active_project}**.")
    
    lms_col1, lms_col2 = st.columns([1, 2], gap="large")
    
    with lms_col1:
        st.markdown("**Record a Sign-Off**")
        with st.form("signoff_form", clear_on_submit=True):
            if not sops_df.empty:
                sop_options = dict(zip(sops_df['title'], sops_df['id']))
                selected_sop_title = st.selectbox("Select SOP Protocol", list(sop_options.keys()))
                target_name = st.text_input("Name of Person (Employee or Subcontractor)")
                target_role = st.selectbox("Role / Trade", ["Subcontractor Foreman", "Project Manager", "Site Superintendent", "Laborer", "Investor"])
                
                if st.form_submit_button("💾 Log Acknowledgment", type="primary"):
                    if target_name:
                        conn = sqlite3.connect(DB_FILE)
                        conn.execute("""
                            INSERT INTO sop_signoffs (sop_id, project_name, target_person, role, signoff_date) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (sop_options[selected_sop_title], active_project, target_name, target_role, str(date.today())))
                        conn.commit()
                        conn.close()
                        st.success(f"Sign-off logged for {target_name} on '{selected_sop_title}'.")
                        st.rerun()
                    else:
                        st.error("Please enter the name of the person acknowledging the SOP.")
            else:
                st.warning("No SOPs available to sign off on.")

    with lms_col2:
        st.markdown("**Historical Sign-Off Registry**")
        signoffs_df = get_signoffs()
        if not signoffs_df.empty:
            st.dataframe(signoffs_df, use_container_width=True, hide_index=True)
        else:
            st.info("No training sign-offs have been recorded for this project yet.")

# ==========================================
# TAB 3: SOP ADMINISTRATION (ADMIN ONLY)
# ==========================================
with tab_admin:
    if role in ["Admin", "Manager"]:
        st.subheader("⚙️ Draft & Publish New SOP")
        st.markdown("Create new company-wide guidelines and protocols.")
        
        with st.form("new_sop_form", clear_on_submit=True):
            new_title = st.text_input("SOP Title")
            new_category = st.selectbox("Category", [
                "Engineering & Architecture", 
                "Safety & Operations", 
                "Financial & Procurement", 
                "Quality Control & Inspections",
                "General Administration"
            ])
            new_content = st.text_area("SOP Content & Guidelines", height=200)
            
            if st.form_submit_button("🚀 Publish SOP to Company Library", type="primary"):
                if new_title and new_content:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("""
                        INSERT INTO company_sops (title, category, content, last_updated) 
                        VALUES (?, ?, ?, ?)
                    """, (new_title, new_category, new_content, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success(f"SOP '{new_title}' successfully published!")
                    st.rerun()
                else:
                    st.error("Title and Content are required to publish an SOP.")
                    
        st.divider()
        st.subheader("Manage Existing SOPs")
        if not sops_df.empty:
            st.dataframe(sops_df[["id", "category", "title", "last_updated"]], use_container_width=True, hide_index=True)
            st.caption("To delete or modify existing SOPs, access the database directly or build a dedicated update function.")
    else:
        st.error("🛑 Access Denied: Only Administrators and Managers can publish new Standard Operating Procedures.")