import streamlit as st
import math

st.set_page_config(page_title="Plumbing Engineering", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("🚰 Plumbing Engineering & Fixture Units")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Calculate Water Supply Fixture Units (WSFU), Drainage Fixture Units (DFU), and service line sizing based on standard IPC definitions.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Fixture Counts")
    toilets = st.number_input("Toilets (Flush Tank)", min_value=1, value=2)
    showers_tubs = st.number_input("Showers / Bathtubs", min_value=1, value=2)
    lavatories = st.number_input("Bathroom Sinks (Lavatory)", min_value=1, value=3)
    kitchen_sinks = st.number_input("Kitchen Sinks", min_value=1, value=1)
    dishwashers = st.number_input("Dishwashers", min_value=0, value=1)
    washing_machines = st.number_input("Washing Machines", min_value=0, value=1)
    hose_bibbs = st.number_input("Exterior Hose Bibbs", min_value=0, value=2)

with col2:
    st.subheader("System Load Calculations")
    
    # Standard IPC Values
    # WSFU: Toilet=2.2, Shower=1.4, Lav=0.7, Sink=1.4, DW=1.4, Washer=1.4, Hose=2.5
    # DFU: Toilet=3, Shower=2, Lav=1, Sink=2, DW=2, Washer=2
    
    total_wsfu = (toilets * 2.2) + (showers_tubs * 1.4) + (lavatories * 0.7) + (kitchen_sinks * 1.4) + (dishwashers * 1.4) + (washing_machines * 1.4) + (hose_bibbs * 2.5)
    total_dfu = (toilets * 3) + (showers_tubs * 2) + (lavatories * 1) + (kitchen_sinks * 2) + (dishwashers * 2) + (washing_machines * 2)
    
    # Sizing Logic
    water_main_size = '3/4"' if total_wsfu <= 17 else '1"'
    if total_wsfu > 36: water_main_size = '1 1/4"'
    
    sewer_main_size = '3"' if total_dfu <= 42 else '4"'

    st.markdown("#### Water Supply Fixture Units (WSFU)")
    w1, w2 = st.columns(2)
    w1.metric("Total WSFU", f"{total_wsfu:.1f}")
    w2.metric("Recommended Minimum Water Main", water_main_size, help="Based on standard IPC velocity thresholds")
    
    st.divider()
    
    st.markdown("#### Drainage Fixture Units (DFU)")
    d1, d2 = st.columns(2)
    d1.metric("Total DFU", f"{total_dfu:.1f}")
    d2.metric("Recommended Minimum Building Drain", sewer_main_size, help="Based on standard 1/4 inch per foot slope")