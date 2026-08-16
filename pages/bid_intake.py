import streamlit as st
import pandas as pd
import sqlite3
import uuid
from datetime import date
import time

st.set_page_config(page_title="AI Bid Ingestion", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- ENSURE DATABASE TABLE EXISTS ---
def init_budgets_table():
    try:
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
    except Exception as e:
        st.error(f"Database initialization error: {e}")

init_budgets_table()

st.header("🤖 AI Bid Ingestion & Parsing")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Upload contractor bids and supplier invoices to extract real-world hard costs directly into your project ledger.")
st.divider()

col1, col2 = st.columns([1, 2.5], gap="large")

# ==========================================
# LEFT COLUMN: UPLOAD & PARSE
# ==========================================
with col1:
    st.subheader("Upload Invoice / Bid")
    uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' staged for parsing.")
        
        # We assign a key to the button to prevent double-clicks
        if st.button("🧠 Parse Document with AI", type="primary", use_container_width=True, key="parse_btn"):
            with st.spinner("Extracting line items and financial data..."):
                time.sleep(1.5) # Simulate API call latency
                
                # Upgraded: Simulating a multi-line item extraction payload
                mock_extraction = pd.DataFrame([
                    {"Category": "Framing, Exterior Shell & Roof", "Description": "Lumber Package - 2x4s and OSB", "Qty": 1.0, "Unit Cost": 8500.00, "Total Cost": 8500.00},
                    {"Category": "Framing, Exterior Shell & Roof", "Description": "Engineered Roof Trusses", "Qty": 1.0, "Unit Cost": 4000.00, "Total Cost": 4000.00},
                    {"Category": "Site Work, Foundation & Civil Grading", "Description": "Concrete Slab Pour (Labor)", "Qty": 1.0, "Unit Cost": 3200.00, "Total Cost": 3200.00}
                ])
                
                st.session_state["parsed_vendor"] = "Acme Building Supply & Concrete (Auto-Detected)"
                st.session_state["parsed_bid_df"] = mock_extraction
            st.rerun()

# ==========================================
# RIGHT COLUMN: REVIEW & COMMIT (MULTI-LINE)
# ==========================================
with col2:
    st.subheader("Review & Commit to Master Budget")
    
    if "parsed_bid_df" in st.session_state:
        st.info("Please verify the AI-extracted line items below. You can edit cells directly before committing to the ledger.")
        
        vendor = st.text_input("Vendor / Contractor", value=st.session_state.get("parsed_vendor", "Unknown Vendor"))
        
        # Interactive Data Editor for multiple line items
        edited_df = st.data_editor(
            st.session_state["parsed_bid_df"],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "Cost Category",
                    help="Assign this cost to a Master Proforma bucket",
                    options=[
                        "Site Work, Foundation & Civil Grading",
                        "Framing, Exterior Shell & Roof",
                        "MEP Rough-Ins",
                        "Interior Finishes & Drywall",
                        "Build Contingency"
                    ],
                    required=True
                ),
                "Unit Cost": st.column_config.NumberColumn("Unit Cost ($)", format="$%.2f"),
                "Total Cost": st.column_config.NumberColumn("Total Cost ($)", format="$%.2f")
            }
        )
        
        total_extracted = edited_df["Total Cost"].sum()
        st.write(f"**Total Verified Amount:** ${total_extracted:,.2f}")
        
        # Commit & Cancel Buttons
        c_commit, c_cancel = st.columns([2, 1])
        with c_commit:
            if st.button("💾 Commit Verified Items to Ledger", type="primary", use_container_width=True):
                try:
                    conn = sqlite3.connect(DB_FILE)
                    today_str = str(date.today())
                    
                    # Iterate through the edited dataframe and insert each row
                    for index, row in edited_df.iterrows():
                        conn.execute(
                            "INSERT INTO project_budgets (id, project_name, created_at, category, vendor_name, description, qty, unit_cost, total_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (str(uuid.uuid4()), active_project, today_str, row['Category'], vendor, row['Description'], row['Qty'], row['Unit Cost'], row['Total Cost'])
                        )
                    conn.commit()
                    conn.close()
                    
                    st.success("Line items successfully committed! The Proforma will now dynamically reflect these actual costs.")
                    del st.session_state["parsed_bid_df"]
                    del st.session_state["parsed_vendor"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving to database: {e}")
                    
        with c_cancel:
            if st.button("Cancel / Clear", type="secondary", use_container_width=True):
                del st.session_state["parsed_bid_df"]
                del st.session_state["parsed_vendor"]
                st.rerun()
                
    else:
        st.info("Upload and parse a document on the left to review extracted line items here.")

st.divider()

# ==========================================
# BOTTOM: INGESTED LEDGER
# ==========================================
st.subheader("Current Hard Cost Ledger (Ingested)")
try:
    conn = sqlite3.connect(DB_FILE)
    df_budgets = pd.read_sql_query("SELECT created_at, category, vendor_name, description, total_cost FROM project_budgets WHERE project_name=?", conn, params=(active_project,))
    conn.close()

    if not df_budgets.empty:
        # Display with proper formatting
        st.dataframe(
            df_budgets, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "created_at": "Date Added",
                "category": "Master Category",
                "vendor_name": "Vendor/Contractor",
                "description": "Line Item Description",
                "total_cost": st.column_config.NumberColumn("Total Cost ($)", format="$%.2f")
            }
        )
        st.metric("Total Ingested Costs", f"${df_budgets['total_cost'].sum():,.2f}")
    else:
        st.caption("No costs ingested yet. Upload your first bid to start populating the ledger.")
except Exception as e:
    st.error(f"Error loading ledger: {e}")