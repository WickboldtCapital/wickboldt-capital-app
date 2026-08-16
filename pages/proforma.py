import streamlit as st
import pandas as pd
import sqlite3
import json
from pdf_ops import generate_proforma_pdf
from db_ops import get_project_budget

st.set_page_config(page_title="Dynamic Scenario Modeling & Proforma", layout="wide")

st.title("Dynamic Scenario Modeling & Proforma 📈")
st.markdown("Stress-test your build-to-rent underwriting with live variables. Hard costs automatically sync with your Estimator module and AI-ingested bids.")

# Ensure we have an active project to pull the budget from
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ No active project selected. Please select a project from the sidebar.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- DB HELPERS ---
def get_db_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

def auto_save(key):
    val = st.session_state[key]
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
    current_state = json.loads(row[0]) if row and row[0] else {}
    current_state[key] = val
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
    conn.commit()
    conn.close()

db_state = get_db_state()
budget_df = get_project_budget(active_project)

ingested_hard_costs = 0.0
if not budget_df.empty:
    ingested_hard_costs = float(budget_df["total_cost"].sum())

# --- Reconstruct Direct Cost Baseline from Estimator ---
sq_ft = float(db_state.get("est_sq_ft", 1150.0))
dir_mode = db_state.get("dir_calc_method", "Percentage Breakdown (Top-Down)")
if dir_mode == "Percentage Breakdown (Top-Down)":
    if db_state.get("est_dir_method", "Target $ / Sq Ft") == "Target $ / Sq Ft":
        est_direct = float(db_state.get("est_dir_target", 100.44)) * sq_ft
    else:
        est_direct = float(db_state.get("est_dir_target_total", 115506.0))
elif dir_mode == "Cost per Sq Ft (Bottom-Up)":
    val = sum([float(db_state.get(k, v)) for k, v in [("dir_site_sf", 20.09), ("dir_frame_sf", 25.11), ("dir_mep_sf", 20.09), ("dir_finish_sf", 25.11), ("dir_cont_sf", 10.04)]])
    est_direct = val * sq_ft
else:
    est_direct = sum([float(db_state.get(k, v)) for k, v in [("dir_site_est", 23101.2), ("dir_frame_est", 28876.5), ("dir_mep_est", 23101.2), ("dir_finish_est", 28876.5), ("dir_cont_est", 11550.6)]])

# --- Reconstruct Indirect Cost Baseline from Estimator ---
ind_mode = db_state.get("ind_calc_method", "Percentage Breakdown (Top-Down)")
if ind_mode == "Percentage Breakdown (Top-Down)":
    if db_state.get("est_ind_method", "Target $ / Sq Ft") == "Target $ / Sq Ft":
        est_indirect = float(db_state.get("est_ind_target", 70.24)) * sq_ft
    else:
        est_indirect = float(db_state.get("est_ind_target_total", 80770.85))
elif ind_mode == "Cost per Sq Ft (Bottom-Up)":
    est_indirect = sum([float(db_state.get(k, v)) for k, v in [("ind_land_sf", 8.19), ("ind_gc_sf", 8.19), ("ind_soft_sf", 4.10), ("ind_r_close_sf", 4.10), ("ind_res_sf", 32.81)]]) * sq_ft
else:
    est_indirect = sum([float(db_state.get(k, v)) for k, v in [("ind_land_est", 9997.75), ("ind_gc_est", 9997.75), ("ind_soft_est", 4998.88), ("ind_r_close_est", 4998.88), ("ind_res_est", 40059.6)]])

baseline_total = est_direct + est_indirect
adjusted_total_cost = baseline_total if ingested_hard_costs == 0 else ingested_hard_costs + max(0, baseline_total - ingested_hard_costs)

# --- LAYOUT SETUP ---
col1, col2 = st.columns([1, 3], gap="large")

