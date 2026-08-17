import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Capital Stack & Financing", layout="wide")

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load an authorized project from the Control tab.")
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

# 3. Custom UI Wrappers that prioritize Global Defaults first
def auto_num(label, key, hardcoded_default, container=st, step=None, min_value=None, max_value=None, help=None):
    # Fallback cascade: DB State -> Global Admin Settings -> Hardcoded Backup
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


# --- HELPER FUNCTION FOR NOI MATH ---
def calculate_noi(monthly_rent, vac_pct, exp_mode, exp_pct, itemized_total):
    gross_annual = monthly_rent * 12
    vacancy_amount = gross_annual * (vac_pct / 100)
    egi = gross_annual - vacancy_amount
    
    if exp_mode == "Global Percentage":
        total_exp = egi * (exp_pct / 100)
    else:
        total_exp = itemized_total
        
    noi = egi - total_exp
    return gross_annual, vacancy_amount, egi, total_exp, noi

def render_operating_assumptions(phase_name, default_rent):
    st.markdown(f"**{phase_name} Phase Operating Assumptions**")
    
    op1, op2 = st.columns(2)
    monthly_rent = auto_num(f"Target Monthly Rent ($) [{phase_name}]", f"{phase_name}_rent", default_rent, container=op1, step=100.0)
    vacancy_pct = auto_slider(f"Vacancy Factor (%) [{phase_name}]", f"{phase_name}_vac", 1.0, 15.0, 5.0, container=op2, step=1.0)

    expense_mode = auto_radio(f"Expense Method [{phase_name}]", f"{phase_name}_exp_mode", ["Global Percentage", "Itemized Categories (Annual $)"], horizontal=True)

    if expense_mode == "Global Percentage":
        expense_pct = auto_num(f"Global Operating Expense Ratio (%) [{phase_name}]", f"{phase_name}_exp_pct", 30.0, step=1.0)
        itemized_expenses_annual = 0
    else:
        expense_pct = 0
        st.markdown(f"**Itemized Annual Expenses ($) [{phase_name}]**")
        e1, e2, e3 = st.columns(3)
        taxes = auto_num("Property Taxes ($/yr)", f"{phase_name}_tax", 3500.0, container=e1, step=100.0)
        insurance = auto_num("Insurance ($/yr)", f"{phase_name}_ins", 2000.0, container=e2, step=100.0)
        maint = auto_num("Maintenance/Repairs ($/yr)", f"{phase_name}_maint", 1500.0, container=e3, step=100.0)
        
        e4, e5, e6 = st.columns(3)
        prop_mgmt = auto_num("Property Management ($/yr)", f"{phase_name}_mgmt", 4000.0, container=e4, step=100.0)
        utilities = auto_num("Utilities/Common Area ($/yr)", f"{phase_name}_util", 0.0, container=e5, step=100.0)
        other_exp = auto_num("Other Expenses ($/yr)", f"{phase_name}_other", 500.0, container=e6, step=100.0)
        
        itemized_expenses_annual = taxes + insurance + maint + prop_mgmt + utilities + other_exp

    gross_annual, vacancy_amount, egi, total_exp, noi = calculate_noi(monthly_rent, vacancy_pct, expense_mode, expense_pct, itemized_expenses_annual)
    
    st.info(f"📊 **{phase_name} Phase NOI:** Gross (\${gross_annual:,.2f}) - Vacancy (\${vacancy_amount:,.2f}) - Expenses (\${total_exp:,.2f}) = **\${noi:,.2f}**")
    st.markdown("---")
    
    return noi, gross_annual


# --- HEADER STYLING ---
st.markdown("### 🏗️ Wickboldt Capital: Master Financial Structuring")
st.success(f"🟢 **Active Workspace:** `{st.session_state['active_project']}`")
st.markdown("---")

st.header("Capital Stack & Financing Structure")
st.markdown("Structured capital allocation, debt financing, refinance points, loan payoffs, DSCR analysis, and cash-out settlement.")
st.write("")

# --- INITIALIZE TOP NAVIGATION TABS ---
tab_precon, tab_const, tab_refi, tab_settle = st.tabs([
    "🏗️ Pre-Construction", 
    "🚧 Construction Loan", 
    "🏦 Permanent Refinance", 
    "💰 Settlement & Cash-Out"
])


# ==========================================
# 1. PRE-CONSTRUCTION CAPITAL
# ==========================================
with tab_precon:
    st.subheader("Pre-Construction Capital Allocation")
    pc1, pc2, pc3 = st.columns(3)
    cash_equity = auto_num("Cash Equity Contribution ($)", "precon_cash", 10000.0, container=pc1, step=1000.0)
    land_basis = auto_num("Land Basis / Value ($)", "precon_land", 0.0, container=pc2, step=1000.0)
    dev_time = auto_num("Value of Developer Time/Entitlement ($)", "precon_dev", 0.0, container=pc3, step=1000.0)

    total_pre_con = cash_equity + land_basis + dev_time
    st.metric("Total Pre-Con Equity Basis", f"${total_pre_con:,.2f}")


