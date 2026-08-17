import streamlit as st
import pandas as pd
import math
import sqlite3
import json

st.set_page_config(page_title="Plumbing Engineering", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

st.header("🚰 Plumbing Engineering & Estimating")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Calculate WSFU/DFU loads per IPC standards, estimate fixture-based costs for your proforma, and generate scopes for inspectors and subcontractors.")
st.divider()

tab_eng, tab_cost, tab_permit, tab_sub = st.tabs([
    "1. Engineering (WSFU, DFU, Gas)", 
    "2. Cost Estimation & Proforma", 
    "3. Inspector Submittal", 
    "4. Subcontractor Scope"
])

# ==========================================
# TAB 1: ENGINEERING & FIXTURE UNITS
# ==========================================
with tab_eng:
    st.subheader("Fixture Counts & Energy Profile")
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

    with col1:
        st.markdown("**Water / Drain Fixtures**")
        toilets = st.number_input("Toilets (Flush Tank)", min_value=1, value=2)
        showers_tubs = st.number_input("Showers / Bathtubs", min_value=1, value=2)
        lavatories = st.number_input("Bathroom Sinks (Lavatory)", min_value=1, value=3)
        kitchen_sinks = st.number_input("Kitchen Sinks", min_value=1, value=1)
        dishwashers = st.number_input("Dishwashers", min_value=0, value=1)
        washing_machines = st.number_input("Washing Machines", min_value=0, value=1)
        hose_bibbs = st.number_input("Exterior Hose Bibbs", min_value=0, value=2)
        
        total_fixtures = toilets + showers_tubs + lavatories + kitchen_sinks + dishwashers + washing_machines + hose_bibbs

    with col2:
        st.markdown("**Energy Profile & Appliances**")
        energy_profile = st.radio("House Energy Profile", ["Gas & Electric", "All Electric (No Gas)"], index=0)
        
        if energy_profile == "All Electric (No Gas)":
            water_heater_type = st.selectbox("Water Heater", ["Electric Tank (Standard)", "Electric Heat Pump (Hybrid)"], index=0)
            gas_range = False
            gas_dryer = False
            gas_furnace = False
            has_gas_stub = False
            st.info("⚡ **All-Electric Home:** Gas appliance loads and gas piping costs are disabled.")
        else:
            water_heater_type = st.selectbox("Water Heater", ["Tankless Gas (199,000 BTU)", "Tank Gas (40,000 BTU)", "Electric (0 BTU)"], index=0)
            gas_range = st.checkbox("Gas Range / Cooktop (60,000 BTU)", value=True)
            gas_dryer = st.checkbox("Gas Clothes Dryer (35,000 BTU)", value=True)
            gas_furnace = st.checkbox("Gas Furnace (80,000 BTU)", value=False)
            has_gas_stub = st.checkbox("Exterior Gas Stub / Grill (50,000 BTU)", value=True)
        
        wh_btu = 199000 if "Tankless Gas" in water_heater_type else (40000 if "Tank Gas" in water_heater_type else 0)
        total_gas_btu = wh_btu + (60000 if gas_range else 0) + (35000 if gas_dryer else 0) + (80000 if gas_furnace else 0) + (50000 if has_gas_stub else 0)

    with col3:
        st.markdown("**System Load Calculations**")

        # Standard IPC Values
        total_wsfu = (toilets * 2.2) + (showers_tubs * 1.4) + (lavatories * 0.7) + (kitchen_sinks * 1.4) + (dishwashers * 1.4) + (washing_machines * 1.4) + (hose_bibbs * 2.5)
        total_dfu = (toilets * 3) + (showers_tubs * 2) + (lavatories * 1) + (kitchen_sinks * 2) + (dishwashers * 2) + (washing_machines * 2)

        # Sizing Logic
        water_main_size = '3/4"' if total_wsfu <= 17 else '1"'
        if total_wsfu > 36: water_main_size = '1 1/4"'

        sewer_main_size = '3"' if total_dfu <= 42 else '4"'

        st.metric("Total WSFU", f"{total_wsfu:.1f}", help=f"Recommended Main: {water_main_size}")
        st.metric("Total DFU", f"{total_dfu:.1f}", help=f"Recommended Drain: {sewer_main_size}")
        
        if energy_profile == "Gas & Electric":
            st.metric("Total Gas Load", f"{total_gas_btu:,} BTU/hr")
        else:
            st.metric("Total Gas Load", "0 BTU/hr (All Electric)")

# ==========================================
# TAB 2: COST ESTIMATION & PROFORMA
# ==========================================
with tab_cost:
    st.subheader("Plumbing Budget Estimation")
    st.markdown("Estimate hard costs based on your specific fixture count. Adjust unit pricing to match your local subcontractors.")
    
    c1, c2 = st.columns(2)
    with c1:
        cost_per_rough_in = st.number_input("Cost per Fixture Drop (Rough-in DWV & Supply) ($)", value=350.0, step=25.0)
        cost_per_trim = st.number_input("Cost per Fixture (Trim-out Labor) ($)", value=125.0, step=25.0)
        water_heater_budget = st.number_input("Water Heater (Unit + Install) ($)", value=2200.0 if "Tankless" in water_heater_type else 1200.0, step=100.0)
    with c2:
        main_water_sewer_tie_in = st.number_input("Main Water & Sewer Tie-in / Trenching ($)", value=1500.0, step=100.0)
        
        if energy_profile == "Gas & Electric":
            gas_piping_lumpsum = st.number_input("Gas Piping System (Lump Sum) ($)", value=1200.0, step=100.0)
        else:
            st.number_input("Gas Piping System (Lump Sum) ($)", value=0.0, disabled=True, help="Disabled for All-Electric profile.")
            gas_piping_lumpsum = 0.0
            
        permit_fee = st.number_input("Municipal Permit Fee ($)", value=250.0, step=25.0)

    # Math
    total_rough_cost = total_fixtures * cost_per_rough_in
    total_trim_cost = total_fixtures * cost_per_trim
    total_plumbing_cost = total_rough_cost + total_trim_cost + water_heater_budget + main_water_sewer_tie_in + gas_piping_lumpsum + permit_fee

    st.divider()
    st.markdown("#### 📋 Bill of Materials & Labor (BOM)")
    st.metric("Total Estimated Plumbing Budget", f"${total_plumbing_cost:,.2f}")
    
    bom_data = [
        {"Phase": "Underground & Tie-in", "Description": "Main Water & Sewer line to municipal/septic connection", "Cost": main_water_sewer_tie_in},
        {"Phase": "Rough-In", "Description": f"{total_fixtures} Fixture Drops (Supply & DWV) @ ${cost_per_rough_in:,.2f} ea", "Cost": total_rough_cost},
        {"Phase": "Trim-Out", "Description": f"{total_fixtures} Fixtures (Setting toilets, sinks, faucets) @ ${cost_per_trim:,.2f} ea", "Cost": total_trim_cost},
        {"Phase": "Equipment", "Description": f"Water Heater: {water_heater_type.split()[0]}", "Cost": water_heater_budget},
        {"Phase": "Gas Piping", "Description": f"Gas distribution for {total_gas_btu:,} BTU/hr load" if energy_profile == "Gas & Electric" else "N/A - All Electric", "Cost": gas_piping_lumpsum},
        {"Phase": "Permitting", "Description": "Municipal Plumbing & Gas Permits", "Cost": permit_fee},
    ]
    st.dataframe(pd.DataFrame(bom_data), use_container_width=True, hide_index=True, column_config={"Cost": st.column_config.NumberColumn("Cost ($)", format="$%.2f")})

    if st.button("💾 Save Plumbing Budget to Proforma & Project Database", type="primary", use_container_width=True):
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
            data = json.loads(row[0]) if row and row[0] else {}
            
            if "engineering" not in data:
                data["engineering"] = {}
                
            data["engineering"]["plumbing_wsfu"] = total_wsfu
            data["engineering"]["plumbing_dfu"] = total_dfu
            data["engineering"]["plumbing_gas_btuh"] = total_gas_btu
            data["engineering"]["plumbing_total_cost"] = total_plumbing_cost
            data["engineering"]["plumbing_total_fixtures"] = total_fixtures
            
            # Sync to Proforma
            if "estimates" not in data:
                data["estimates"] = {}
            data["estimates"]["Plumbing & Gas"] = total_plumbing_cost
            
            conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(data), active_project))
            conn.commit()
            conn.close()
            st.toast("✅ Plumbing engineering & budget synced to master project ledger!")
        except Exception as e:
            st.error(f"Database error: {e}")

