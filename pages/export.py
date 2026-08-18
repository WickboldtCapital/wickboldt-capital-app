import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import date
from fpdf import FPDF
import tempfile
import os
from db_ops import get_project_budget, get_project_milestones

st.set_page_config(page_title="Master Project Export", layout="wide")

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

# --- ENTERPRISE PERSISTENT STORAGE ROUTING ---
if os.path.exists("/app/data"):
    DB_FILE = "/app/data/wickboldt_projects.db"
else:
    DB_FILE = "wickboldt_projects.db"

# ==========================================
# DATA FETCHING HELPERS
# ==========================================
def get_lms_logs(project_name):
    df = pd.DataFrame()
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        df = pd.read_sql_query("SELECT worker_name, trade_company, course_name, completion_date FROM lms_training_logs WHERE project_name=?", conn, params=(project_name,))
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    return df

def get_vault_manifest(project_name):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (project_name,)).fetchone()
        if row and row[0]:
            p_data = json.loads(row[0])
            return p_data.get("vault_docs", {})
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    return {}

# ==========================================
# PDF GENERATOR CLASS
# ==========================================
class ProjectBible(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, 'Wickboldt Capital - Master Project Bible', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_bible():
    pdf = ProjectBible()
    pdf.add_page()
    
    # Title Page
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 20, active_project.upper(), 0, 1, 'C')
    pdf.set_font("Arial", '', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Enterprise Aggregation Report | Generated: {date.today()}", 0, 1, 'C')
    pdf.ln(10)
    
    # 1. Budget & Proforma
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "1. Financial Ledger & Budget", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    b_df = get_project_budget(active_project)
    if not b_df.empty and 'item_name' in b_df.columns and 'total_cost' in b_df.columns:
        total_budget = b_df['total_cost'].sum()
        pdf.cell(0, 10, f"Total Managed Budget: ${total_budget:,.2f}", 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(100, 8, "Line Item", 1, 0, 'C')
        pdf.cell(50, 8, "Cost", 1, 1, 'C')
        pdf.set_font("Arial", '', 10)
        
        for _, row in b_df.iterrows():
            pdf.cell(100, 8, str(row.get('item_name', 'N/A'))[:50], 1, 0, 'L')
            pdf.cell(50, 8, f"${row.get('total_cost', 0):,.2f}", 1, 1, 'R')
    else:
        pdf.cell(0, 10, "No budget data logged for this project.", 0, 1, 'L')
    pdf.ln(10)
    
    # 2. Schedule & Milestones
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "2. Schedule & Milestones", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    m_df = get_project_milestones(active_project)
    if not m_df.empty and 'milestone_name' in m_df.columns:
        completed = len(m_df[m_df.get('is_complete', 0) == 1])
        total_m = len(m_df)
        progress = int((completed / total_m) * 100) if total_m > 0 else 0
        pdf.cell(0, 10, f"Phase Completion: {progress}% ({completed}/{total_m} Milestones)", 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(100, 8, "Milestone", 1, 0, 'C')
        pdf.cell(50, 8, "Status", 1, 1, 'C')
        pdf.set_font("Arial", '', 10)
        
        for _, row in m_df.iterrows():
            status = "Completed" if row.get('is_complete', 0) == 1 else "Pending"
            pdf.cell(100, 8, str(row.get('milestone_name', 'N/A'))[:50], 1, 0, 'L')
            pdf.cell(50, 8, status, 1, 1, 'C')
    else:
        pdf.cell(0, 10, "No milestones scheduled for this project.", 0, 1, 'L')
    pdf.ln(10)
    
    # 3. Compliance & Training (LMS)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "3. Jobsite Compliance & Certifications", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    lms_df = get_lms_logs(active_project)
    if not lms_df.empty:
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(40, 8, "Worker", 1, 0, 'C')
        pdf.cell(40, 8, "Company", 1, 0, 'C')
        pdf.cell(80, 8, "Course", 1, 0, 'C')
        pdf.cell(30, 8, "Date", 1, 1, 'C')
        pdf.set_font("Arial", '', 9)
        
        for _, row in lms_df.iterrows():
            pdf.cell(40, 8, str(row.get('worker_name', ''))[:20], 1, 0, 'L')
            pdf.cell(40, 8, str(row.get('trade_company', ''))[:20], 1, 0, 'L')
            pdf.cell(80, 8, str(row.get('course_name', ''))[:40], 1, 0, 'L')
            pdf.cell(30, 8, str(row.get('completion_date', '')), 1, 1, 'C')
    else:
        pdf.cell(0, 10, "No active certifications logged for this project.", 0, 1, 'L')
    pdf.ln(10)

    # 4. Master Vault Manifest
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "4. Document Vault Manifest", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    vault = get_vault_manifest(active_project)
    has_docs = False
    for category, docs in vault.items():
        if docs:
            has_docs = True
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, category, 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            for doc in docs:
                pdf.cell(0, 6, f"- {doc.get('Title', 'Untitled')} ({doc.get('Filename', 'N/A')})", 0, 1, 'L')
            pdf.ln(4)
            
    if not has_docs:
        pdf.cell(0, 10, "No documents stored in the master vault.", 0, 1, 'L')

    # Output to temp file
    temp_path = os.path.join(tempfile.gettempdir(), f"Bible_{active_project.replace(' ', '_')}.pdf")
    pdf.output(temp_path)
    return temp_path

# ==========================================
# UI RENDERING
# ==========================================
st.title("🖨️ Master Project Export")
st.markdown(f"**Active Workspace:** `{active_project}`")
st.markdown("Compile all Proforma financials, Subcontractor compliance logs, Engineering schedules, and Document Vault manifests into a single, comprehensive PDF Bible for institutional lenders or internal archiving.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Generate PDF Bible")
    st.info("The generation process pulls real-time data from the SQLite database. Ensure all recent milestones and compliance logs are saved before generating.")
    
    if st.button("🚀 Compile Master Report", type="primary", use_container_width=True):
        with st.spinner("Aggregating project ledgers, compliance logs, and vault records..."):
            try:
                pdf_path = generate_pdf_bible()
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.session_state["pdf_bible_bytes"] = pdf_bytes
                st.success("Compilation successful!")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")

    if "pdf_bible_bytes" in st.session_state:
        st.download_button(
            label="📥 Download PDF Bible",
            data=st.session_state["pdf_bible_bytes"],
            file_name=f"{active_project.replace(' ', '_')}_Master_Bible.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="secondary"
        )

with col2:
    st.subheader("Report Contents")
    st.markdown("""
    **This master document automatically aggregates the following modules into a formalized report:**
    *   **Financial Ledger:** The complete Budget line items linked to the active workspace.
    *   **Schedule & Milestones:** Current project progression and critical path status.
    *   **Compliance & Certifications:** Multi-tenant isolated LMS records tracking safety and site sign-offs.
    *   **Document Vault Manifest:** A ledger mapping of all uploaded engineering blueprints, municipal permits, and corporate deeds linked to this site.
    """)