# ==========================================
# 2. CONSTRUCTION LOAN
# ==========================================
with tab_const:
    st.subheader("Construction Loan Inputs & Structuring")
    
    const_noi, const_gross_annual = render_operating_assumptions("Construction", default_rent=4500.0)

    st.markdown("#### Project Valuation & Loan Sizing")
    val1, val2 = st.columns(2)
    const_val_method = auto_select("Construction Valuation Method", "const_val_method", ["Appraised Value", "Gross Rent Multiplier (GRM)"], container=val1)
    
    if const_val_method == "Appraised Value":
        const_project_value = auto_num("Construction Appraised Value ($)", "const_appraised", 200000.0, container=val2, step=5000.0)
    else:
        const_grm = auto_slider("Construction Gross Rent Multiplier (GRM)", "const_grm", 8.0, 15.0, 10.0, container=val2, step=0.5)
        const_project_value = const_gross_annual * const_grm
        st.info(f"📈 **GRM Valuation:** Gross Annual Rent (\${const_gross_annual:,.2f}) × {const_grm} = **\${const_project_value:,.2f}**")
        
    const_equity_pct = auto_slider("Construction Equity Position (%)", "const_eq_pct", 5.0, 40.0, 25.0, step=5.0)
    
    const_limit = const_project_value * (1 - (const_equity_pct / 100))
    st.info(f"🔗 **Construction Loan Facility:** Calculated from Project Value (\${const_project_value:,.2f}) at {const_equity_pct}% Equity: **\${const_limit:,.2f}**")
    st.markdown("---")

    st.markdown("#### A. Bank Underwriting & DSCR Qualification")
    
    uw1, uw2 = st.columns(2)
    uw_rate = auto_slider("Bank Underwriting Interest Rate (%)", "const_uw_rate", 0.0, 15.0, 7.50, container=uw1, step=0.25, help="Theoretical rate used only for DSCR qualification.")
    target_const_dscr = auto_num("Target Construction DSCR Threshold", "const_tgt_dscr", 1.20, container=uw2, step=0.05)
    
    uw_annual_interest = const_limit * (uw_rate / 100)
    const_dscr = const_noi / uw_annual_interest if uw_annual_interest > 0 else 0

    st.metric("Underwriting DSCR", f"{const_dscr:.2f}x")
    if const_dscr >= target_const_dscr:
        st.success(f"✅ **PASS:** Underwriting DSCR ({const_dscr:.2f}x) meets bank target ({target_const_dscr:.2f}x)")
    else:
        st.error(f"❌ **FAIL:** Underwriting DSCR ({const_dscr:.2f}x) is below bank target ({target_const_dscr:.2f}x)")

    st.markdown("---")
    
    st.markdown("#### B. Actual Construction Loan Mechanics & Interest Cost")
    
    cl1, cl2, cl3 = st.columns(3)
    const_rate = auto_slider("Actual Construction Interest Rate (%)", "const_act_rate", 0.0, 15.0, 6.25, container=cl1, step=0.25)
    const_term = auto_num("Construction Term (Months)", "const_term", 12.0, container=cl2, step=1.0)
    avg_draw_pct = auto_slider("Average Drawn Balance (%)", "const_draw_pct", 10.0, 100.0, 50.0, container=cl3, step=5.0)

    const_closing = auto_num("Construction Loan Closing Costs ($)", "const_close", 0.0, step=500.0)

    actual_interest_cost = const_limit * (const_rate / 100) * (const_term / 12) * (avg_draw_pct / 100)
    
    st.info(f"💸 **Estimated Total Interest Cost:** Based on a {const_term}-month schedule at an average drawn balance of {avg_draw_pct}%, the total interest cost will be **\${actual_interest_cost:,.2f}**.")


