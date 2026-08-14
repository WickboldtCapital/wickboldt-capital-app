import streamlit as st
from db_ops import get_library_state

if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: You must be logged in as an Administrator to view this page.")
    st.stop()

st.title("🏢 Master Company Library & Governance")
st.markdown("Central repository for corporate bylaws, real estate templates, and Wickboldt Capital standard operating procedures.")
st.divider()

library_data = get_library_state()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📋 Corporate Governance")
    st.info("Bylaws and operating agreements")
    st.markdown(f"[📄 Operating Agreement](/?view_doc=Wickboldt+Capital+LLC+-+Operating+Agreement)", unsafe_allow_html=True)
    st.markdown(f"[📄 Board Resolutions](/?view_doc=Board+Resolutions)", unsafe_allow_html=True)

with col2:
    st.markdown("### 🏗️ Master Templates")
    st.info("Standardized Wickboldt execution documents")
    st.markdown(f"[📄 Subcontractor Agreement](/?view_doc=Master+Subcontractor+Agreement)", unsafe_allow_html=True)
    st.markdown(f"[📄 Scope of Work Template](/?view_doc=Master+Scope+of+Work)", unsafe_allow_html=True)

with col3:
    st.markdown("### 🏦 Financial Standards")
    st.info("Underwriting and Draw protocols")
    st.markdown(f"[📄 Draw Schedule Standards](/?view_doc=Standard+Draw+Schedule)", unsafe_allow_html=True)
    st.markdown(f"[📄 Cost Code Master List](/?view_doc=Master+Cost+Codes)", unsafe_allow_html=True)

st.divider()
st.subheader("Raw Library Database Check")
with st.expander("View Available Document Keys in Database"):
    st.json(list(library_data.keys()))