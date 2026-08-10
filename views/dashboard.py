import streamlit as st

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please select a project first on the Control tab.")
    st.stop()

st.header("🏠 Executive Dashboard")
st.markdown(f"### Active Project: `{st.session_state['active_project']}`")

col1, col2, col3 = st.columns(3)
col1.metric("Active Development", st.session_state['active_project'], "Build-to-Rent")
col2.metric("Target Equity Position", "30.0%", "Standard Underwriting")
col3.metric("Narrow-Footprint Config", "3 Bed / 2 Bath", "Max Width: 26 ft")