# ==========================================
# 3. PERMANENT REFINANCE LOAN
# ==========================================
with tab_refi:
    st.subheader("Permanent Refinance Loan, Equity, Points & DSCR Analysis")

    refi_noi, refi_gross_annual = render_operating_assumptions("Refinance", default_rent=5100.0)

    st.markdown("#### Project Valuation & Loan Sizing")
    r_val1, r_val2 = st.columns(2)
    refi_val_method = auto_select("Refinance Valuation Method", "refi_val_method", ["Appraised Value", "Gross Rent Multiplier (GRM)"], container=r_val1)
    
    if refi_val_method == "Appraised Value":
        refi_project_value = auto_num("Refinance Appraised Value ($)", "refi_appraised", 230000.0, container=r_val2, step=5000.0)
    else:
        refi_grm = auto_slider("Refinance Gross Rent Multiplier (GRM)", "refi_grm", 8.0, 15.0, 10.0, container=r_val2, step=0.5)
        refi_project_value = refi_gross_annual * refi_grm
        st.info(f"📈 **GRM Valuation:** Gross Annual Rent (\${refi_gross_annual:,.2f}) × {refi_grm} = **\${refi_project_value:,.2f}**")

    refi_equity_pct = auto_slider("Refinance Equity Position (%)", "refi_eq_pct", 5.0, 40.0, 35.0, step=5.0) 
    
    refi_loan_amt = refi_project_value * (1 - (refi_equity_pct / 100))
    st.info(f"🔗 **Refinance Loan Amount:** Calculated from Project Value (\${refi_project_value:,.2f}) at {refi_equity_pct}% Equity: **\${refi_loan_amt:,.2f}**")
    st.markdown("---")

    st.markdown("#### Refinance Terms & DSCR Qualification")
    rl3, rl4, rl5 = st.columns(3)
    base_refi_rate = auto_slider("Base Refi Interest Rate (%)", "refi_base_rate", 0.0, 10.0, 6.25, container=rl3, step=0.125)
    refi_points = auto_slider("Refinance Points (%)", "refi_points", 0.0, 4.0, 3.0, container=rl4, step=0.25)
    refi_closing_base = auto_num("Refinance Base Closing Costs ($)", "refi_close", 515.0, container=rl5, step=100.0)

    rl6, rl7 = st.columns(2)
    amort_years = auto_num("Amortization (Years)", "refi_amort", 30.0, container=rl6, step=5.0)
    target_refi_dscr = auto_num("Target Permanent Refi DSCR Threshold", "refi_tgt_dscr", 1.20, container=rl7, step=0.05)

    effective_rate = base_refi_rate - (refi_points * 0.25)
    total_points_cost = refi_loan_amt * (refi_points / 100)
    total_refi_closing = refi_closing_base + total_points_cost

    r_monthly = (effective_rate / 100) / 12
    n_months = amort_years * 12
    if r_monthly > 0:
        monthly_ads = refi_loan_amt * (r_monthly * (1 + r_monthly)**n_months) / ((1 + r_monthly)**n_months - 1)
    else:
        monthly_ads = refi_loan_amt / n_months

    annual_ads = monthly_ads * 12
    refi_dscr = refi_noi / annual_ads if annual_ads > 0 else 0

    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Effective Refi Interest Rate (After Points)", f"{effective_rate:.2f}%")
    m2.metric("Total Cost of Refi Points", f"${total_points_cost:,.2f}")
    m3.metric("Permanent Monthly ADS", f"${monthly_ads:,.2f}")

    st.metric("Refinance Loan DSCR", f"{refi_dscr:.2f}x")
    if refi_dscr >= target_refi_dscr:
        st.success(f"✅ **PASS:** Refi DSCR ({refi_dscr:.2f}x) meets bank target ({target_refi_dscr:.2f}x)")
    else:
        st.error(f"❌ **FAIL:** Refi DSCR ({refi_dscr:.2f}x) is below bank target ({target_refi_dscr:.2f}x)")


# ==========================================
# 4. SETTLEMENT & CASH-OUT (ENTERPRISE UPGRADE)
# ==========================================
with tab_settle:
    st.subheader("Refinance Takeout & Settlement Waterfall")
    st.markdown("Visual breakdown of the final takeout transaction and developer equity extraction.")

    net_cash_out = refi_loan_amt - const_limit - total_refi_closing - total_pre_con

    # Enterprise Metric Highlight
    s1, s2, s3 = st.columns(3)
    s1.metric("Gross Refinance Proceeds", f"${refi_loan_amt:,.2f}")
    s2.metric("Total Capital Obligations", f"${(const_limit + total_refi_closing + total_pre_con):,.2f}")
    
    if net_cash_out >= 0:
        s3.metric("Net Developer Cash-Out", f"${net_cash_out:,.2f}", "+ Profit Yielded")
    else:
        s3.metric("Capital Shortfall to Close", f"${abs(net_cash_out):,.2f}", "- Additional Equity Required")

    st.divider()

    col_table, col_summary = st.columns([2, 1], gap="large")
    
    with col_table:
        st.markdown("**Settlement Ledger**")
        settlement_data = {
            "Settlement Line Item": [
                "Gross Permanent Refinance Loan Proceeds",
                "Less: Construction Loan Principal Payoff",
                "Less: Refinance Closing Costs & Rate Buy-Down Points",
                "Less: Initial Pre-Construction Capital Recovery"
            ],
            "Amount ($)": [
                f"${refi_loan_amt:,.2f}",
                f"-${const_limit:,.2f}",
                f"-${total_refi_closing:,.2f}",
                f"-${total_pre_con:,.2f}"
            ]
        }
        st.dataframe(pd.DataFrame(settlement_data), use_container_width=True, hide_index=True)
        
    with col_summary:
        st.markdown("**Capital Velocity Analysis**")
        if net_cash_out >= 0:
            st.success(f"**Stabilized Extraction Achieved.**\nThe permanent takeout facility is sufficient to retire the `{const_limit:,.0f}` construction note, cover all settlement charges, fully reimburse the original `{total_pre_con:,.0f}` pre-construction capital basis, and extract a net `{net_cash_out:,.0f}` liquid dividend.")
        else:
            st.error(f"**Capital Trapped.**\nThe permanent takeout facility fails to cover the cumulative basis. An additional cash injection of `${abs(net_cash_out):,.2f}` is required at the closing table to satisfy the construction note payoff and settlement charges.")