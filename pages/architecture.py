import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Architecture & Master Specs", layout="wide")

# ==========================================
# 🔒 SECURITY & CONTEXT GUARDS
# ==========================================
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

st.header("📐 Architecture & Master Specs")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Enforce structural design constraints, standardize finish schedules, estimate costs, and generate municipal/HOA submittals.")
st.divider()

def get_project_state():
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
        conn.close()
        return json.loads(row[0]) if row and row[0] else {}
    except Exception:
        return {}

db_state = get_project_state()
arch_state = db_state.get("architecture", {})
sq_ft = float(db_state.get("est_sq_ft", 1404.0))

# ==========================================
# TABS FOR ENTERPRISE WORKFLOW
# ==========================================
tab_specs, tab_cost, tab_hoa, tab_sub = st.tabs([
    "1. Master Specifications", 
    "2. Cost Estimation & Proforma", 
    "3. HOA / ARB Submittal", 
    "4. Subcontractor Scopes"
])

# ==========================================
# TAB 1: MASTER SPECIFICATIONS
# ==========================================
with tab_specs:
    
    # --- YOUR EXISTING CORE CONSTRAINTS ---
    st.subheader("Design Constraints & Methodologies")
    
    colA, colB = st.columns([2, 1], gap="large")
    with colA:
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
            
    with colB:
        st.info("💡 **Execution Note:** Any deviation from the 26ft width constraint or specified framing methodology requires direct corporate approval prior to municipal submission.")
        st.subheader("Site Plans")
        st.button("📄 View Master Plot Plan", use_container_width=True)
        st.button("📄 View Phase Lots (Color Coded)", use_container_width=True)

    st.divider()
    
    # --- ENTERPRISE FINISH SCHEDULES ---
    st.subheader("Project Finish Schedules")
    
    with st.expander("🏠 Exterior Envelope & Elevation", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            primary_siding = st.selectbox("Primary Siding Material", ["Fiber Cement Lap (Hardie)", "Vinyl Siding", "Stucco", "Brick Veneer", "Board & Batten"], index=0)
            secondary_siding = st.selectbox("Secondary Accent Material", ["None", "Brick Veneer", "Stone Accent", "Cedar Shake", "Board & Batten"], index=1)
            fascia_soffit = st.selectbox("Fascia & Soffit Material", ["Vinyl Vented Soffit / Alum Fascia", "Fiber Cement (Hardie)", "Painted Wood"], index=0)
        with col2:
            roofing_type = st.selectbox("Roof Material", ["Architectural Shingles (30-Year)", "3-Tab Shingles", "Standing Seam Metal", "Ribbed Metal Panel"], index=0)
            roof_color = st.text_input("Roof Color Code/Name", value=arch_state.get("roof_color", "Charcoal / Weathered Wood"))
            drip_edge = st.selectbox("Drip Edge Color", ["White", "Black", "Bronze", "Mill Finish"], index=1)
        with col3:
            window_style = st.selectbox("Window Type", ["Single Hung Vinyl", "Double Hung Vinyl", "Aluminum Frame"], index=0)
            window_color = st.selectbox("Window Frame Color", ["White", "Black", "Almond", "Bronze"], index=0)
            front_door = st.selectbox("Front Door Style", ["Fiberglass Craftsman (Stained)", "Steel 6-Panel (Painted)", "Solid Wood", "Glass Light Panel"], index=0)

    with st.expander("🛋️ Interior Finishes, Millwork & Cabinetry", expanded=True):
        icol1, icol2, icol3 = st.columns(3)
        with icol1:
            primary_floor = st.selectbox("Main Living Floors", ["Luxury Vinyl Plank (LVP)", "Engineered Hardwood", "Ceramic Wood-Look Tile", "Stained Concrete"], index=0)
            bedroom_floor = st.selectbox("Bedroom Floors", ["Match Primary (LVP)", "Plush Carpet", "Berber Carpet"], index=0)
            bathroom_floor = st.selectbox("Bathroom Floors", ["Ceramic Tile", "Porcelain Tile", "Match Primary (LVP)"], index=0)
        with icol2:
            cabinet_style = st.selectbox("Cabinet Door Profile", ["Shaker Style", "Raised Panel", "Flat Panel (Modern)"], index=0)
            countertop_mat = st.selectbox("Countertop Material", ["3cm Quartz", "Level 1 Granite", "Butcher Block", "Laminate (Formica)"], index=0)
            hardware_finish = st.selectbox("Cabinet Hardware Finish", ["Matte Black", "Brushed Nickel", "Oil Rubbed Bronze", "Satin Brass"], index=0)
        with icol3:
            baseboard_style = st.selectbox("Baseboards", ["5-1/4\" Speed Base", "3-1/4\" Colonial", "1x6 Craftsman (Square)"], index=0)
            casing_style = st.selectbox("Door/Window Casing", ["3-1/4\" Colonial", "1x4 Craftsman (Square)", "2-1/4\" Ranch"], index=1)
            interior_doors = st.selectbox("Interior Door Style", ["2-Panel Square Hollow Core", "6-Panel Textured", "Solid Core Craftsman"], index=0)

    with st.expander("🎨 Master Paint & Color Schedule", expanded=True):
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            wall_paint = st.text_input("Interior Walls", value=arch_state.get("wall_paint", "SW 7029 Agreeable Gray - Flat/Eggshell"))
            trim_paint = st.text_input("Interior Trim & Doors", value=arch_state.get("trim_paint", "SW 7006 Extra White - Semi-Gloss"))
            ceiling_paint = st.text_input("Ceilings", value=arch_state.get("ceiling_paint", "SW 7007 Ceiling Bright White - Flat"))
            cabinet_paint = st.text_input("Cabinet Color", value=arch_state.get("cabinet_paint", "SW 7006 Extra White OR Factory Finish"))
        with pcol2:
            ext_siding_paint = st.text_input("Main Exterior Body", value=arch_state.get("ext_siding_paint", "SW 7004 Snowbound"))
            ext_trim_paint = st.text_input("Exterior Trim & Fascia", value=arch_state.get("ext_trim_paint", "SW 7069 Iron Ore"))
            ext_accent_paint = st.text_input("Exterior Accent / Shutters", value=arch_state.get("ext_accent_paint", "SW 6258 Tricorn Black"))
            ext_door_paint = st.text_input("Front Door", value=arch_state.get("ext_door_paint", "Minwax Early American Stain OR SW 6258"))

# ==========================================
# TAB 2: COST ESTIMATION & PROFORMA
# ==========================================
with tab_cost:
    st.subheader("Exterior & Interior Finish Budgets")
    st.markdown("Estimate hard costs for finishes to feed the Proforma.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Exterior Finishes**")
        siding_cost = st.number_input("Siding & Cornice (Turnkey) ($)", value=sq_ft * 8.50, step=500.0)
        roofing_cost = st.number_input("Roofing System (Turnkey) ($)", value=sq_ft * 4.50, step=500.0)
        ext_paint_cost = st.number_input("Exterior Painting ($)", value=sq_ft * 2.50, step=250.0)
        total_exterior_finishes = siding_cost + roofing_cost + ext_paint_cost
        
    with c2:
        st.markdown("**Interior Finishes**")
        flooring_cost = st.number_input("Flooring (Material & Install) ($)", value=sq_ft * 4.00, step=500.0)
        cabinets_tops_cost = st.number_input("Cabinets & Countertops ($)", value=8500.0, step=500.0)
        millwork_doors_cost = st.number_input("Interior Doors, Trim & Hardware ($)", value=4500.0, step=250.0)
        int_paint_cost = st.number_input("Interior Painting ($)", value=sq_ft * 3.50, step=250.0)
        total_interior_finishes = flooring_cost + cabinets_tops_cost + millwork_doors_cost + int_paint_cost

    st.divider()
    t1, t2, t3 = st.columns(3)
    t1.metric("Exterior Finishes Total", f"${total_exterior_finishes:,.2f}")
    t2.metric("Interior Finishes Total", f"${total_interior_finishes:,.2f}")
    t3.metric("Total Finish Budget", f"${(total_exterior_finishes + total_interior_finishes):,.2f}")

    if st.button("💾 Save Architecture & Sync Budgets to DB", type="primary", use_container_width=True):
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
            data = json.loads(row[0]) if row and row[0] else {}
            
            # Save Specs
            data["architecture"] = {
                "primary_siding": primary_siding, "secondary_siding": secondary_siding, "roofing_type": roofing_type,
                "roof_color": roof_color, "window_color": window_color, "primary_floor": primary_floor,
                "cabinet_style": cabinet_style, "countertop_mat": countertop_mat, "wall_paint": wall_paint,
                "trim_paint": trim_paint, "ext_siding_paint": ext_siding_paint, "ext_trim_paint": ext_trim_paint
            }
            
            # Sync Budgets to Proforma
            if "estimates" not in data:
                data["estimates"] = {}
            data["estimates"]["Exterior Shell Finishes"] = total_exterior_finishes
            data["estimates"]["Interior Finishes & Drywall"] = total_interior_finishes
            
            conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(data), active_project))
            conn.commit()
            conn.close()
            st.toast("✅ Master Architecture and Proforma Budgets successfully saved!")
        except Exception as e:
            st.error(f"Database error: {e}")

