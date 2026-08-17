import streamlit as st
import pandas as pd
import sqlite3
import json

st.set_page_config(page_title="Cash Flow Forecasting", layout="wide")

# ==========================================
# 🔒 SECURITY & CONTEXT GUARDS
# ==========================================
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# ==========================================
# 💾 DATABASE FETCHING & SAVING
# ==========================================
def get_project_state():
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return {}
    except Exception:
        return {}

def save_forecast_schedule(schedule_data):
    try:
        data = get_project_state()
        data["draw_schedule"] = schedule_data
        conn = sqlite3.connect(DB_FILE)
        conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(data), active_project))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

db_state = get_project_state()

st.title("🔮 Cash Flow Forecasting & Draw Schedule")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Map your total construction budget across the project timeline to generate a precise lender draw schedule and capital requirements forecast.")
st.divider()

# ==========================================
# 📊 SECTION 1: BASE PARAMETERS
# ==========================================
# Default to the baseline estimates saved from the Proforma
saved_estimates = db_state.get("estimates", {})
default_budget = sum(saved_estimates.values()) if saved_estimates else 250000.0

st.subheader("1. Forecast Parameters")
col1, col2 = st.columns(2)
with col1:
    total_budget = st.number_input("Total Project Budget ($)", value=float(default_budget), step=5000.0)
with col2:
    st.info("💡 **Tip:** The total budget defaults to the baseline estimates saved in your Proforma module. You can manually adjust it here to stress-test your cash flow needs.")

st.divider()

# ==========================================
# 🗓️ SECTION 2: DRAW SCHEDULE BUILDER
# ==========================================
st.subheader("2. Milestone & Draw Configuration")
st.markdown("Adjust the percentage of the budget required at each phase. **The total allocation must equal exactly 100%.**")

# Default 6-month build template
default_schedule = [
    {"Month": 1, "Phase": "Site Prep, Civil & Foundation", "Allocation (%)": 15.0},
    {"Month": 2, "Phase": "Framing, Sheathing & Roof Dry-In", "Allocation (%)": 25.0},
    {"Month": 3, "Phase": "MEP Rough-Ins (HVAC, Plumbing, Elec)", "Allocation (%)": 20.0},
    {"Month": 4, "Phase": "Insulation, Drywall & Tape", "Allocation (%)": 15.0},
    {"Month": 5, "Phase": "Interior Finishes, Trim & Paint", "Allocation (%)": 15.0},
    {"Month": 6, "Phase": "Final Grade, CO & Retainage", "Allocation (%)": 10.0},
]

# Load saved schedule or fall back to default
saved_schedule = db_state.get("draw_schedule", default_schedule)
df_schedule = pd.DataFrame(saved_schedule)

# Interactive Data Editor
edited_schedule = st.data_editor(
    df_schedule,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Month": st.column_config.NumberColumn("Month / Draw #", min_value=1, max_value=36, step=1),
        "Phase": st.column_config.TextColumn("Construction Phase"),
        "Allocation (%)": st.column_config.NumberColumn("Allocation (%)", min_value=0.0, max_value=100.0, format="%.1f%%")
    }
)

# Math & Validation
total_pct = edited_schedule["Allocation (%)"].sum()

if round(total_pct, 1) != 100.0:
    st.error(f"⚠️ Current Allocation: **{total_pct:.1f}%**. It must equal exactly **100.0%** before the system can generate accurate charts.")
else:
    st.success("✅ Allocation equals 100%. Draw schedule is balanced.")

    # Calculate actual dollars based on percentages
    edited_schedule["Draw Amount ($)"] = (edited_schedule["Allocation (%)"] / 100.0) * total_budget
    edited_schedule["Cumulative Capital ($)"] = edited_schedule["Draw Amount ($)"].cumsum()

    if st.button("💾 Save Draw Schedule to Project", type="primary"):
        # Save only the configuration columns to DB
        clean_save = edited_schedule[["Month", "Phase", "Allocation (%)"]].to_dict(orient="records")
        if save_forecast_schedule(clean_save):
            st.success("Draw schedule saved successfully!")
        else:
            st.error("Failed to save schedule.")

    st.divider()

    # ==========================================
    # 📈 SECTION 3: VISUALIZATIONS & OUTPUT
    # ==========================================
    st.subheader("3. Capital Deployment Charts")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Monthly Draw Amounts (Burn Rate)**")
        st.bar_chart(edited_schedule.set_index("Month")["Draw Amount ($)"], color="#1a365d")

    with chart_col2:
        st.markdown("**Cumulative Capital Required (S-Curve)**")
        st.line_chart(edited_schedule.set_index("Month")["Cumulative Capital ($)"], color="#d4af37")

    st.divider()

    st.subheader("📋 Final Lender Draw Table")
    st.markdown("Export this data directly to your PDF deal packets or lender presentations.")
    st.dataframe(
        edited_schedule,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Month": "Draw #",
            "Phase": "Milestone description",
            "Allocation (%)": st.column_config.NumberColumn("Allocation", format="%.1f%%"),
            "Draw Amount ($)": st.column_config.NumberColumn("Draw Amount ($)", format="$%.2f"),
            "Cumulative Capital ($)": st.column_config.NumberColumn("Cumulative Capital ($)", format="$%.2f")
        }
    )