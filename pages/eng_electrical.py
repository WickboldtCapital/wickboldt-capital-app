import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Electrical Engineering", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

st.header("⚡ Electrical Engineering & Estimating")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Calculate residential service panel loads, establish granular material/labor budgets, and generate scopes for inspectors and subcontractors.")
st.divider()

# ==========================================
# TABS FOR ENTERPRISE WORKFLOW
# ==========================================
tab_eng, tab_cost, tab_permit, tab_sub = st.tabs([
    "1. NEC Load Calculation", 
    "2. Cost Estimation & Proforma", 
    "3. Inspector Submittal", 
    "4. Subcontractor Scope"
])

# ==========================================
# TAB 1: ENGINEERING & NEC LOAD CALC
# ==========================================
with tab_eng:
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.subheader("Home Parameters")
        sq_ft = st.number_input("Conditioned Living Area (SqFt)", min_value=500, value=1150, step=50)
        
        st.subheader("Major Appliances (Volt-Amperes)")
        heating_cooling_va = st.number_input("HVAC System (VA)", min_value=0, value=5000, step=500, help="e.g., 5000 VA for a standard 3-ton Heat Pump")
        water_heater_va = st.number_input("Water Heater (VA)", min_value=0, value=4500, step=500, help="Enter 0 if using Natural Gas")
        range_oven_va = st.number_input("Range / Oven (VA)", min_value=0, value=8000, step=500, help="Enter 0 if using Natural Gas")
        dryer_va = st.number_input("Electric Dryer (VA)", min_value=0, value=5000, step=500, help="Enter 0 if using Natural Gas")

    with col2:
        st.subheader("NEC Standard Load Calculation")
        
        # 1. General Lighting & Receptacles (3 VA per sq ft)
        gen_lighting_va = sq_ft * 3
        
        # 2. Small Appliance & Laundry Branch Circuits
        small_appliance_va = 4500 
        
        total_general_va = gen_lighting_va + small_appliance_va
        
        # 3. Demand Factor Application (First 3000 VA at 100%, remainder at 35%)
        if total_general_va > 3000:
            net_general_va = 3000 + ((total_general_va - 3000) * 0.35)
        else:
            net_general_va = total_general_va
            
        # 4. Total Projected VA
        total_projected_va = net_general_va + heating_cooling_va + water_heater_va + range_oven_va + dryer_va
        
        # 5. Required Amperage (Total VA / 240 Volts)
        required_amps = total_projected_va / 240
        
        # 6. Panel Recommendation
        if required_amps <= 100:
            panel_rec = "100 Amp Panel"
        elif required_amps <= 150:
            panel_rec = "150 Amp Panel"
        else:
            panel_rec = "200 Amp Panel"

        # Display Breakdown
        st.markdown("#### Demand Factors & Adjustments")
        st.text(f"General Lighting & Receptacles: {gen_lighting_va:,.0f} VA")
        st.text(f"Small Appliance/Laundry Circuits: {small_appliance_va:,.0f} VA")
        st.text(f"Net General Load (after Demand Factor): {net_general_va:,.0f} VA")
        
        st.divider()
        
        st.markdown("#### Final Service Sizing")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Load (VA)", f"{total_projected_va:,.0f} VA")
        m2.metric("Calculated Amperage", f"{required_amps:.1f} Amps", help="Divided by 240V Service")
        
        if panel_rec == "200 Amp Panel":
            m3.metric("Recommended Main Service", panel_rec)
        else:
            m3.metric("Recommended Main Service", panel_rec, delta="Upgrading to 200A recommended for EV charging", delta_color="normal")

