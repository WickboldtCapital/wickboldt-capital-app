import streamlit as st
import pandas as pd

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# ==========================================
# 🛡️ SANDBOXED EXECUTION BLOCK
# ==========================================
try:
    st.header("📈 Financial Proforma & Underwriting")
    st.markdown(f"**Active Development:** `{st.session_state['active_project']}`")
    st.markdown("---")

    st.subheader("Development Assumptions")
    col1, col2, col3 = st.columns(3)

    # ⚡ NAMESPACING: Notice the key="prof_..." added to every single input
    with col1:
        unit_count = st.number_input("Total Units/Lots", value=3, min_value=1, key="prof_unit_count")
        land_cost = st.number_input("Total Land Cost ($)", value=120000.0, step=10000.0, key="prof_land_cost")
    with col2:
        cost_per_unit = st.number_input("Construction Cost per Unit ($)", value=185000.0, step=5000.0, key="prof_cost_per_unit")
        monthly_rent = st.number_input("Target Monthly Rent per Unit ($)", value=1850.0, step=50.0, key="prof_monthly_rent")
    with col3:
        exit_cap_rate = st.number_input("Exit Cap Rate (%)", value=6.5, step=0.25, key="prof_exit_cap")
        # Equity target maintains the 30% baseline standard
        equity_pct_input = st.slider("Target Equity Position (%)", min_value=0.0, max_value=100.0, value=30.0, step=5.0, key="prof_equity_pct")
        equity_pct = equity_pct_input / 100.0

    # --- FINANCIAL CALCULATIONS ---
    total_construction = unit_count * cost_per_unit
    total_project_cost = land_cost + total_construction
    required_equity = total_project_cost * equity_pct
    required_debt = total_project_cost - required_equity
    
    annual_gross_income = unit_count * monthly_rent * 12
    noi = annual_gross_income * 0.65
    stabilized_value = noi / (exit_cap_rate / 100)
    projected_margin = stabilized_value - total_project_cost

    # --- UI RENDERING ---
    st.markdown("---")
    st.subheader("Capital Stack & Valuation")
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Total Project Cost", f"${total_project_cost:,.0f}")
    metric2.metric(f"Required Equity ({equity_pct_input}%)", f"${required_equity:,.0f}")
    metric3.metric("Debt Facility Required", f"${required_debt:,.0f}")
    metric4.metric("Stabilized Valuation", f"${stabilized_value:,.0f}")

    st.markdown("---")
    st.subheader("Operating Projections")
    st.dataframe(pd.DataFrame({
        "Metric": ["Annual Gross Revenue", "Net Operating Income (NOI)", "Projected Margin (Equity Creation)"],
        "Value": [f"${annual_gross_income:,.0f}", f"${noi:,.0f}", f"${projected_margin:,.0f}"]
    }), use_container_width=True, hide_index=True)

# 🛡️ ERROR TRAP: Catches any math or typo errors without crashing the main app
except Exception as e:
    st.error("🚨 An error occurred in the Proforma module. The rest of the app is still running safely.")
    st.code(str(e))