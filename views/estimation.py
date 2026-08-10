import streamlit as st
import pandas as pd
import sqlite3
import json

# --- SECURITY GUARD ---
if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# ==========================================
# 💾 INSTANT AUTO-SAVE & GLOBAL DB ENGINE
# ==========================================
DB_FILE = "wickboldt_projects.db"

def init_db_schema():
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN project_data TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass 
    conn.close()

init_db_schema()

# 1. Fetch Global Admin Defaults
def get_global_defaults():
    conn = sqlite3.connect(DB_FILE)
    try:
        row = conn.execute("SELECT project_data FROM projects WHERE project_name='__GLOBAL_DEFAULTS__'").fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        pass
    finally:
        conn.close()
    return {}

global_defaults = get_global_defaults()

# 2. Fetch User's Local Project State
def get_db_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (st.session_state["active_project"],)).fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

db_state = get_db_state()

def auto_save(key):
    val = st.session_state[key]
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (st.session_state["active_project"],)).fetchone()
    current_state = json.loads(row[0]) if row and row[0] else {}
    current_state[key] = val
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), st.session_state["active_project"]))
    conn.commit()
    conn.close()

def bound(val, minimum, maximum):
    if minimum is not None: val = max(val, minimum)
    if maximum is not None: val = min(val, maximum)
    return val

# 3. Custom UI Wrappers prioritizing Global Defaults
def auto_num(label, key, hardcoded_default, container=st, step=None, min_value=None, max_value=None, help=None):
    effective_default = global_defaults.get(key, hardcoded_default)
    saved_val = bound(float(db_state.get(key, effective_default)), min_value, max_value)
    return container.number_input(label, value=saved_val, step=step, min_value=min_value, max_value=max_value, help=help, key=key, on_change=auto_save, args=(key,))

def auto_slider(label, key, min_value, max_value, hardcoded_default, container=st, step=None, help=None):
    effective_default = global_defaults.get(key, hardcoded_default)
    saved_val = bound(float(db_state.get(key, effective_default)), min_value, max_value)
    return container.slider(label, min_value=float(min_value), max_value=float(max_value), value=saved_val, step=step, help=help, key=key, on_change=auto_save, args=(key,))

def auto_radio(label, key, options, default_index=0, container=st, horizontal=False):
    effective_default = global_defaults.get(key, options[default_index])
    saved_val = db_state.get(key, effective_default)
    idx = options.index(saved_val) if saved_val in options else default_index
    return container.radio(label, options=options, index=idx, horizontal=horizontal, key=key, on_change=auto_save, args=(key,))

def auto_select(label, key, options, default_index=0, container=st):
    effective_default = global_defaults.get(key, options[default_index])
    saved_val = db_state.get(key, effective_default)
    idx = options.index(saved_val) if saved_val in options else default_index
    return container.selectbox(label, options=options, index=idx, key=key, on_change=auto_save, args=(key,))

def safe_pct(val, total):
    return (val / total * 100) if total > 0 else 0.0

# --- HEADER STYLING ---
st.markdown("### 🏗️ Wickboldt Capital: Moore Parkway Portal")
st.markdown("*Today's Foundation. Tomorrow's Legacy.*")
st.success(f"🟢 **Active Project:** `{st.session_state['active_project']}` &nbsp;&nbsp;|&nbsp;&nbsp; 📂 **Active Revision:** Comprehensive Proforma Baseline")
st.markdown("---")

st.header("Construction Cost Estimation & Budget Breakdown")
st.markdown("Manage your direct construction draws, indirect soft costs, and bank draw schedules.")
st.write("")

# --- TABS ---
tab_costs, tab_draws = st.tabs(["📊 Cost Breakdown & Totals", "🏦 Bank Draw Schedule"])