# ==========================================
# TAB 2: COST ESTIMATION & PROFORMA (GRANULAR)
# ==========================================
with tab_cost:
    st.subheader("Granular Electrical Budget Estimation")
    st.markdown("Control the exact material and labor costs for each phase of the electrical installation.")
    
    # Set dynamic defaults based on Tab 1
    default_panel_mat = 1200.0 if panel_rec == "200 Amp Panel" else 800.0
    default_panel_lab = 1300.0 if panel_rec == "200 Amp Panel" else 1000.0
    
    default_rough_mat = sq_ft * 1.50
    default_rough_lab = sq_ft * 3.00
    
    # Grid Header
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    c1.markdown("**Construction Phase / Item**")
    c2.markdown("**Material Cost ($)**")
    c3.markdown("**Labor Cost ($)**")
    c4.markdown("**Total Cost ($)**")
    
    st.divider()
    
    # Row 1: Temp Power
    r1c1, r1c2, r1c3, r1c4 = st.columns([3, 2, 2, 2])
    r1c1.markdown("**Temporary Power Pole**")
    mat_temp = r1c2.number_input("Mat: Temp", value=150.0, step=50.0, label_visibility="collapsed")
    lab_temp = r1c3.number_input("Lab: Temp", value=300.0, step=50.0, label_visibility="collapsed")
    total_temp = mat_temp + lab_temp
    r1c4.markdown(f"**${total_temp:,.2f}**")
    
    # Row 2: Service Panel
    r2c1, r2c2, r2c3, r2c4 = st.columns([3, 2, 2, 2])
    r2c1.markdown(f"**Main Service ({panel_rec}) & Feed**")
    mat_panel = r2c2.number_input("Mat: Panel", value=default_panel_mat, step=100.0, label_visibility="collapsed")
    lab_panel = r2c3.number_input("Lab: Panel", value=default_panel_lab, step=100.0, label_visibility="collapsed")
    total_panel = mat_panel + lab_panel
    r2c4.markdown(f"**${total_panel:,.2f}**")
    
    # Row 3: Rough-In
    r3c1, r3c2, r3c3, r3c4 = st.columns([3, 2, 2, 2])
    r3c1.markdown(f"**Rough-In Wiring ({sq_ft:,.0f} SqFt)**")
    mat_rough = r3c2.number_input("Mat: Rough", value=float(default_rough_mat), step=100.0, label_visibility="collapsed")
    lab_rough = r3c3.number_input("Lab: Rough", value=float(default_rough_lab), step=100.0, label_visibility="collapsed")
    total_rough = mat_rough + lab_rough
    r3c4.markdown(f"**${total_rough:,.2f}**")
    
    # Row 4: Trim Out
    r4c1, r4c2, r4c3, r4c4 = st.columns([3, 2, 2, 2])
    r4c1.markdown("**Trim-Out (Devices & Plates)**")
    mat_trim = r4c2.number_input("Mat: Trim", value=500.0, step=50.0, label_visibility="collapsed")
    lab_trim = r4c3.number_input("Lab: Trim", value=1000.0, step=100.0, label_visibility="collapsed")
    total_trim = mat_trim + lab_trim
    r4c4.markdown(f"**${total_trim:,.2f}**")
    
    # Row 5: Fixtures
    r5c1, r5c2, r5c3, r5c4 = st.columns([3, 2, 2, 2])
    r5c1.markdown("**Light Fixtures & Ceiling Fans**")
    mat_fix = r5c2.number_input("Mat: Fix", value=2000.0, step=250.0, label_visibility="collapsed")
    lab_fix = r5c3.number_input("Lab: Fix", value=500.0, step=100.0, label_visibility="collapsed")
    total_fix = mat_fix + lab_fix
    r5c4.markdown(f"**${total_fix:,.2f}**")
    
    # Row 6: Permits
    r6c1, r6c2, r6c3, r6c4 = st.columns([3, 2, 2, 2])
    r6c1.markdown("**Municipal Permit Fees**")
    mat_permit = r6c2.number_input("Fee: Permit", value=250.0, step=25.0, label_visibility="collapsed")
    lab_permit = r6c3.number_input("Lab: Permit", value=0.0, disabled=True, label_visibility="collapsed")
    total_permit = mat_permit
    r6c4.markdown(f"**${total_permit:,.2f}**")
    
    # Totals Calculation
    total_material = mat_temp + mat_panel + mat_rough + mat_trim + mat_fix + mat_permit
    total_labor = lab_temp + lab_panel + lab_rough + lab_trim + lab_fix + lab_permit
    total_electrical_cost = total_material + total_labor
    
    st.divider()
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Material Cost", f"${total_material:,.2f}")
    t2.metric("Total Labor Cost", f"${total_labor:,.2f}")
    t3.metric("Total Electrical Budget", f"${total_electrical_cost:,.2f}")

    if st.button("💾 Save Electrical Budget to Proforma & Project Database", type="primary", use_container_width=True):
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
            data = json.loads(row[0]) if row and row[0] else {}
            
            if "engineering" not in data:
                data["engineering"] = {}
                
            data["engineering"]["elec_calc_amps"] = required_amps
            data["engineering"]["elec_main_service"] = panel_rec
            data["engineering"]["elec_total_cost"] = total_electrical_cost
            
            # Sync to Proforma
            if "estimates" not in data:
                data["estimates"] = {}
            data["estimates"]["Electrical"] = total_electrical_cost
            
            conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(data), active_project))
            conn.commit()
            conn.close()
            st.toast("✅ Electrical engineering & budget synced to master project ledger!")
        except Exception as e:
            st.error(f"Database error: {e}")

