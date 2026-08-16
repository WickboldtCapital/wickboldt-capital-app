import streamlit as st
import pandas as pd

st.set_page_config(page_title="HVAC Engineering", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("❄️ HVAC Engineering (ACCA Specs)")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Manual J (Load)", "Manual S (Equipment)", "Manual D (Ducts)"])

# --- TAB 1: MANUAL J ---
with tab1:
    st.markdown("#### Manual J: Block Load Estimator")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Building Envelope**")
        sqft = st.number_input("Conditioned Square Footage", min_value=500, value=2200, step=100)
        ceiling_h = st.number_input("Average Ceiling Height (ft)", min_value=8, value=9, step=1)
        
        wall_insulation = st.selectbox(
            "Wall Assembly & Insulation", 
            ["2x4 Walls + Standard Insulation", "2x6 Walls + Standard Insulation", "2x4 Walls + Spray Foam", "2x6 Walls + Spray Foam"], 
            index=0
        )
        attic_type = st.radio("Attic / Roof Deck", ["Standard Vented Attic", "Conditioned Attic (Spray Foam)"])
        
    with c2:
        st.markdown("**Glazing & Orientation**")
        windows = st.number_input("Total Window Area (SqFt)", min_value=0, value=300, step=50)
        window_shgc = st.slider("Average Window SHGC", min_value=0.1, max_value=0.8, value=0.3, step=0.05)
        
    with c3:
        st.markdown("**Climate Design Conditions**")
        design_temp_out = st.number_input("Summer Design Temp (Outdoor °F)", value=95)
        design_temp_in = st.number_input("Summer Design Temp (Indoor °F)", value=72)
        occupants = st.number_input("Number of Occupants", min_value=1, value=4)

    base_multipliers = {"2x4 Walls + Standard Insulation": 32, "2x6 Walls + Standard Insulation": 28, "2x4 Walls + Spray Foam": 24, "2x6 Walls + Spray Foam": 20}
    multiplier = base_multipliers[wall_insulation]
    if attic_type == "Conditioned Attic (Spray Foam)":
        multiplier -= 4
    
    base_btu = sqft * multiplier
    window_load = windows * (window_shgc * 100)
    temp_delta = design_temp_out - design_temp_in
    delta_load = temp_delta * 150 
    
    infiltration_factor = 0.8 if "Spray Foam" in wall_insulation else 1.5
    latent_btu = (occupants * 200) + (sqft * infiltration_factor)
    
    total_sensible = base_btu + window_load + delta_load
    total_btu = total_sensible + latent_btu
    tonnage = total_btu / 12000

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Sensible Load", f"{total_sensible:,.0f} BTU/h")
    m2.metric("Total Latent Load", f"{latent_btu:,.0f} BTU/h")
    m3.metric("Total Cooling Load", f"{total_btu:,.0f} BTU/h")
    m4.metric("Required Equipment Size", f"{tonnage:.2f} Tons")

# --- TAB 2: MANUAL S ---
with tab2:
    st.markdown("#### Manual S: Equipment Verification")
    with st.form("manual_s_form"):
        scol1, scol2 = st.columns(2)
        with scol1:
            equip_type = st.selectbox("System Type", ["Standard Central AC / Heat Pump", "Ducted Mini-Split Heat Pump"])
            st.text_input("Manufacturer / Model Number")
            equip_tonnage = st.number_input("Nominal Tonnage (OEM)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
        with scol2:
            equip_sensible = st.number_input("OEM Rated Sensible Capacity (BTU/h)", value=28000, step=1000)
            equip_latent = st.number_input("OEM Rated Latent Capacity (BTU/h)", value=8000, step=1000)
            
        submitted = st.form_submit_button("Verify Equipment Match", type="primary")
        
        if submitted:
            total_equip_capacity = equip_sensible + equip_latent
            shr = equip_sensible / total_equip_capacity if total_equip_capacity > 0 else 0
            
            st.divider()
            res1, res2, res3 = st.columns(3)
            res1.metric("Total OEM Capacity", f"{total_equip_capacity:,.0f} BTU/h")
            res2.metric("Sensible Heat Ratio (SHR)", f"{shr:.2f}")
            
            oversize_pct = ((total_equip_capacity - total_btu) / total_btu) * 100 if total_btu > 0 else 0
            res3.metric("Oversize Margin", f"{oversize_pct:.1f}%", delta_color="inverse" if oversize_pct > 15 else "normal")
            
            if oversize_pct > 15:
                if "Mini-Split" in equip_type:
                    st.warning("⚠️ **Note:** Equipment is oversized, but inverter-driven ducted mini-splits can ramp down capacity. Ensure it hits low-stage CFM targets for dehumidification.")
                else:
                    st.error(f"⚠️ **Warning:** Standard single-stage equipment is oversized by {oversize_pct:.1f}%. This leads to short-cycling and poor dehumidification.")
            elif oversize_pct < 0:
                st.warning("⚠️ **Warning:** Equipment is undersized compared to the Manual J block load.")
            else:
                st.success("✅ **Pass:** Equipment is sized correctly for the envelope load.")

# --- TAB 3: MANUAL D ---
with tab3:
    st.markdown("#### Manual D: Duct Design & Airflow")
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.markdown("**System Airflow Target**")
        target_cfm_per_ton = st.number_input("Target CFM per Ton", min_value=300, max_value=450, value=400, step=10)
        total_cfm = equip_tonnage * target_cfm_per_ton if 'equip_tonnage' in locals() else tonnage * target_cfm_per_ton
        st.metric("Total System Airflow", f"{total_cfm:,.0f} CFM")
        
    with dcol2:
        st.markdown("**Static Pressure Allowances**")
        external_static = st.number_input("Available External Static Pressure (IWC)", value=0.50, step=0.05)
        coil_drop = st.number_input("Evaporator Coil Drop (IWC)", value=0.20, step=0.05)
        filter_drop = st.number_input("Filter Drop (IWC)", value=0.10, step=0.05)
        
        available_duct_esp = external_static - coil_drop - filter_drop
        st.metric("Available Static for Ductwork", f"{available_duct_esp:.2f} IWC")
        
        if available_duct_esp < 0.1:
            st.error("⚠️ **Warning:** Available static pressure for ductwork is critically low.")