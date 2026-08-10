import streamlit as st
if not st.session_state.get("active_project"):
    st.warning("Please select a project first.")
    st.stop()
st.header("Proforma Module")
