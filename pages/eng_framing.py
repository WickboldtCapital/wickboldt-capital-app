import streamlit as st
import pandas as pd
import math
import sqlite3
import json

st.set_page_config(page_title="Structural Framing", layout="wide")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

st.header("🪵 Structural Framing & Lumber Takeoffs")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Estimate lumber packages, studs, plates, and sheathing with support for traditional 16\" framing and 24\" Advanced Framing (OVE) options. Data syncs with the Master Estimator.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Building Dimensions")
    st.info("💡 **Constraint Reminder:** Max footprint width is 26 feet.")
    
    building_length = st.number_input("Building Length (ft)", min_value=10.0, value=60.0, step=1.0)
    building_width = st.number_input("Building Width (ft)", min_value=10.0, max_value=26.0, value=26.0, step=1.0)
    wall_height = st.selectbox("Wall Height / Stud Length", ["8 ft (92-5/8\")", "9 ft (104-5/8\")", "10 ft (116-5/8\")"], index=1)
    
    st.subheader("Framing Specs & OVE Options")
    stud_spacing = st.selectbox("Stud Spacing (O.C.)", ["16 inches (Traditional)", "24 inches (Advanced Framing / OVE)"], index=0)
    
    # Advanced Framing (OVE) Conditional Options
    alignment_mode = "N/A"
    top_plate_mode = "Double Top Plate"
    
    if "24 inches" in stud_spacing:
        st.markdown("##### 📐 Advanced Framing (OVE) Configurations")
        alignment_mode = st.radio(
            "Stud & Roof Framing Alignment", 
            ["Aligned (Studs centered on roof trusses/rafters)", "Unaligned (Standard 24\" spacing)"]
        )
        
        if alignment_mode == "Aligned (Studs centered on roof trusses/rafters)":
            top_plate_mode = st.selectbox(
                "Top Plate Style", 
                ["Single Top Plate (Requires Aligned Stacking)", "Double Top Plate"]
            )
        else:
            top_plate_mode = "Double Top Plate"
            st.info("ℹ️ Unaligned 24\" O.C. framing requires a standard Double Top Plate.")
    
    exterior_walls = st.selectbox("Exterior Wall Depth", ["2x4", "2x6"], index=0)
    
    interior_lf = st.number_input("Estimated Interior Wall Length (Linear Feet)", min_value=0.0, value=150.0, step=10.0)
    waste_factor = st.slider("Lumber Waste Buffer (%)", min_value=0, max_value=25, value=15, step=1)
    
    st.subheader("Lumber Pricing (Optional)")
    avg_stud_cost = st.number_input("Est. Cost per Stud ($)", value=4.50, step=0.25)
    avg_plate_cost = st.number_input("Est. Cost per 16ft Plate Board ($)", value=11.00, step=0.50)
    avg_osb_cost = st.number_input("Est. Cost per 4x8 OSB Sheet ($)", value=14.50, step=0.50)

