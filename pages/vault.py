import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import date

st.set_page_config(page_title="Master Document Vault", layout="wide")

# ==========================================
# 🔒 SECURITY & CONTEXT GUARDS
# ==========================================
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- DB HELPERS ---
def get_db_state():
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        pass
    return {}

def save_state(updated_dict):
    current_state = get_db_state()
    current_state.update(updated_dict)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
    conn.commit()
    conn.close()

db_state = get_db_state()

# Initialize vault structure if it doesn't exist
vault_docs = db_state.get("vault_docs", {
    "Blueprints & Engineering": [],
    "Permits & Municipal": [],
    "Legal & Corporate Deeds": []
})

st.header("🗄️ Master Document Vault")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Centralize project blueprints, municipal permits, and corporate deeds for Wickboldt Capital governance and lender compliance.")
st.divider()

# ==========================================
# ENTERPRISE WORKFLOW TABS
# ==========================================
tab_blueprints, tab_permits, tab_legal, tab_master = st.tabs([
    "1. 📐 Blueprints & Engineering", 
    "2. 🏛️ Permits & Municipal", 
    "3. ⚖️ Legal & Deeds", 
    "4. 🗂️ Master Archive"
])

def render_vault_tab(category, description, icon, example_docs):
    """Helper function to render the upload and display UI for a specific document category."""
    st.subheader(f"{icon} {category}")
    st.markdown(description)
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.markdown("**Upload New Document**")
        with st.form(f"upload_form_{category}", clear_on_submit=True):
            doc_title = st.text_input("Document Title / Description", placeholder=example_docs)
            uploaded_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "dwg", "zip"])
            
            if st.form_submit_button("💾 Save to Vault", type="primary"):
                if doc_title and uploaded_file:
                    new_doc = {
                        "Title": doc_title,
                        "Filename": uploaded_file.name,
                        "Type": uploaded_file.type,
                        "Size (KB)": round(uploaded_file.size / 1024, 2),
                        "Upload Date": str(date.today()),
                        "Category": category
                    }
                    vault_docs[category].append(new_doc)
                    save_state({"vault_docs": vault_docs})
                    st.success(f"'{doc_title}' saved successfully to {category}.")
                else:
                    st.error("Please provide both a title and a file to upload.")

    with col2:
        st.markdown(f"**{category} Archive**")
        if vault_docs[category]:
            df = pd.DataFrame(vault_docs[category])
            st.dataframe(
                df[["Title", "Filename", "Size (KB)", "Upload Date"]], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info(f"No documents currently stored in the {category} vault.")

# ==========================================
# TAB 1: BLUEPRINTS & ENGINEERING
# ==========================================
with tab_blueprints:
    render_vault_tab(
        "Blueprints & Engineering",
        "Store architectural plans, ACCA HVAC reports, and structural engineering sign-offs.",
        "📐",
        "e.g., Master Plot Plan, Manual J/S/D Submittal"
    )

# ==========================================
# TAB 2: PERMITS & MUNICIPAL
# ==========================================
with tab_permits:
    render_vault_tab(
        "Permits & Municipal",
        "Track zoning approvals, elevation certificates, and municipal utility tap documents.",
        "🏛️",
        "e.g., Building Permit Submittal, Final Elevation Certificate"
    )

# ==========================================
# TAB 3: LEGAL & CORPORATE DEEDS
# ==========================================
with tab_legal:
    render_vault_tab(
        "Legal & Corporate Deeds",
        "Safeguard land deeds, LLC operating agreements, and lender documentation.",
        "⚖️",
        "e.g., Warranty Deed, Bank Draw Schedule"
    )

# ==========================================
# TAB 4: MASTER ARCHIVE
# ==========================================
with tab_master:
    st.subheader("🗂️ Master Document Archive")
    st.markdown("A consolidated view of all critical files linked to this development project.")
    
    all_docs = []
    for cat, docs in vault_docs.items():
        all_docs.extend(docs)
        
    if all_docs:
        df_all = pd.DataFrame(all_docs)
        # Sort by Upload Date descending
        df_all = df_all.sort_values(by="Upload Date", ascending=False)
        st.dataframe(
            df_all[["Category", "Title", "Filename", "Size (KB)", "Upload Date"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        st.divider()
        st.metric("Total Vault Files", len(all_docs))
    else:
        st.info("The Master Vault is currently empty.")