import streamlit as st
import sqlite3
import json

st.set_page_config(page_title="Quality Control", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- DB HELPERS ---
def get_db_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

def save_qc_state(qc_data):
    current_state = get_db_state()
    current_state["qc_data"] = qc_data
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
    conn.commit()
    conn.close()

db_state = get_db_state()
# Initialize QC data if it doesn't exist
qc_data = db_state.get("qc_data", {})

st.header("✅ Quality Control & Digital Punch-List")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Track phase-by-phase framing, MEP, and finish standards to ensure portfolio consistency.")
st.divider()

# --- WICKBOLDT CAPITAL STANDARD QC ITEMS ---
qc_categories = {
    "Framing & Structural": [
        "Maximum structural footprint width strictly 26 feet verified",
        "2x4 or 2x6 exterior wall assemblies plumb, square, and secured",
        "Primary suite hallway routing preserves contiguous square footage (no bisection)",
        "Roof trusses/rafters installed at correct spacing and pitch",
        "Exterior sheathing and house wrap fully sealed without tears"
    ],
    "MEP & Insulation": [
        "Natural gas supply lines installed and pressure tested successfully",
        "HVAC system equipment and ductwork matches ACCA Manual J, S, and D specs",
        "Spray foam or standard batt insulation installed evenly without voids",
        "Attic assembly (vented or conditioned) sealed and compliant",
        "Plumbing supply (WSFU) and drainage (DFU) mains sized correctly"
    ],
    "Finishes & Hardware": [
        "Brushless Direct Current (BLDC) ceiling fans mounted and balanced in living/beds",
        "LVP main flooring and wet-area tile installed with correct transitions",
        "Kitchen and bath cabinetry level; countertops secured",
        "All interior/exterior door hardware and window blinds installed correctly",
        "Final paint walk-through complete (no flashing or holidays)"
    ]
}

# --- TABS FOR PHASES ---
tabs = st.tabs(list(qc_categories.keys()))

for i, (category, items) in enumerate(qc_categories.items()):
    with tabs[i]:
        st.subheader(category)
        
        # We use a form to prevent the page from refreshing on every single radio button click
        with st.form(key=f"qc_form_{i}"):
            updated_category_data = {}
            
            for item in items:
                # Retrieve existing state or default to "Pending"
                item_key = f"{category}_{item}"
                existing_status = qc_data.get(item_key, {}).get("status", "Pending")
                existing_notes = qc_data.get(item_key, {}).get("notes", "")
                
                c1, c2 = st.columns([3, 2])
                with c1:
                    st.markdown(f"**{item}**")
                    status = st.radio(
                        "Status", 
                        ["Pending", "Pass", "Fail", "N/A"], 
                        index=["Pending", "Pass", "Fail", "N/A"].index(existing_status),
                        key=f"status_{item_key}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                with c2:
                    notes = st.text_input("Inspector Notes", value=existing_notes, key=f"notes_{item_key}", placeholder="Add notes or deficiencies...")
                
                st.markdown("---")
                updated_category_data[item_key] = {"status": status, "notes": notes}
            
            submit_button = st.form_submit_button(label="💾 Save Checklist Updates", type="primary")
            
            if submit_button:
                # Update the master qc_data dictionary with the new form values
                for k, v in updated_category_data.items():
                    qc_data[k] = v
                save_qc_state(qc_data)
                st.success(f"{category} checklist saved successfully!")

# --- PROJECT COMPLETION METRICS ---
st.divider()
st.subheader("📊 QC Progress Overview")

total_items = sum(len(items) for items in qc_categories.values())
passed_items = sum(1 for data in qc_data.values() if data.get("status") == "Pass")
failed_items = sum(1 for data in qc_data.values() if data.get("status") == "Fail")

p1, p2, p3 = st.columns(3)
p1.metric("Total QC Checks", total_items)
p2.metric("Passed Inspections", passed_items)
p3.metric("Deficiencies (Fail)", failed_items, delta="Needs Attention" if failed_items > 0 else "All Clear", delta_color="inverse" if failed_items > 0 else "normal")

if total_items > 0:
    progress = passed_items / total_items
    st.progress(progress)
    if progress == 1.0:
        st.success("🎉 All Quality Control checks have passed. This project is ready for final delivery.")