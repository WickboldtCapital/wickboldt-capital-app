import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Quality Control & Punch Lists", layout="wide")

# ==========================================
# 🔒 SECURITY GUARD
# ==========================================
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
qc_data = db_state.get("qc_data", {})

st.header("✅ Quality Control & Digital Punch-List")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Track phase-by-phase framing, MEP, and finish standards, manage subcontractor punch lists, and sync quality costs to your proforma.")
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

# --- ENTERPRISE WORKFLOW TABS ---
tab_checklists, tab_punch, tab_costs, tab_report = st.tabs([
    "1. Phase Checklists", 
    "2. Subcontractor Punch List", 
    "3. Quality Costs & Proforma Sync", 
    "4. Official Inspection Sign-Off"
])

# ==========================================
# TAB 1: PHASE CHECKLISTS (Your Exact Code)
# ==========================================
with tab_checklists:
    sub_tabs = st.tabs(list(qc_categories.keys()))

    for i, (category, items) in enumerate(qc_categories.items()):
        with sub_tabs[i]:
            st.subheader(category)
            
            with st.form(key=f"qc_form_{i}"):
                updated_category_data = {}
                
                for item in items:
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
                    for k, v in updated_category_data.items():
                        qc_data[k] = v
                    save_qc_state(qc_data)
                    st.success(f"{category} checklist saved successfully!")

# ==========================================
# TAB 2: SUBCONTRACTOR PUNCH LIST (Pillar 4)
# ==========================================
with tab_punch:
    st.subheader("🛠️ Deficiencies & Subcontractor Punch List")
    st.markdown("Isolated list of items marked as **Fail** or requiring corrective action, ready for subcontractor work orders.")
    
    failed_items = []
    for item_key, data in qc_data.items():
        if data.get("status") == "Fail":
            parts = item_key.split("_", 1)
            cat = parts[0] if len(parts) > 1 else "General"
            desc = parts[1] if len(parts) > 1 else item_key
            failed_items.append({
                "Category": cat,
                "Deficiency / Item": desc,
                "Inspector Notes": data.get("notes", "None"),
                "Assigned Trade": "Framing Sub" if "Framing" in cat else ("Plumbing/MEP Sub" if "MEP" in cat else "Finish Sub")
            })
            
    if failed_items:
        df_punch = pd.DataFrame(failed_items)
        st.dataframe(df_punch, use_container_width=True, hide_index=True)
        st.info("💡 **Action:** Export or print this table to issue formal punch-list work orders to respective subcontractors.")
    else:
        st.success("🟢 No active deficiencies or failed items found across inspections!")

# ==========================================
# TAB 3: QUALITY COSTS & PROFORMA SYNC (Pillar 2)
# ==========================================
with tab_costs:
    st.subheader("💰 Quality Control & Testing Hard Costs")
    st.markdown("Track third-party inspection fees, engineering sign-offs, and rework costs for Proforma integration.")
    
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        testing_fees = st.number_input("Third-Party Inspection & Testing Fees ($)", value=float(db_state.get("qc_testing_fees", 750.0)), step=50.0)
        rework_budget = st.number_input("Estimated Punch-List Rework Budget ($)", value=float(db_state.get("qc_rework_budget", 1200.0)), step=100.0)
    with q_col2:
        st.markdown("##### 📊 Cost Impact")
        total_qc_cost = testing_fees + rework_budget
        st.metric("Total Quality Control Budget", f"${total_qc_cost:,.2f}")
        st.info("Syncing this budget updates your master Proforma indirect/hard cost line items automatically.")

    if st.button("💾 Sync Quality Budget to Proforma & Database", type="primary"):
        current_state = get_db_state()
        current_state["qc_testing_fees"] = testing_fees
        current_state["qc_rework_budget"] = rework_budget
        
        if "estimates" not in current_state:
            current_state["estimates"] = {}
        current_state["estimates"]["Quality Control & Testing"] = total_qc_cost
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
        conn.commit()
        conn.close()
        st.toast("✅ QC testing and rework budget successfully synced to Proforma!")

# ==========================================
# TAB 4: OFFICIAL INSPECTION SIGN-OFF (Pillar 3)
# ==========================================
with tab_report:
    st.subheader("📋 Municipal & Lender Inspection Sign-Off Report")
    st.markdown("Formal quality compliance summary for building inspectors, lenders, and asset managers.")
    
    total_items = sum(len(items) for items in qc_categories.values())
    passed_items = sum(1 for data in qc_data.values() if data.get("status") == "Pass")
    failed_items = sum(1 for data in qc_data.values() if data.get("status") == "Fail")
    pending_items = total_items - (passed_items + failed_items)
    
    st.markdown(f"""
    ### Project Compliance Certificate Summary
    * **Development Project:** `{active_project}`
    * **Total Quality Checkpoints:** {total_items}
    * **Passed Standards:** {passed_items}
    * **Open Deficiencies (Fail):** {failed_items}
    * **Pending Inspections:** {pending_items}
    
    > **Certification Statement:** All structural width constraints (maximum 26 feet), thermal envelope specifications, MEP engineering alignments (ACCA Manual J/S/D & IPC standards), and finish protocols have been audited per Wickboldt Capital corporate standards.
    """)
    
    if failed_items == 0 and pending_items == 0:
        st.success("🎉 **Status: Fully Compliant & Certified Ready for Final Occupancy / Closing.**")
    else:
        st.warning("⚠️ **Status: Pending Resolution of Open Deficiencies.**")

# --- PROJECT COMPLETION METRICS FOOTER ---
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