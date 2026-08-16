import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Foundation & Concrete", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("🧱 Foundation, Site & Concrete Engineering")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Calculate concrete yardage, track site elevations, and manage rebar requirements.")
st.divider()

tab1, tab2, tab3 = st.tabs(["Site Elevations & Fill", "Concrete Yardage Estimator", "Rebar & Steel Reinforcement"])

# ==========================================
# TAB 1: SITE ELEVATIONS & FILL
# ==========================================
with tab1:
    st.subheader("Site Elevation & Flood Compliance (BFE)")
    st.markdown("Track Base Flood Elevation (BFE) requirements for FEMA 50% Rule and municipal permitting.")
    
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.markdown("**Current Site Topography**")
        current_elevation = st.number_input("Average Existing Ground Elevation (ft)", value=17.00, step=0.10)
        
    with ecol2:
        st.markdown("**Municipal & FEMA Targets**")
        bfe = st.number_input("Base Flood Elevation (BFE) (ft)", value=20.00, step=0.10)
        freeboard = st.number_input("Required Freeboard (ft)", value=1.12, step=0.10)
        
    target_elevation = bfe + freeboard
    required_fill_height = target_elevation - current_elevation if target_elevation > current_elevation else 0
    
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Target Final Elevation", f"{target_elevation:.2f} ft", help="BFE + Freeboard (e.g., 21.12 ft target)")
    m2.metric("Required Fill / Lift", f"{required_fill_height:.2f} ft")
    m3.metric("FEMA Status", "Compliant ✅" if target_elevation >= (bfe + freeboard) else "Non-Compliant ❌")

# ==========================================
# TAB 2: CONCRETE YARDAGE ESTIMATOR
# ==========================================
with tab2:
    st.subheader("Concrete Yardage Calculator")
    st.markdown("Estimate total cubic yards required for monolithic slabs, footings, and grade beams.")
    
    ccol1, ccol2, ccol3 = st.columns(3)
    with ccol1:
        st.markdown("**Slab Dimensions**")
        slab_length = st.number_input("Slab Length (ft)", min_value=0.0, value=60.0, step=1.0)
        slab_width = st.number_input("Slab Width (ft)", min_value=0.0, value=26.0, step=1.0, help="Max 26ft footprint enforced.")
        slab_thickness = st.number_input("Slab Thickness (inches)", min_value=0.0, value=4.0, step=0.5)
        
    with ccol2:
        st.markdown("**Footings & Grade Beams**")
        footing_length = st.number_input("Total Linear Feet of Footings (ft)", min_value=0.0, value=172.0, step=1.0)
        footing_width = st.number_input("Footing Width (inches)", min_value=0.0, value=12.0, step=1.0)
        footing_depth = st.number_input("Footing Depth (inches)", min_value=0.0, value=24.0, step=1.0)
        
    with ccol3:
        st.markdown("**Ordering Allowances**")
        waste_factor = st.slider("Waste / Over-pour Buffer (%)", min_value=0, max_value=20, value=10, step=1)
        
    # Math
    slab_cu_ft = slab_length * slab_width * (slab_thickness / 12)
    footing_cu_ft = footing_length * (footing_width / 12) * (footing_depth / 12)
    total_cu_ft = slab_cu_ft + footing_cu_ft
    total_cu_yards = total_cu_ft / 27
    ordered_yards = math.ceil(total_cu_yards * (1 + (waste_factor / 100)))
    
    st.divider()
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Slab Volume", f"{slab_cu_ft / 27:.1f} Cu Yds")
    res2.metric("Footing Volume", f"{footing_cu_ft / 27:.1f} Cu Yds")
    res3.metric("Total Exact Volume", f"{total_cu_yards:.1f} Cu Yds")
    res4.metric("Total to Order (with Waste)", f"{ordered_yards} Cu Yds")

# ==========================================
# TAB 3: REBAR & STEEL
# ==========================================
with tab3:
    st.subheader("Rebar & Reinforcement Layout")
    
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        rebar_size = st.selectbox("Rebar Size", ["#3 (3/8\")", "#4 (1/2\")", "#5 (5/8\")"], index=1)
        grid_spacing = st.selectbox("Grid Spacing (O.C.)", ["12 inches", "16 inches", "18 inches", "24 inches"], index=1)
        
    with rcol2:
        spacing_val = int(grid_spacing.split()[0])
        # Grid math: (Length / spacing) * Width + (Width / spacing) * Length
        runs_lengthwise = math.ceil(slab_width / (spacing_val / 12)) + 1
        runs_widthwise = math.ceil(slab_length / (spacing_val / 12)) + 1
        
        linear_feet_length = runs_lengthwise * slab_length
        linear_feet_width = runs_widthwise * slab_width
        total_linear_feet = linear_feet_length + linear_feet_width
        
        st.metric("Estimated Rebar Required (Slab Grid)", f"{total_linear_feet:,.0f} Linear Feet")
        
        # 20ft stick equivalent
        sticks_20ft = math.ceil(total_linear_feet / 20)
        st.metric("Equivalent 20ft Sticks", f"{sticks_20ft} Sticks")