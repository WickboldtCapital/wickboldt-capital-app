import streamlit as st
import pandas as pd
from pdf_ops import generate_proforma_pdf
from db_ops import get_project_budget

st.title("Dynamic Scenario Modeling & Proforma 📈")
st.markdown("Stress-test your build-to-rent underwriting with live variables. Hard costs automatically sync with AI-ingested contractor bids and materials.")

# Ensure we have an active project to pull the budget from
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ No active project selected. Please select a project from the sidebar.")
    st.stop()

# --- FETCH INGESTED AI BUDGET DATA ---
budget_df = get_project_budget(active_project)
ingested_hard_costs = 0.0

if not budget_df.empty:
    ingested_hard_costs = float(budget_df["total_cost"].sum())

# --- LAYOUT SETUP ---
col1, col2 = st.columns([1, 3], gap="large")

# --- INTERACTIVE ASSUMPTIONS (LEFT COLUMN) ---
with col1:
    st.header("Assumptions")
    
    st.subheader("Project Scope")
    num_units = st.number_input("Total Units/Lots", min_value=1, max_value=200, value=24)
    
    # Replaced assumed unit cost with actual ingested hard costs + manual base
    base_hard_costs = st.number_input("Base Hard Costs (Manual Entry) ($)", min_value=0.0, value=150000.0, step=5000.0)
    st.info(f"**🤖 AI-Ingested Costs:** ${ingested_hard_costs:,.2f}")
    
    total_hard_costs = base_hard_costs + ingested_hard_costs
    
    st.subheader("Revenue & Operations")
    monthly_rent = st.number_input("Avg Monthly Rent per Unit", min_value=500, max_value=5000, value=1800, step=50)
    opex_ratio = st.slider("Operating Expenses (%)", 10, 50, 35)
    vacancy_rate = st.slider("Vacancy Rate (%)", 0, 20, 5)
    
    st.subheader("Financing")
    equity_target = st.slider("Target Equity Position (%)", 0, 100, 25)
    interest_rate = st.number_input("Debt Interest Rate (%)", 1.0, 15.0, 7.5, step=0.25)

# --- CACHED FINANCIAL ENGINE (PHASE 2 OPTIMIZATION) ---
@st.cache_data(show_spinner=False)
def run_underwriting_engine(units, total_hard_costs, rent, opex, vacancy, equity_pct):
    """
    Cached financial modeling block to prevent UI lag during live slider adjustments.
    """
    # Assuming land/soft costs are baked into the 15% markup for this simplified engine
    total_project_cost = total_hard_costs * 1.15  

    required_equity = total_project_cost * (equity_pct / 100)
    required_debt = total_project_cost - required_equity

    gross_annual_rent = units * rent * 12
    effective_gross_income = gross_annual_rent * (1 - (vacancy / 100))
    net_operating_income = effective_gross_income * (1 - (opex / 100))

    yield_on_cost = (net_operating_income / total_project_cost) * 100 if total_project_cost > 0 else 0

    years = list(range(1, 11))
    cash_flows = [net_operating_income * ((1.03) ** (year - 1)) for year in years]
    cf_df = pd.DataFrame({
        "Year": years,
        "Projected NOI": cash_flows
    })

    return total_project_cost, required_equity, required_debt, net_operating_income, yield_on_cost, cash_flows, cf_df

# Execute calculations via cached function
total_project_cost, required_equity, required_debt, net_operating_income, yield_on_cost, cash_flows, cf_df = run_underwriting_engine(
    num_units, total_hard_costs, monthly_rent, opex_ratio, vacancy_rate, equity_target
)

# --- LIVE METRICS & CHARTS (RIGHT COLUMN) ---
with col2:
    st.header("Deal Metrics")
    
    # Top Level Dashboard
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Project Cost", f"${total_project_cost:,.0f}")
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
        total_project_cost, 
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