import streamlit as st

if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: Administrator privileges required.")
    st.stop()

st.title("⚙️ Account Settings")
st.markdown("Manage global system configurations and administrative preferences.")
st.write(f"**Logged in Administrator:** `{st.session_state.get('email', 'N/A')}`")
st.write(f"**System Role:** `{st.session_state.get('role', 'N/A')}`")