with tab_costs:
    st.subheader("Base Project Metrics")
    sq_ft = auto_num("Unit Living Area (Square Feet)", "est_sq_ft", 1150.0, step=50.0)
    st.markdown("---")

    # ==========================================
    # GLOBALLY LINKED DEBT CALCULATIONS
    # ==========================================
    # Fetch variables set in the Debt Stack (or fallback to defaults)
    const_val_method = db_state.get("const_val_method", global_defaults.get("const_val_method", "Appraised Value"))
    const_appraised = float(db_state.get("const_appraised", global_defaults.get("const_appraised", 200000.0)))
    const_grm = float(db_state.get("const_grm", global_defaults.get("const_grm", 10.0)))
    const_rent = float(db_state.get("Construction_rent", global_defaults.get("Construction_rent", 4500.0)))
    const_eq_pct = float(db_state.get("const_eq_pct", global_defaults.get("const_eq_pct", 25.0)))
    const_act_rate = float(db_state.get("const_act_rate", global_defaults.get("const_act_rate", 6.25)))
    const_draw_pct = float(db_state.get("const_draw_pct", global_defaults.get("const_draw_pct", 50.0)))
    
    # NEW: Fetch Construction Loan Closing Costs from Debt Stack
    const_close = float(db_state.get("const_close", global_defaults.get("const_close", 0.0)))

    if const_val_method == "Appraised Value":
        const_project_value = const_appraised
    else:
        const_project_value = (const_rent * 12) * const_grm

    const_limit = const_project_value * (1 - (const_eq_pct / 100))

    st.subheader("📋 Indirect Costs (Soft Costs & Fees)")
    
    st.markdown("#### Project Timeline & Globally Linked Debt Costs")
    const_term = auto_num("Construction Term (Months) [Controls timeline across portal]", "const_term", 12.0, step=1.0)
    linked_interest_cost = const_limit * (const_act_rate / 100) * (const_term / 12) * (const_draw_pct / 100)
    
    st.info(f"🔗 **Linked Construction Interest:** \${linked_interest_cost:,.2f} *(Synchronized with Debt Stack: {const_term:,.0f} months, {const_act_rate}% rate, against \${const_limit:,.2f} facility)*\n\n"
            f"🔗 **Linked Const. Closing Costs:** \${const_close:,.2f} *(Synchronized with Debt Stack)*")
    st.markdown("---")
    
    # ==========================================
    # INDIRECT COSTS
    # ==========================================
    ind_mode = auto_radio("Indirect Budget Input Method", "ind_calc_method", ["Percentage Breakdown (Top-Down)", "Cost per Sq Ft (Bottom-Up)", "Manual Estimates (Bottom-Up)"], horizontal=True)
    st.write("")
    
    if ind_mode == "Percentage Breakdown (Top-Down)":
        ind_col1, ind_col2 = st.columns(2)
        ind_method = auto_select("Determine Total Budget By:", "est_ind_method", ["Target $ / Sq Ft", "Lump Sum Total ($)"], container=ind_col1)
        if ind_method == "Target $ / Sq Ft":
            ind_target_input = auto_num("Target Indirect Budget ($ / Sq Ft)", "est_ind_target", 70.24, container=ind_col2, step=1.0)
            total_indirect = ind_target_input * sq_ft
        else:
            total_indirect = auto_num("Total Indirect Budget ($)", "est_ind_target_total", 80770.85, container=ind_col2, step=1000.0)

        st.markdown("#### Indirect Cost Allocation (%)")
        i1, i2 = st.columns(2)
        ind_land_pct = auto_num("Land Acquisition / Lot Basis (%)", "ind_land_pct", 11.66, container=i1, step=0.1)
        ind_gc_pct = auto_num("General Contracting Fee (%)", "ind_gc_pct", 11.66, container=i1, step=0.1)
        ind_soft_pct = auto_num("Soft Costs & Engineering (%)", "ind_soft_pct", 5.83, container=i1, step=0.1)
        
        # Globally Linked Fixed Math - Closing Costs
        ind_c_close_val = const_close
        ind_c_close_pct = safe_pct(ind_c_close_val, total_indirect)
        i1.text_input("Const. Loan Closing Costs (%)", value=f"{ind_c_close_pct:.2f}% (Globally Linked)", disabled=True)

        # Globally Linked Fixed Math - Interest
        ind_c_int_val = linked_interest_cost
        ind_c_int_pct = safe_pct(ind_c_int_val, total_indirect)
        i2.text_input("Est. Construction Loan Interest (%)", value=f"{ind_c_int_pct:.2f}% (Globally Linked)", disabled=True)

        ind_r_close_pct = auto_num("Perm. Refi Closing & Takeout (%)", "ind_r_close_pct", 5.83, container=i2, step=0.1)
        ind_res_pct = auto_num("Capital Reserves & Equity Buffer (%)", "ind_res_pct", 46.72, container=i2, step=0.1)

        ind_total_pct = ind_land_pct + ind_gc_pct + ind_soft_pct + ind_c_close_pct + ind_c_int_pct + ind_r_close_pct + ind_res_pct
        if abs(ind_total_pct - 100.0) > 0.1:
            st.warning(f"⚠️ Allocation totals {ind_total_pct:.2f}%. Please adjust manual inputs so total equals 100%.")

        ind_land_val = total_indirect * (ind_land_pct / 100)
        ind_gc_val = total_indirect * (ind_gc_pct / 100)
        ind_soft_val = total_indirect * (ind_soft_pct / 100)
        ind_r_close_val = total_indirect * (ind_r_close_pct / 100)
        ind_res_val = total_indirect * (ind_res_pct / 100)

    elif ind_mode == "Cost per Sq Ft (Bottom-Up)":
        st.markdown("#### Indirect Cost per Square Foot ($/sf)")
        i1, i2 = st.columns(2)
        ind_land_sf = auto_num("Land Acquisition / Lot Basis ($/sf)", "ind_land_sf", 8.19, container=i1, step=0.1)
        ind_gc_sf = auto_num("General Contracting Fee ($/sf)", "ind_gc_sf", 8.19, container=i1, step=0.1)
        ind_soft_sf = auto_num("Soft Costs & Engineering ($/sf)", "ind_soft_sf", 4.10, container=i1, step=0.1)
        
        # Globally Linked Fixed Math - Closing Costs
        ind_c_close_val = const_close
        ind_c_close_sf = ind_c_close_val / sq_ft if sq_ft > 0 else 0
        i1.text_input("Const. Loan Closing Costs ($/sf)", value=f"${ind_c_close_sf:.2f} (Globally Linked)", disabled=True)

        # Globally Linked Fixed Math - Interest
        ind_c_int_val = linked_interest_cost
        ind_c_int_sf = ind_c_int_val / sq_ft if sq_ft > 0 else 0
        i2.text_input("Est. Construction Loan Interest ($/sf)", value=f"${ind_c_int_sf:.2f} (Globally Linked)", disabled=True)

        ind_r_close_sf = auto_num("Perm. Refi Closing & Takeout ($/sf)", "ind_r_close_sf", 4.10, container=i2, step=0.1)
        ind_res_sf = auto_num("Capital Reserves & Equity Buffer ($/sf)", "ind_res_sf", 32.81, container=i2, step=0.1)

        ind_land_val = ind_land_sf * sq_ft
        ind_gc_val = ind_gc_sf * sq_ft
        ind_soft_val = ind_soft_sf * sq_ft
        ind_r_close_val = ind_r_close_sf * sq_ft
        ind_res_val = ind_res_sf * sq_ft
        
        total_indirect = ind_land_val + ind_gc_val + ind_soft_val + ind_c_close_val + ind_c_int_val + ind_r_close_val + ind_res_val

    else: # Manual Estimates
        st.markdown("#### Indirect Cost Manual Estimates ($)")
        i1, i2 = st.columns(2)
        ind_land_val = auto_num("Land Acquisition / Lot Basis ($)", "ind_land_est", 9997.75, container=i1, step=100.0)
        ind_gc_val = auto_num("General Contracting Fee ($)", "ind_gc_est", 9997.75, container=i1, step=100.0)
        ind_soft_val = auto_num("Soft Costs & Engineering ($)", "ind_soft_est", 4998.88, container=i1, step=100.0)
        
        # Globally Linked Fixed Math - Closing Costs
        ind_c_close_val = const_close
        i1.text_input("Const. Loan Closing Costs ($)", value=f"${ind_c_close_val:,.2f} (Globally Linked)", disabled=True)
        
        # Globally Linked Fixed Math - Interest
        ind_c_int_val = linked_interest_cost
        i2.text_input("Est. Construction Loan Interest ($)", value=f"${ind_c_int_val:,.2f} (Globally Linked)", disabled=True)

        ind_r_close_val = auto_num("Perm. Refi Closing & Takeout ($)", "ind_r_close_est", 4998.88, container=i2, step=100.0)
        ind_res_val = auto_num("Capital Reserves & Equity Buffer ($)", "ind_res_est", 40059.60, container=i2, step=100.0)
        
        total_indirect = ind_land_val + ind_gc_val + ind_soft_val + ind_c_close_val + ind_c_int_val + ind_r_close_val + ind_res_val

    # Reverse calculation for the UI table
    ind_land_pct_disp = safe_pct(ind_land_val, total_indirect)
    ind_gc_pct_disp = safe_pct(ind_gc_val, total_indirect)
    ind_soft_pct_disp = safe_pct(ind_soft_val, total_indirect)
    ind_c_close_pct_disp = safe_pct(ind_c_close_val, total_indirect)
    ind_c_int_pct_disp = safe_pct(ind_c_int_val, total_indirect)
    ind_r_close_pct_disp = safe_pct(ind_r_close_val, total_indirect)
    ind_res_pct_disp = safe_pct(ind_res_val, total_indirect)
    ind_target = total_indirect / sq_ft if sq_ft > 0 else 0

    ind_data = {
        "Indirect Category": [
            f"Land Acquisition / Lot Basis ({ind_land_pct_disp:.2f}%)",
            f"General Contracting Fee ({ind_gc_pct_disp:.2f}%)",
            f"Soft Costs & Engineering ({ind_soft_pct_disp:.2f}%)",
            f"Construction Loan Closing Costs ({ind_c_close_pct_disp:.2f}%)",
            f"Estimated Construction Loan Interest ({ind_c_int_pct_disp:.2f}%)",
            f"Permanent Refinance Closing & Takeout ({ind_r_close_pct_disp:.2f}%)",
            f"Capital Reserves & Equity Buffer ({ind_res_pct_disp:.2f}%)"
        ],
        "Allocated Budget": [
            f"\${ind_land_val:,.2f}", f"\${ind_gc_val:,.2f}", f"\${ind_soft_val:,.2f}", 
            f"\${ind_c_close_val:,.2f}", f"\${ind_c_int_val:,.2f}", f"\${ind_r_close_val:,.2f}", 
            f"\${ind_res_val:,.2f}"
        ]
    }
    st.table(pd.DataFrame(ind_data))
    st.info(f"📋 **Indirect Total:** \${total_indirect:,.2f} (*\${ind_target:,.2f} / sq ft*)")
    st.markdown("---")

    # ==========================================
    # DIRECT COSTS
    # ==========================================
    st.subheader("🧱 Direct Costs (Construction Draws)")
    
    dir_mode = auto_radio("Direct Budget Input Method", "dir_calc_method", ["Percentage Breakdown (Top-Down)", "Cost per Sq Ft (Bottom-Up)", "Manual Estimates (Bottom-Up)"], horizontal=True)
    st.write("")
    
    if dir_mode == "Percentage Breakdown (Top-Down)":
        dir_col1, dir_col2 = st.columns(2)
        dir_method = auto_select("Determine Total Budget By:", "est_dir_method", ["Target $ / Sq Ft", "Lump Sum Total ($)"], container=dir_col1)
        if dir_method == "Target $ / Sq Ft":
            dir_target_input = auto_num("Target Direct Construction Budget ($ / Sq Ft)", "est_dir_target", 100.44, container=dir_col2, step=1.0)
            total_direct = dir_target_input * sq_ft
        else:
            total_direct = auto_num("Total Direct Construction Budget ($)", "est_dir_target_total", 115506.00, container=dir_col2, step=1000.0)

        st.markdown("#### Direct Cost Allocation (%)")
        d1, d2 = st.columns(2)
        dir_site_pct = auto_num("Site Work, Foundation & Civil Grading (%)", "dir_site_pct", 20.00, container=d1, step=1.0)
        dir_frame_pct = auto_num("Framing, Exterior Shell & Roof (%)", "dir_frame_pct", 25.00, container=d1, step=1.0)
        dir_mep_pct = auto_num("MEP Rough-Ins (%)", "dir_mep_pct", 20.00, container=d1, step=1.0)
        dir_finish_pct = auto_num("Interior Finishes & Drywall (%)", "dir_finish_pct", 25.00, container=d2, step=1.0)
        dir_cont_pct = auto_num("Build Contingency (%)", "dir_cont_pct", 10.00, container=d2, step=1.0)

        dir_total_pct = dir_site_pct + dir_frame_pct + dir_mep_pct + dir_finish_pct + dir_cont_pct
        if abs(dir_total_pct - 100.0) > 0.1:
            st.warning(f"⚠️ Allocation totals {dir_total_pct:.2f}%. Please adjust to equal 100%.")

        dir_site_val = total_direct * (dir_site_pct / 100)
        dir_frame_val = total_direct * (dir_frame_pct / 100)
        dir_mep_val = total_direct * (dir_mep_pct / 100)
        dir_finish_val = total_direct * (dir_finish_pct / 100)
        dir_cont_val = total_direct * (dir_cont_pct / 100)

    elif dir_mode == "Cost per Sq Ft (Bottom-Up)":
        st.markdown("#### Direct Cost per Square Foot ($/sf)")
        d1, d2 = st.columns(2)
        dir_site_sf = auto_num("Site Work, Foundation & Civil Grading ($/sf)", "dir_site_sf", 20.09, container=d1, step=0.1)
        dir_frame_sf = auto_num("Framing, Exterior Shell & Roof ($/sf)", "dir_frame_sf", 25.11, container=d1, step=0.1)
        dir_mep_sf = auto_num("MEP Rough-Ins ($/sf)", "dir_mep_sf", 20.09, container=d1, step=0.1)
        dir_finish_sf = auto_num("Interior Finishes & Drywall ($/sf)", "dir_finish_sf", 25.11, container=d2, step=0.1)
        dir_cont_sf = auto_num("Build Contingency ($/sf)", "dir_cont_sf", 10.04, container=d2, step=0.1)

        dir_site_val = dir_site_sf * sq_ft
        dir_frame_val = dir_frame_sf * sq_ft
        dir_mep_val = dir_mep_sf * sq_ft
        dir_finish_val = dir_finish_sf * sq_ft
        dir_cont_val = dir_cont_sf * sq_ft
        total_direct = dir_site_val + dir_frame_val + dir_mep_val + dir_finish_val + dir_cont_val

    else: # Manual Estimates
        st.markdown("#### Direct Cost Manual Estimates ($)")
        d1, d2 = st.columns(2)
        dir_site_val = auto_num("Site Work, Foundation & Civil Grading ($)", "dir_site_est", 23101.20, container=d1, step=100.0)
        dir_frame_val = auto_num("Framing, Exterior Shell & Roof ($)", "dir_frame_est", 28876.50, container=d1, step=100.0)
        dir_mep_val = auto_num("MEP Rough-Ins ($)", "dir_mep_est", 23101.20, container=d1, step=100.0)
        dir_finish_val = auto_num("Interior Finishes & Drywall ($)", "dir_finish_est", 28876.50, container=d2, step=100.0)
        dir_cont_val = auto_num("Build Contingency ($)", "dir_cont_est", 11550.60, container=d2, step=100.0)

        total_direct = dir_site_val + dir_frame_val + dir_mep_val + dir_finish_val + dir_cont_val

    # Reverse calculation for the UI table
    dir_site_pct_disp = safe_pct(dir_site_val, total_direct)
    dir_frame_pct_disp = safe_pct(dir_frame_val, total_direct)
    dir_mep_pct_disp = safe_pct(dir_mep_val, total_direct)
    dir_finish_pct_disp = safe_pct(dir_finish_val, total_direct)
    dir_cont_pct_disp = safe_pct(dir_cont_val, total_direct)
    dir_target = total_direct / sq_ft if sq_ft > 0 else 0
    
    dir_data = {
        "Direct Category (Construction Stages)": [
            f"Site Work, Foundation & Civil Grading ({dir_site_pct_disp:.2f}%)",
            f"Framing, Exterior Shell & Roof ({dir_frame_pct_disp:.2f}%)",
            f"MEP Rough-Ins ({dir_mep_pct_disp:.2f}%)",
            f"Interior Finishes & Drywall ({dir_finish_pct_disp:.2f}%)",
            f"Build Contingency ({dir_cont_pct_disp:.2f}%)"
        ],
        "Allocated Budget": [
            f"\${dir_site_val:,.2f}", f"\${dir_frame_val:,.2f}", f"\${dir_mep_val:,.2f}", 
            f"\${dir_finish_val:,.2f}", f"\${dir_cont_val:,.2f}"
        ]
    }
    st.table(pd.DataFrame(dir_data))
    st.info(f"🧱 **Direct Total:** \${total_direct:,.2f} (*\${dir_target:,.2f} / sq ft*)")
    st.markdown("---")

    # ==========================================
    # GRAND TOTALS
    # ==========================================
    grand_total = total_indirect + total_direct
    combined_sqft = grand_total / sq_ft if sq_ft > 0 else 0
    
    st.subheader("Grand Project Total")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Project Cost", f"${grand_total:,.2f}")
    m2.metric("Combined Cost / Sq Ft", f"${combined_sqft:,.2f} / sq ft")
    m3.metric("Square Footage Basis", f"{sq_ft:,.0f} sq ft")


