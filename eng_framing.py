import streamlit as st
import math

st.set_page_config(page_title="Structural Framing", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

st.header("🪵 Structural Framing & Lumber Takeoffs")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Estimate lumber packages, studs, plates, and sheathing based on your specific building envelope constraints.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Building Dimensions")
    st.info("💡 **Constraint Reminder:** Max footprint width is 26 feet.")
    
    building_length = st.number_input("Building Length (ft)", min_value=10.0, value=60.0, step=1.0)
    building_width = st.number_input("Building Width (ft)", min_value=10.0, max_value=26.0, value=26.0, step=1.0)
    wall_height = st.selectbox("Wall Height / Stud Length", ["8 ft (92-5/8\")", "9 ft (104-5/8\")", "10 ft (116-5/8\")"], index=1)
    
    st.subheader("Framing Specs")
    stud_spacing = st.selectbox("Stud Spacing (O.C.)", ["16 inches", "24 inches"], index=0)
    exterior_walls = st.selectbox("Exterior Wall Depth", ["2x4", "2x6"], index=0)
    
    interior_lf = st.number_input("Estimated Interior Wall Length (Linear Feet)", min_value=0.0, value=150.0, step=10.0)
    waste_factor = st.slider("Lumber Waste Buffer (%)", min_value=0, max_value=25, value=15, step=1)

with col2:
    st.subheader("Takeoff Estimates")
    
    # Mathematical Calculations
    exterior_lf = (building_length * 2) + (building_width * 2)
    total_lf = exterior_lf + interior_lf
    
    spacing_val = 16 if "16" in stud_spacing else 24
    
    # Studs: 1 stud per spacing interval + 1 for start + ~3 per corner/intersection (simplified estimation)
    base_studs = math.ceil(total_lf / (spacing_val / 12))
    corner_intersection_allowance = math.ceil((exterior_lf / 10) * 3) # rough allowance for corners and tees
    total_studs_exact = base_studs + corner_intersection_allowance
    total_studs_order = math.ceil(total_studs_exact * (1 + (waste_factor / 100)))
    
    # Plates: 3 plates total per wall (1 bottom plate, 2 top plates)
    plate_lf_exact = total_lf * 3
    plate_board_length = 16 # Assuming ordering 16ft boards for plates
    total_plates_exact = math.ceil(plate_lf_exact / plate_board_length)
    total_plates_order = math.ceil(total_plates_exact * (1 + (waste_factor / 100)))
    
    # Exterior Sheathing (4x8 OSB/Plywood)
    sqft_wall_surface = exterior_lf * int(wall_height.split()[0])
    sheets_exact = sqft_wall_surface / 32 # 32 sqft per 4x8 sheet
    sheets_order = math.ceil(sheets_exact * (1 + (waste_factor / 100)))
    
    st.markdown("#### 🌲 Wall Framing (Studs & Plates)")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Wall Studs ({exterior_walls})", f"{total_studs_order} pcs", help="Includes waste factor and corners")
    m2.metric("Plates (16ft boards)", f"{total_plates_order} pcs", help="Single bottom, double top")
    m3.metric("Exterior Sheathing (4x8)", f"{sheets_order} sheets", help="OSB/ZIP System or Plywood")
    
    st.divider()
    
    st.markdown("#### 🏠 Roof / Ceiling")
    # Trusses are typically 24" O.C. or 16" O.C. span the width
    truss_spacing = 24 # Standard roof truss spacing
    total_trusses = math.ceil(building_length / (truss_spacing / 12)) + 1
    
    # Roof sheathing (Simplified assuming a 6/12 pitch for square footage multiplier ~ 1.12)
    roof_sqft_flat = building_length * building_width
    roof_sqft_pitched = roof_sqft_flat * 1.12 
    roof_sheets_exact = roof_sqft_pitched / 32
    roof_sheets_order = math.ceil(roof_sheets_exact * (1 + (waste_factor / 100)))
    
    r1, r2 = st.columns(2)
    r1.metric(f"Roof Trusses ({building_width}ft span)", f"{total_trusses} pcs", help="Calculated at 24-inch O.C.")
    r2.metric("Roof Decking (4x8)", f"{roof_sheets_order} sheets", help="Assuming standard 6/12 pitch")