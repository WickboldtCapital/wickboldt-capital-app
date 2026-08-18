import streamlit as st
import sqlite3
import json
import os
from datetime import date

st.set_page_config(page_title="Due Diligence", layout="wide")

# ==========================================
# 🔒 SECURITY & MULTI-TENANT GATEKEEPER
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
    VAULT_DIR = "/app/data/project_vault"
else:
    DB_FILE = "wickboldt_projects.db"
    VAULT_DIR = "project_vault"

PROJECT_VAULT_PATH = os.path.join(VAULT_DIR, active_project.replace(" ", "_"))
os.makedirs(PROJECT_VAULT_PATH, exist_ok=True)

# ==========================================
# 💾 DB STATE HELPERS
# ==========================================
def get_db_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

def save_state(updated_dict):
    current_state = get_db_state()
    current_state.update(updated_dict)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
    conn.commit()
    conn.close()

db_state = get_db_state()

# Initialize DD Checklists if missing
if "dd_checklists" not in db_state:
    db_state["dd_checklists"] = {
        "Site & Zoning": {},
        "Legal & Title": {},
        "Engineering & Environmental": {}
    }

# Initialize Vault if missing
if "vault_docs" not in db_state:
    db_state["vault_docs"] = {
        "Blueprints & Engineering": [],
        "Permits & Municipal": [],
        "Legal & Corporate Deeds": []
    }

def toggle_dd_item(category, item_name):
    # Auto-save toggle states
    current_val = db_state["dd_checklists"][category].get(item_name, False)
    db_state["dd_checklists"][category][item_name] = not current_val
    save_state({"dd_checklists": db_state["dd_checklists"]})

# --- UI HEADER ---
st.title("🔍 Due Diligence & Feasibility")
st.markdown(f"**Active Workspace:** `{active_project}`")
st.markdown("Track pre-construction viability, municipal compliance, and title commitments. Documents uploaded here synchronize directly to the Master Vault.")
st.divider()

# ==========================================
# ENTERPRISE WORKFLOW TABS
# ==========================================
tab_site, tab_legal, tab_eng = st.tabs([
    "1. 🗺️ Site & Zoning", 
    "2. ⚖️ Legal & Title", 
    "3. 📐 Engineering & Environmental"
])

def render_dd_section(category, checklist_items, vault_target_category):
    """Renders the checklist and an integrated vault upload form for the specific DD phase."""
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.subheader(f"{category} Requirements")
        for item, description in checklist_items.items():
            checked = db_state["dd_checklists"][category].get(item, False)
            st.checkbox(
                f"**{item}** — {description}", 
                value=checked, 
                key=f"chk_{category}_{item}",
                on_change=toggle_dd_item,
                args=(category, item)
            )
            
    with col2:
        st.markdown(f"**Upload {category} Documentation**")
        st.caption(f"Files route to Master Vault: `{vault_target_category}`")
        with st.form(f"dd_upload_{category}", clear_on_submit=True):
            doc_title = st.text_input("Document Title (e.g., Boundary Survey, Phase 1 ESA)")
            uploaded_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "dwg", "zip"])
            
            if st.form_submit_button("💾 Save to Vault", type="primary"):
                if doc_title and uploaded_file:
                    # 1. Save Physical File to Disk
                    file_path = os.path.join(PROJECT_VAULT_PATH, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 2. Save Metadata to SQLite Vault
                    new_doc = {
                        "Title": doc_title,
                        "Filename": uploaded_file.name,
                        "Type": uploaded_file.type,
                        "Size (KB)": round(uploaded_file.size / 1024, 2),
                        "Upload Date": str(date.today()),
                        "Category": vault_target_category
                    }
                    db_state["vault_docs"][vault_target_category].append(new_doc)
                    save_state({"vault_docs": db_state["vault_docs"]})
                    st.success(f"'{doc_title}' physically uploaded and synced to the Master Vault.")
                else:
                    st.error("Please provide both a title and a file to upload.")

# ==========================================
# TAB 1: SITE & ZONING
# ==========================================
with tab_site:
    site_items = {
        "Boundary Survey": "Acquire stamped boundary and topographical survey.",
        "Zoning Verification": "Verify municipal zoning density limits (e.g., RS-3) and setbacks.",
        "Utility Availability": "Confirm municipal tap access for water, sewer, natural gas, and electrical.",
        "Flood Zone & Elevation": "Verify FEMA Base Flood Elevation (BFE). Note target finished floor elevations (e.g., 21.12 specification)."
    }
    render_dd_section("Site & Zoning", site_items, "Permits & Municipal")

# ==========================================
# TAB 2: LEGAL & TITLE
# ==========================================
with tab_legal:
    legal_items = {
        "Title Commitment": "Receive clean title commitment free of fatal encumbrances.",
        "HOA / Restrictive Covenants": "Review subdivision restrictions for minimum square footage or architectural limitations.",
        "Easement Verification": "Confirm structural footprints do not encroach on municipal or utility easements.",
        "Entity Formation": "Execute LLC operating agreements for the specific property holding entity."
    }
    render_dd_section("Legal & Title", legal_items, "Legal & Corporate Deeds")

# ==========================================
# TAB 3: ENGINEERING & ENVIRONMENTAL
# ==========================================
with tab_eng:
    eng_items = {
        "Phase 1 ESA": "Complete Phase 1 Environmental Site Assessment (if required by lender).",
        "Geotechnical Soils Report": "Boring logs and soil bearing capacity verification for foundation engineering.",
        "ACCA MEP Engineering": "Finalize Manual J/S/D calculations and IPC/NEC load modeling.",
        "Municipal Permit Submittal": "Submit finalized structural, MEP, and site plan packet to municipal planning council."
    }
    render_dd_section("Engineering & Environmental", eng_items, "Blueprints & Engineering")

st.divider()

# --- DD PROGRESS BAR ---
st.subheader("Due Diligence Completion Metrics")
total_items = len(site_items) + len(legal_items) + len(eng_items)
completed_items = 0
for cat in db_state["dd_checklists"]:
    completed_items += sum(db_state["dd_checklists"][cat].values())

progress = int((completed_items / total_items) * 100) if total_items > 0 else 0
st.progress(progress / 100)
st.metric("Checklist Progress", f"{progress}% ({completed_items}/{total_items})")