# ==========================================
# TAB 3: HOA / ARB SUBMITTAL
# ==========================================
with tab_hoa:
    st.subheader("Architectural Review Board (ARB) / HOA Submittal")
    st.markdown("Use this summarized exterior profile for submitting design plans to municipal boards or HOA committees.")
    
    st.markdown(f"""
    ### Exterior Elevation Materials
    * **Primary Cladding:** {primary_siding} (Painted: *{ext_siding_paint}*)
    * **Secondary/Accent Cladding:** {secondary_siding}
    * **Fascia & Soffit:** {fascia_soffit} (Painted: *{ext_trim_paint}*)
    * **Roofing System:** {roofing_type} in **{roof_color}** (Drip Edge: {drip_edge})
    
    ### Fenestration & Accents
    * **Windows:** {window_style} featuring **{window_color}** frames.
    * **Front Door:** {front_door} (Finish: *{ext_door_paint}*)
    * **Shutters / Accents:** Painted in *{ext_accent_paint}*
    
    > **Note to Committee:** All materials selected meet standard subdivision covenants for architectural harmony. Physical color swatches can be provided upon request.
    """)
    st.button("🖨️ Print Submittal Page")

# ==========================================
# TAB 4: SUBCONTRACTOR SCOPES
# ==========================================
with tab_sub:
    st.subheader("🛠️ Subcontractor Specific Scopes")
    st.markdown("Isolate the Master Schedule by trade to attach to your Subcontractor Agreements.")
    
    sub_col1, sub_col2 = st.columns(2)
    
    with sub_col1:
        st.markdown("##### 🖌️ Painting Subcontractor Scope")
        paint_scope = [
            {"Surface": "Interior Walls", "Spec": wall_paint},
            {"Surface": "Interior Trim/Doors", "Spec": trim_paint},
            {"Surface": "Ceilings", "Spec": ceiling_paint},
            {"Surface": "Exterior Body", "Spec": ext_siding_paint},
            {"Surface": "Exterior Trim", "Spec": ext_trim_paint},
            {"Surface": "Front Door", "Spec": ext_door_paint},
        ]
        st.dataframe(pd.DataFrame(paint_scope), use_container_width=True, hide_index=True)
        
    with sub_col2:
        st.markdown("##### 🪚 Finish Carpentry Scope")
        trim_scope = [
            {"Item", "Specification"},
            {"Baseboards", baseboard_style},
            {"Window/Door Casing", casing_style},
            {"Interior Doors", interior_doors},
            {"Cabinet Profile", cabinet_style},
            {"Cabinet Hardware", hardware_finish},
        ]
        st.dataframe(pd.DataFrame(trim_scope[1:], columns=trim_scope[0]), use_container_width=True, hide_index=True)

    st.markdown("##### 🧱 Exterior Envelope Scope (Siding/Roofing)")
    ext_scope = [
        {"Trade", "Material / Scope Item"},
        {"Siding Sub", f"Install {primary_siding} as main, {secondary_siding} as accent."},
        {"Siding Sub", f"Install {fascia_soffit} systems."},
        {"Roofing Sub", f"Install {roofing_type} ({roof_color}) with {drip_edge} drip edge."},
        {"Window Sub", f"Install {window_style} ({window_color} frames)."},
    ]
    st.dataframe(pd.DataFrame(ext_scope[1:], columns=ext_scope[0]), use_container_width=True, hide_index=True)