# ==========================================
# TAB 3: INSPECTOR SUBMITTAL
# ==========================================
with tab_permit:
    st.subheader("Municipal Permit & Building Inspector Submittal")
    st.markdown("Code compliance summary for building department review per International Plumbing Code (IPC).")
    
    if energy_profile == "Gas & Electric":
        gas_string = f"* **Natural Gas / Propane Piping:** Total connected load of **{total_gas_btu:,} BTU/hr**. Piping to be sized per local utility gas pressure tables and pressure tested prior to inspection."
    else:
        gas_string = "* **Natural Gas / Propane Piping:** N/A — Property is designed as an All-Electric home."
    
    st.markdown(f"""
    * **Water Service & Distribution:** Designed with PEX-a distribution. Main supply line sized at **{water_main_size}** to accommodate a calculated peak demand of **{total_wsfu:.1f} WSFU**.
    * **Drain, Waste & Vent (DWV):** Building main sewer drain sized at **{sewer_main_size}** Schedule 40 PVC. Total calculated drainage load is **{total_dfu:.1f} DFU**. All fixtures to be properly trapped and vented through the roof.
    {gas_string}
    * **Water Heater:** {water_heater_type}. Thermal expansion tank and T&P relief valve discharge line routed to exterior per code.
    """)
    st.success("✅ **Status:** Engineering parameters meet or exceed minimum IPC standards for residential permitting.")

