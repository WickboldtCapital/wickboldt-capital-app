import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date

st.set_page_config(page_title="AI Bid Ingestion", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- ENSURE DATABASE TABLE EXISTS ---
def init_budgets_table():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS project_budgets (
                    id TEXT PRIMARY KEY,
                    project_name TEXT,
                    created_at TEXT,
                    category TEXT,
                    vendor_name TEXT,
                    description TEXT,
                    qty REAL,
                    unit_cost REAL,
                    total_cost REAL
                )''')
    conn.commit()
    conn.close()

init_budgets_table()

st.header("🤖 AI Bid Ingestion & Parsing")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Upload contractor bids and supplier invoices to extract real-world hard costs directly into your Proforma budget.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

# ==========================================
# LEFT COLUMN: UPLOAD & PARSE
# ==========================================
with col1:
    st.subheader("Upload Invoice / Bid")
    uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' staged for AI parsing.")
        if st.button("🧠 Parse Document with AI", type="primary", use_container_width=True):
            with st.spinner("Extracting line items and financial data..."):
                # Simulating AI extraction payload for the UI
                st.session_state["parsed_bid"] = {
                    "vendor_name": "Acme Building Supply (Auto-Detected)",
                    "category": "Framing, Exterior Shell & Roof",
                    "description": "Lumber Package - 2x4s, OSB, and Roof Trusses",
                    "qty": 1.0,
                    "unit_cost": 12500.00,
                    "total_cost": 12500.00
                }
            st.success("Extraction Complete! Review data before committing to the master budget.")

# ==========================================
# RIGHT COLUMN: REVIEW & COMMIT
# ==========================================
with col2:
    st.subheader("Review & Commit to Master Budget")
    if "parsed_bid" in st.session_state:
        with st.form("commit_bid_form"):
            st.info("Please verify the AI-extracted data below before saving it to the project ledger.")
            vendor = st.text_input("Vendor / Contractor", value=st.session_state["parsed_bid"]["vendor_name"])
            category = st.selectbox("Cost Category", [
                "Site Work, Foundation & Civil Grading",
                "Framing, Exterior Shell & Roof",
                "MEP Rough-Ins",
                "Interior Finishes & Drywall",
                "Build Contingency"
            ], index=1)
            desc = st.text_input("Line Item Description", value=st.session_state["parsed_bid"]["description"])
            
            c1, c2, c3 = st.columns(3)
            qty = c1.number_input("Quantity", value=st.session_state["parsed_bid"]["qty"])
            unit_cost = c2.number_input("Unit Cost ($)", value=st.session_state["parsed_bid"]["unit_cost"])
            total_cost = c3.number_input("Total Cost ($)", value=st.session_state["parsed_bid"]["total_cost"])
            
            if st.form_submit_button("💾 Commit to Project Budget", type="primary"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute(
                    "INSERT INTO project_budgets (id, project_name, created_at, category, vendor_name, description, qty, unit_cost, total_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), active_project, str(date.today()), category, vendor, desc, qty, unit_cost, total_cost)
                )
                conn.commit()
                conn.close()
                st.success("Bid successfully committed! The Proforma will now dynamically reflect this actual cost.")
                del st.session_state["parsed_bid"]
                st.rerun()
    else:
        st.info("Upload and parse a document on the left to review extracted data here.")

st.divider()

# ==========================================
# BOTTOM: INGESTED LEDGER
# ==========================================
st.subheader("Current Hard Cost Ledger (Ingested)")
conn = sqlite3.connect(DB_FILE)
df_budgets = pd.read_sql_query("SELECT created_at, category, vendor_name, description, total_cost FROM project_budgets WHERE project_name=?", conn, params=(active_project,))
conn.close()

if not df_budgets.empty:
    st.dataframe(df_budgets, use_container_width=True, hide_index=True)
    st.metric("Total Ingested Costs", f"${df_budgets['total_cost'].sum():,.2f}")
else:
    st.caption("No costs ingested yet. Upload your first bid to start populating the ledger.")