with col2:
    st.subheader("Takeoff Estimates")
    
    # Mathematical Calculations
    exterior_lf = (building_length * 2) + (building_width * 2)
    total_lf = exterior_lf + interior_lf
    
    spacing_val = 16 if "16" in stud_spacing else 24
    
    # Studs: 1 stud per spacing interval + corner/intersection allowance
    base_studs = math.ceil(total_lf / (spacing_val / 12))
    # Advanced framing (OVE) often optimizes corners (e.g., 2-stud corners instead of 3), 
    # but we retain robust allowance scaled by spacing efficiency
    corner_multiplier = 2 if "24" in stud_spacing else 3
    corner_intersection_allowance = math.ceil((exterior_lf / 10) * corner_multiplier)
    
    total_studs_exact = base_studs + corner_intersection_allowance
    total_studs_order = math.ceil(total_studs_exact * (1 + (waste_factor / 100)))
    
    # Plates Calculation based on OVE selection
    # Single top plate = 1 bottom + 1 top = 2 plates total. Double top plate = 1 bottom + 2 top = 3 plates total.
    if "24" in stud_spacing and alignment_mode == "Aligned (Studs centered on roof trusses/rafters)" and top_plate_mode == "Single Top Plate (Requires Aligned Stacking)":
        plates_per_wall = 2
        plate_description = "Single Top Plate (OVE Stacked)"
    else:
        plates_per_wall = 3
        plate_description = "Double Top Plate"
        
    plate_lf_exact = total_lf * plates_per_wall
    plate_board_length = 16
    total_plates_exact = math.ceil(plate_lf_exact / plate_board_length)
    total_plates_order = math.ceil(total_plates_exact * (1 + (waste_factor / 100)))
    
    # Exterior Sheathing (4x8 OSB/Plywood)
    sqft_wall_surface = exterior_lf * int(wall_height.split()[0])
    sheets_exact = sqft_wall_surface / 32
    sheets_order = math.ceil(sheets_exact * (1 + (waste_factor / 100)))
    
    st.markdown("#### 🌲 Wall Framing (Studs & Plates)")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Wall Studs ({exterior_walls})", f"{total_studs_order:,} pcs", help="Includes waste factor and corners")
    m2.metric("Plates (16ft boards)", f"{total_plates_order:,} pcs", help=plate_description)
    m3.metric("Exterior Sheathing (4x8)", f"{sheets_order:,} sheets", help="OSB/ZIP System or Plywood")
    
    st.divider()
    
    st.markdown("#### 🏠 Roof / Ceiling")
    # Roof framing spacing automatically matches wall spacing if aligned
    truss_spacing = 24 if "24" in stud_spacing else 24
    total_trusses = math.ceil(building_length / (truss_spacing / 12)) + 1
    
    roof_sqft_flat = building_length * building_width
    roof_sqft_pitched = roof_sqft_flat * 1.12 
    roof_sheets_exact = roof_sqft_pitched / 32
    roof_sheets_order = math.ceil(roof_sheets_exact * (1 + (waste_factor / 100)))
    
    r1, r2 = st.columns(2)
    r1.metric(f"Roof Trusses ({building_width}ft span)", f"{total_trusses:,} pcs", help=f"Calculated at {truss_spacing}-inch O.C. ({'Aligned with studs' if alignment_mode.startswith('Aligned') else 'Standard spacing'})")
    r2.metric("Roof Decking (4x8)", f"{roof_sheets_order:,} sheets", help="Assuming standard 6/12 pitch")

    st.divider()

    # ==========================================
    # BOM TABLE & PRICING
    # ==========================================
    st.markdown("#### 📋 Bill of Materials (BOM) Summary & Valuation")
    
    total_lumber_cost = (total_studs_order * avg_stud_cost) + (total_plates_order * avg_plate_cost) + ((sheets_order + roof_sheets_order) * avg_osb_cost)
    st.metric("Estimated Rough Framing Material Cost", f"${total_lumber_cost:,.2f}")

    bom_df = pd.DataFrame([
        {"Material": f"Wall Studs ({exterior_walls} - {wall_height[:4]})", "Quantity": total_studs_order, "Unit": "Pcs", "Unit Cost": avg_stud_cost, "Total": total_studs_order * avg_stud_cost},
        {"Material": f"Plates (16ft Lumber Boards) - {plate_description}", "Quantity": total_plates_order, "Unit": "Pcs", "Unit Cost": avg_plate_cost, "Total": total_plates_order * avg_plate_cost},
        {"Material": "Exterior Wall Sheathing (4x8)", "Quantity": sheets_order, "Unit": "Sheets", "Unit Cost": avg_osb_cost, "Total": sheets_order * avg_osb_cost},
        {"Material": f"Roof Trusses (Prefab) @ {truss_spacing}\" O.C.", "Quantity": total_trusses, "Unit": "Pcs", "Unit Cost": 125.00, "Total": total_trusses * 125.00},
        {"Material": "Roof Decking / Sheathing (4x8)", "Quantity": roof_sheets_order, "Unit": "Sheets", "Unit Cost": avg_osb_cost, "Total": roof_sheets_order * avg_osb_cost},
    ])

    st.dataframe(
        bom_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Unit Cost": st.column_config.NumberColumn("Unit Cost ($)", format="$%.2f"),
            "Total": st.column_config.NumberColumn("Total Cost ($)", format="$%.2f")
        }
    )

    st.divider()

    # ==========================================
    # DATABASE COMMIT
    # ==========================================
    if st.button("💾 Save Takeoff to Project Database", type="primary", use_container_width=True):
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
            data = json.loads(row[0]) if row and row[0] else {}
            
            if "engineering" not in data:
                data["engineering"] = {}
                
            data["engineering"]["framing_method"] = stud_spacing
            data["engineering"]["framing_alignment"] = alignment_mode
            data["engineering"]["framing_top_plate"] = top_plate_mode
            data["engineering"]["framing_studs"] = total_studs_order
            data["engineering"]["framing_plates"] = total_plates_order
            data["engineering"]["framing_sheathing_sheets"] = sheets_order
            data["engineering"]["framing_trusses"] = total_trusses
            data["engineering"]["framing_total_cost"] = total_lumber_cost
            
            conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(data), active_project))
            conn.commit()
            conn.close()
            st.toast("✅ Framing takeoff and OVE configurations saved to master project ledger!")
        except Exception as e:
            st.error(f"Database error: {e}")