# ==========================================
# BANK DRAW SCHEDULE TAB
# ==========================================
with tab_draws:
    st.subheader("🏦 Projected Bank Draw Schedule")
    st.markdown("This schedule maps your direct construction allocations into standard funding draws for the lender.")
    
    c_site = dir_site_val
    c_frame = c_site + dir_frame_val
    c_mep = c_frame + dir_mep_val
    c_finish = c_mep + dir_finish_val
    c_final = c_finish + dir_cont_val
    
    draw_schedule = {
        "Draw Phase": [
            "Draw 1: Site Prep & Foundation",
            "Draw 2: Framing & Dry-In",
            "Draw 3: MEP Rough-Ins",
            "Draw 4: Finishes & Trim-Out",
            "Draw 5: Final Punchlist & CO (Contingency)"
        ],
        "Draw Amount": [
            f"\${dir_site_val:,.2f}", 
            f"\${dir_frame_val:,.2f}", 
            f"\${dir_mep_val:,.2f}", 
            f"\${dir_finish_val:,.2f}", 
            f"\${dir_cont_val:,.2f}"
        ],
        "% of Direct Total": [
            f"{dir_site_pct_disp:.2f}%",
            f"{dir_frame_pct_disp:.2f}%",
            f"{dir_mep_pct_disp:.2f}%",
            f"{dir_finish_pct_disp:.2f}%",
            f"{dir_cont_pct_disp:.2f}%"
        ],
        "Cumulative Funding": [
            f"\${c_site:,.2f}",
            f"\${c_frame:,.2f}",
            f"\${c_mep:,.2f}",
            f"\${c_finish:,.2f}",
            f"\${c_final:,.2f}"
        ]
    }
    
    st.table(pd.DataFrame(draw_schedule))
    st.info("💡 **Note to Developer:** Ensure your inspector signs off on the completed phase at least 5 business days prior to requesting the associated bank draw.")