# ==========================================
# TAB 3: INSPECTOR SUBMITTAL
# ==========================================
with tab_permit:
    st.subheader("Municipal Permit & Inspector Submittal")
    st.markdown("NEC Article 220 Load Calculation summary for the local building department.")
    
    st.markdown(f"""
    ### Electrical Load Calculation (Standard Method)
    **Property Footprint:** {sq_ft:,.0f} Sq Ft  

    * **General Lighting & Receptacles (3 VA/SqFt):** {gen_lighting_va:,.0f} VA
    * **Kitchen & Laundry Circuits (3 @ 1,500 VA):** {small_appliance_va:,.0f} VA
    * **Net General Load (First 3kVA @ 100%, Remainder @ 35%):** {net_general_va:,.0f} VA
    * **HVAC / Heat Pump Load:** {heating_cooling_va:,.0f} VA
    * **Water Heater Load:** {water_heater_va:,.0f} VA
    * **Range / Oven Load:** {range_oven_va:,.0f} VA
    * **Electric Dryer Load:** {dryer_va:,.0f} VA
    ---
    * **Total Calculated Volt-Amperes:** **{total_projected_va:,.0f} VA**
    * **Total Amperage at 240V:** **{required_amps:.1f} Amps**
    
    ### Service Panel Declaration
    Based on the NEC Standard Load Calculation, a **{panel_rec} Main Service Panel** is required and specified for this dwelling. All GFCI, AFCI, and tamper-resistant receptacle requirements will conform to the latest adopted National Electrical Code.
    """)
    st.success("✅ **Code Compliance Status:** Ready for municipal electrical permit plan review.")

# ==========================================
# TAB 4: SUBCONTRACTOR SCOPE
# ==========================================
with tab_sub:
    st.subheader("🛠️ Electrical Subcontractor Bid Scope")
    st.markdown("Include this checklist when requesting bids to ensure electricians price the exact same scope of work.")
    
    owner_supplied = st.checkbox("General Contractor / Owner will supply all decorative light fixtures and ceiling fans", value=True)
    trenching_resp = st.selectbox("Underground Service Trenching Responsibility", ["Electrical Subcontractor", "Site Work / Excavation Subcontractor", "Utility Company"])
    
    st.markdown("##### 📋 Subcontractor Responsibilities")
    scope_table = [
        {"Scope Item": "Install temporary construction power pole & setup utility account", "Responsibility": "Electrical Sub"},
        {"Scope Item": f"Furnish and install {panel_rec} Main Breaker Panel & Grounding system", "Responsibility": "Electrical Sub"},
        {"Scope Item": f"Underground trenching & conduit to utility transformer", "Responsibility": trenching_resp},
        {"Scope Item": "Complete house rough-in wiring per local code (AFCI/GFCI protection)", "Responsibility": "Electrical Sub"},
        {"Scope Item": f"Dedicated 240V circuits for HVAC and heavy appliances", "Responsibility": "Electrical Sub"},
        {"Scope Item": "Supply and install standard devices (receptacles, switches, cover plates)", "Responsibility": "Electrical Sub"},
        {"Scope Item": "Supply decorative light fixtures and ceiling fans", "Responsibility": "General Contractor" if owner_supplied else "Electrical Sub"},
        {"Scope Item": "Hang/install all light fixtures, fans, and final trims", "Responsibility": "Electrical Sub"},
        {"Scope Item": "Pull municipal electrical permits & schedule inspections", "Responsibility": "Electrical Sub"},
    ]
    
    st.dataframe(pd.DataFrame(scope_table), use_container_width=True, hide_index=True)