# --- INTERACTIVE ASSUMPTIONS (LEFT COLUMN) ---
with col1:
    st.header("Assumptions")
    
    st.subheader("Project Scope")
    num_units = st.number_input("Total Units/Lots", min_value=1, max_value=200, value=24)
    
    st.info(f"**🏗️ Est. Baseline:** ${baseline_total:,.2f}")
    st.info(f"**🤖 AI-Ingested:** ${ingested_hard_costs:,.2f}")
    
    st.subheader("Revenue & Operations")
    monthly_rent = st.number_input(
        "Avg Monthly Rent per Unit", 
        min_value=500, max_value=5000, 
        value=int(db_state.get("proforma_rent", 1800)), 
        step=50,
        key="proforma_rent",
        on_change=auto_save, args=("proforma_rent",)
    )
    opex_ratio = st.slider(
        "Operating Expenses (%)", 10, 50, 
        value=int(db_state.get("proforma_opex", 35)),
        key="proforma_opex",
        on_change=auto_save, args=("proforma_opex",)
    )
    vacancy_rate = st.slider(
        "Vacancy Rate (%)", 0, 20, 
        value=int(db_state.get("proforma_vacancy", 5)),
        key="proforma_vacancy",
        on_change=auto_save, args=("proforma_vacancy",)
    )
    
    st.subheader("Financing")
    equity_target = st.slider(
        "Target Equity Position (%)", 0, 100, 
        value=int(db_state.get("const_eq_pct", 25)),
        key="const_eq_pct",
        on_change=auto_save, args=("const_eq_pct",)
    )

# --- CACHED FINANCIAL ENGINE ---
@st.cache_data(show_spinner=False)
def run_underwriting_engine(units, total_cost, rent, opex, vacancy, equity_pct):
    required_equity = total_cost * (equity_pct / 100)
    required_debt = total_cost - required_equity

    gross_annual_rent = units * rent * 12
    effective_gross_income = gross_annual_rent * (1 - (vacancy / 100))
    net_operating_income = effective_gross_income * (1 - (opex / 100))

    yield_on_cost = (net_operating_income / total_cost) * 100 if total_cost > 0 else 0

    years = list(range(1, 11))
    cash_flows = [net_operating_income * ((1.03) ** (year - 1)) for year in years]
    cf_df = pd.DataFrame({
        "Year": years,
        "Projected NOI": cash_flows
    })

    return required_equity, required_debt, net_operating_income, yield_on_cost, cash_flows, cf_df

# Execute calculations
required_equity, required_debt, net_operating_income, yield_on_cost, cash_flows, cf_df = run_underwriting_engine(
    num_units, adjusted_total_cost, monthly_rent, opex_ratio, vacancy_rate, equity_target
)

# --- LIVE METRICS & CHARTS (RIGHT COLUMN) ---
with col2:
    st.header("Deal Metrics")
    
    # Top Level Dashboard
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Adjusted Project Cost", f"${adjusted_total_cost:,.0f}")
    m2.metric("Required Equity", f"${required_equity:,.0f}")
    m3.metric("Annual NOI", f"${net_operating_income:,.0f}")
    m4.metric("Yield on Cost (Cap)", f"{yield_on_cost:.2f}%")
    
    st.divider()
    
    chart_col1, chart_col2 = st.columns(2)
    
    # Capital Stack Visual
    with chart_col1:
        st.subheader("Capital Stack Breakdown")
        stack_data = pd.DataFrame({
            "Source": ["Equity", "Debt"],
            "Amount": [required_equity, required_debt]
        })
        st.bar_chart(stack_data.set_index("Source"), color="#2b6cb0")
        
    # Cash Flow Projections (10 Year)
    with chart_col2:
        st.subheader("10-Year NOI Projection")
        st.caption("Assuming 3% Annual Rent Growth")
        st.line_chart(cf_df.set_index("Year"), color="#2f855a")
        
    st.divider()
    
    # Raw Data Table Export
    with st.expander("View Full Amortization & Raw Data"):
        st.dataframe(cf_df.style.format({"Projected NOI": "${:,.2f}"}), use_container_width=True)
        
    st.divider()
    
    # AI Budget Breakdown Table
    st.subheader("AI Budget Breakdown")
    if not budget_df.empty:
        st.markdown("These line items were automatically extracted from bids/invoices and are actively driving your total hard costs.")
        st.dataframe(
            budget_df[["created_at", "category", "vendor_name", "description", "qty", "unit_cost", "total_cost"]], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No AI-ingested budget items found for this project. Upload bids via the AI Bid Ingestion tool to automatically populate this section.")
        
    st.divider()
    
    # PDF Generation & Download
    st.subheader("Export Deal Packet")
    pdf_bytes = generate_proforma_pdf(
        adjusted_total_cost, 
        required_equity, 
        net_operating_income, 
        yield_on_cost, 
        cash_flows
    )
    
    st.download_button(
        label="📄 Download Proforma PDF",
        data=pdf_bytes,
        file_name="Wickboldt_Capital_Proforma.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )