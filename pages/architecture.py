import streamlit as st

st.set_page_config(page_title="Architecture & Master Specs", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("📐 Architecture & Master Specs")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Design Constraints & Methodologies")
    
    with st.expander("🏗️ Structural & Foundation", expanded=True):
        st.markdown("""
        * **Framing System:** Standard 2x4 or 2x6 timber framing.
        * **Thermal Envelope:** High-efficiency envelope utilizing spray foam or standard insulation with conditioned or vented attics.
        * **Footprint:** Maximum structural width of **26 feet** strictly enforced.
        """)
        
    with st.expander("📐 Floor Plan Configuration", expanded=True):
        st.markdown("""
        * **Layout Standard:** 3 Bedrooms / 2 Bathrooms.
        * **Primary Suite:** Hallway routing optimized to preserve contiguous primary bedroom square footage (no bisection).
        * **Target Strategy:** Build-to-Rent portfolio standardization.
        """)
        
with col2:
    st.info("💡 **Execution Note:** Any deviation from the 26ft width constraint or specified framing methodology requires direct corporate approval prior to municipal submission.")
    st.subheader("Site Plans")
    st.button("📄 View Master Plot Plan", use_container_width=True)
    st.button("📄 View Phase Lots (Color Coded)", use_container_width=True)