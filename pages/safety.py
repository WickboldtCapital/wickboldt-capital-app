import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import date

st.set_page_config(page_title="Jobsite Safety", layout="wide")

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
toolbox_talks = db_state.get("toolbox_talks", [])
osha_data = db_state.get("osha_data", {})

st.header("🦺 Jobsite Safety & OSHA Compliance")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Log daily toolbox talks, enforce OSHA compliance checklists, and track safety budgets for Proforma integration.")
st.divider()

# ==========================================
# ENTERPRISE WORKFLOW TABS (FOUR PILLARS)
# ==========================================
tab_talks, tab_osha, tab_cost, tab_report = st.tabs([
    "1. 🗣️ Daily Toolbox Talks", 
    "2. 📋 OSHA Compliance",
    "3. 💰 Safety Budget & Sync",
    "4. 📋 Compliance Certificate"
])

# ==========================================
# TAB 1: TOOLBOX TALKS LOGGER (Your Exact Code)
# ==========================================
with tab_talks:
    st.subheader("Log a New Toolbox Talk")
    
    with st.form("toolbox_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            talk_date = st.date_input("Date", value=date.today())
            foreman = st.text_input("Foreman / Supervisor Name")
            attendees = st.number_input("Number of Attendees", min_value=1, step=1)
        with col2:
            topic = st.selectbox("Safety Topic", [
                "Heat Illness & Hydration (Critical)", 
                "Fall Protection (> 6ft)", 
                "PPE & Hard Hats", 
                "Electrical Safety & GFCI", 
                "Trenching & Excavation", 
                "Scaffolding & Ladders", 
                "Housekeeping & Debris"
            ])
            notes = st.text_area("Discussion Notes / Concerns Raised")
            
        submit_talk = st.form_submit_button("💾 Save Toolbox Talk", type="primary")
        
        if submit_talk:
            new_log = {
                "Date": str(talk_date),
                "Topic": topic,
                "Foreman": foreman,
                "Attendees": attendees,
                "Notes": notes
            }
            toolbox_talks.append(new_log)
            save_state({"toolbox_talks": toolbox_talks})
            st.success("Toolbox Talk logged successfully!")

    st.divider()
    st.subheader("Historical Safety Logs")
    if toolbox_talks:
        # Sort by date descending
        sorted_talks = sorted(toolbox_talks, key=lambda x: x["Date"], reverse=True)
        st.dataframe(pd.DataFrame(sorted_talks), use_container_width=True, hide_index=True)
    else:
        st.info("No toolbox talks logged for this project yet.")

# ==========================================
# TAB 2: OSHA COMPLIANCE CHECKLIST (Your Exact Code)
# ==========================================
with tab_osha:
    st.subheader("Standard Site Safety Checks")
    st.markdown("Ensure site compliance with OSHA residential construction standards.")
    
    osha_categories = {
        "Personal Protective Equipment (PPE)": [
            "Hard hats worn by all personnel under overhead hazards",
            "Safety glasses worn during cutting, grinding, and nailing",
            "Proper high-visibility clothing worn around heavy equipment"
        ],
        "Fall Protection & Ladders": [
            "Fall protection systems active for framing/roofing > 6 feet",
            "Ladders extend at least 3 feet above landing surface and are secured",
            "Scaffolding fully planked and equipped with guardrails"
        ],
        "Electrical & Site Work": [
            "GFCI protection used for all temporary power circuits",
            "Extension cords free from cuts, splices, or frayed insulation",
            "Trenches 5+ feet deep are properly shored, sloped, or shielded",
            "Underground utilities (Louisiana One Call / 811) marked and respected",
            "Jobsite free of trip hazards, nails bent/removed from scrap lumber"
        ]
    }

    with st.form(key="osha_form"):
        updated_osha_data = {}
        
        for category, items in osha_categories.items():
            st.markdown(f"#### {category}")
            for item in items:
                item_key = f"osha_{item}"
                existing_status = osha_data.get(item_key, "Pending")
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(item)
                with c2:
                    status = st.radio(
                        "Status", 
                        ["Pending", "Pass", "Fail", "N/A"], 
                        index=["Pending", "Pass", "Fail", "N/A"].index(existing_status),
                        key=f"status_{item_key}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                updated_osha_data[item_key] = status
            st.markdown("---")
            
        submit_osha = st.form_submit_button(label="💾 Save Compliance Checklist", type="primary")
        
        if submit_osha:
            save_state({"osha_data": updated_osha_data})
            st.success("OSHA Compliance Checklist updated!")

# ==========================================
# TAB 3: SAFETY BUDGET & PROFORMA SYNC (Enterprise Pillar 2)
# ==========================================
with tab_cost:
    st.subheader("Safety Equipment & Compliance Budgeting")
    st.markdown("Estimate hard costs for jobsite safety equipment to sync into your Proforma indirect budget.")
    
    scol1, scol2 = st.columns(2)
    with scol1:
        ppe_budget = st.number_input("PPE Station, Vests, Hard Hats & Glasses ($)", value=350.0, step=50.0)
        first_aid_budget = st.number_input("OSHA-Compliant First Aid Kits & Eye Wash ($)", value=200.0, step=25.0)
        signage_budget = st.number_input("Jobsite Safety & Warning Signage ($)", value=250.0, step=25.0)
    with scol2:
        fencing_budget = st.number_input("Temporary Safety Fencing & Barricades ($)", value=1200.0, step=100.0)
        extinguishers_budget = st.number_input("Jobsite Fire Extinguishers ($)", value=150.0, step=25.0)
        
        total_safety_cost = ppe_budget + first_aid_budget + signage_budget + fencing_budget + extinguishers_budget

    st.divider()
    st.metric("💰 Total Jobsite Safety Budget", f"${total_safety_cost:,.2f}")

    if st.button("💾 Sync Safety Budget to Proforma & Project Database", type="primary", use_container_width=True):
        try:
            current_state = get_db_state()
            if "estimates" not in current_state:
                current_state["estimates"] = {}
            current_state["estimates"]["Jobsite Safety & Compliance"] = total_safety_cost
            save_state({"estimates": current_state["estimates"]})
            st.toast("✅ Safety budget synced to Proforma master ledger!")
        except Exception as e:
            st.error(f"Database error: {e}")

# ==========================================
# TAB 4: OSHA COMPLIANCE CERTIFICATE (Enterprise Pillar 3)
# ==========================================
with tab_report:
    st.subheader("📋 OSHA Jobsite Compliance Summary")
    st.markdown("Printable compliance summary confirming adherence to OSHA standards for lender risk management.")
    
    total_checks = len(osha_data) if osha_data else sum(len(items) for items in osha_categories.values())
    passed_checks = sum(1 for status in osha_data.values() if status == "Pass")
    failed_checks = sum(1 for status in osha_data.values() if status == "Fail")
    pending_checks = sum(1 for status in osha_data.values() if status == "Pending")
    
    st.markdown(f"""
    ### Safety Record Verification
    * **Project Development:** `{active_project}`
    * **Total Safety Checkpoints Audited:** {total_checks}
    * **Passed Items Verified:** {passed_checks}
    * **Active Violations (Fail):** {failed_checks}
    * **Pending Inspections:** {pending_checks}
    
    > **Indemnification & Safety Policy:** Wickboldt Capital enforces strict adherence to 29 CFR OSHA standards across all active builds. All trade partners and subcontractors are contractually required to maintain hazard-free working conditions and provide certified PPE.
    """)
    
    if failed_checks == 0 and passed_checks > 0:
        st.success("🟢 **Jobsite Safety Status:** Fully compliant with audited safety standards.")
    elif failed_checks > 0:
        st.warning(f"⚠️ **Attention Required:** {failed_checks} safety violation(s) identified. Immediate corrective action required.")
    else:
        st.info("🔄 **Status:** Audits pending.")