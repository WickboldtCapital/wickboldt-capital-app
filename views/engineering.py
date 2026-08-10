import streamlit as st

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("📐 Engineering & Architectural Specs")
st.markdown(f"**Active Development:** `{st.session_state['active_project']}`")
st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Design Constraints & Methodologies")
    with st.expander("🏗️ Structural & Foundation", expanded=True):
        st.markdown("* **Foundation/Wall System:** Insulated Concrete Form (ICF) utilization (Mikey Block protocol).\n* **Thermal Mass:** High-efficiency envelope designed for long-term hold.\n* **Footprint:** Maximum structural width of **26 feet** strictly enforced.")
    with st.expander("📐 Floor Plan Configuration", expanded=True):
        st.markdown("* **Layout Standard:** 3 Bedrooms / 2 Bathrooms.\n* **Primary Suite:** Hallway routing optimized to preserve contiguous primary bedroom square footage (no bisection).\n* **Target Strategy:** Build-to-Rent portfolio standardization.")
    with st.expander("⚡ MEP Systems", expanded=True):
        st.markdown("* **HVAC Design Protocol:** Full system adherence to ACCA Manuals **J, S, D, and T** based on the design brief.\n* **Load Calculations:** Scaled for ICF thermal performance.")
with col2:
    st.info("💡 **Execution Note:** Any deviation from the 26ft width constraint or ICF methodology requires direct corporate approval prior to municipal submission.")
    st.subheader("Site Plans")
    st.button("📄 View Master Plot Plan", use_container_width=True)
    st.button("📄 View Phase Lots (Color Coded)", use_container_width=True)
