import streamlit as st

st.set_page_config(page_title="Electrical Engineering", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("⚡ Electrical Engineering & Panel Loads")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Calculate residential service panel loads and verify main breaker sizing using the NEC Article 220 Standard Method.")
st.divider()

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
    
    # 2. Small Appliance & Laundry Branch Circuits (Required by NEC)
    # 2 Kitchen circuits @ 1500VA each, 1 Laundry @ 1500VA
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
    
    # Color code the panel recommendation
    if panel_rec == "200 Amp Panel":
        m3.metric("Recommended Main Service", panel_rec)
    else:
        m3.metric("Recommended Main Service", panel_rec, delta="Upgrading to 200A recommended for EV charging", delta_color="normal")