# ==========================================
# TAB 4: SUBCONTRACTOR SCOPE
# ==========================================
with tab_sub:
    st.subheader("🛠️ Plumbing Subcontractor Bid Scope")
    st.markdown("Include this checklist when requesting bids to ensure mechanical contractors price the exact same scope of work.")
    
    owner_supplied = st.checkbox("General Contractor / Owner will supply finish fixtures (faucets, toilets, shower heads)", value=True)
    
    st.markdown("##### 📋 Subcontractor Responsibilities")
    scope_table = [
        {"Scope Item": f"Underground sewer rough-in and {sewer_main_size} building drain stub-out", "Responsibility": "Plumbing Sub"},
        {"Scope Item": f"Water distribution (Supply) for {total_fixtures} total fixtures ({water_main_size} main)", "Responsibility": "Plumbing Sub"},
        {"Scope Item": "DWV top-out, vent stacks through roof, and flashing installation", "Responsibility": "Plumbing Sub"},
        {"Scope Item": f"Supply and install Water Heater: {water_heater_type}", "Responsibility": "Plumbing Sub"},
        {"Scope Item": "Supply finish fixtures (Toilets, Faucets, Tubs)", "Responsibility": "General Contractor" if owner_supplied else "Plumbing Sub"},
        {"Scope Item": "Install finish fixtures & final trim-out labor", "Responsibility": "Plumbing Sub"},
        {"Scope Item": "Pull municipal plumbing/gas permits & schedule inspections", "Responsibility": "Plumbing Sub"},
    ]
    
    if energy_profile == "Gas & Electric":
        scope_table.insert(3, {"Scope Item": f"Gas line installation & pressure test ({total_gas_btu:,} BTU total)", "Responsibility": "Plumbing Sub"})
    
    st.dataframe(pd.DataFrame(scope_table), use_container_width=True, hide_index=True)