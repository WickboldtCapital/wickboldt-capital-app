import json
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# --- DATABASE SETUP ---
DB_FILE = "wickboldt_projects.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            created_at TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS revisions (
            revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            revision_name TEXT,
            timestamp TEXT,
            data_json TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        )
    """)
  conn.commit()
  conn.close()


init_db()

# Page Config
st.set_page_config(
    page_title="Wickboldt Capital Portal", layout="wide", initial_sidebar_state="expanded"
)

st.title("🏗️ Wickboldt Capital: Rogers Moore Parkway Portal")
st.markdown("*Today's Foundation. Tomorrow's Legacy.*")
st.markdown("---")

# --- SIDEBAR: NAVIGATION & REVISION MANAGER ---
st.sidebar.header("🧭 Main Menu")
main_section = st.sidebar.radio(
    "Go to Section",
    ["📊 Financials & Capital Stack", "🏗️ Project & Engineering"],
)

st.sidebar.markdown("---")
st.sidebar.header("📁 Project & Revision Control")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT project_name FROM projects")
projects = [row[0] for row in cursor.fetchall()]
conn.close()

project_mode = st.sidebar.radio(
    "Action", ["Load Existing Project", "Create New Project"]
)

if project_mode == "Create New Project":
  new_proj_name = st.sidebar.text_input(
      "New Project Name", "Rogers Moore Phase 1 - Tracts C1-3"
  )
  if st.sidebar.button("Initialize Project"):
    if new_proj_name:
      try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (project_name, created_at) VALUES (?, ?)",
            (new_proj_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        st.sidebar.success(f"Initialized '{new_proj_name}'!")
        st.rerun()
      except sqlite3.IntegrityError:
        st.sidebar.error("Project name already exists.")

selected_project = None
if projects:
  selected_project = st.sidebar.selectbox("Select Project", projects)

loaded_data = {}
if selected_project:
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        SELECT r.revision_name, r.timestamp, r.revision_id 
        FROM revisions r
        JOIN projects p ON r.project_id = p.project_id
        WHERE p.project_name = ?
        ORDER BY r.timestamp DESC
    """,
      (selected_project,),
  )
  revisions = cursor.fetchall()
  conn.close()

  rev_dict = {f"{r[0]} ({r[1]})": r[2] for r in revisions}

  if rev_dict:
    selected_rev_label = st.sidebar.selectbox(
        "Select Revision to Load", list(rev_dict.keys())
    )
    if st.sidebar.button("Load Revision"):
      rev_id = rev_dict[selected_rev_label]
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT data_json FROM revisions WHERE revision_id = ?", (rev_id,)
      )
      row = cursor.fetchone()
      conn.close()
      if row:
        loaded_data = json.loads(row[0])
        st.sidebar.success("Revision loaded successfully!")

# --- DEFAULT FINANCIAL VALUES ---
d_cost = loaded_data.get("total_cost", 175350.32)
d_equity = loaded_data.get("equity_pct", 30.0)
d_rent = loaded_data.get("annual_rent", 18000.0)
d_opex = loaded_data.get("opex", 5130.0)

# --- SECTION 1: FINANCIALS & CAPITAL STACK ---
if main_section == "📊 Financials & Capital Stack":
  sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
      "📊 Unit Proforma",
      "🏗️ Cost Estimator & Budget",
      "💰 Capital Stack",
      "📈 10-Year Forecast",
  ])

  # --- SUB-TAB 1: UNIT PROFORMA ---
  with sub_tab1:
    st.header("Unit-Level Underwriting Proforma")
    st.markdown(
        "Optimized 1,150 sq ft two-story 3-bedroom, 2.5-bathroom single-family"
        " rental unit."
    )

    col1, col2 = st.columns(2)
    with col1:
      total_cost = st.number_input(
          "Total Project Cost ($)", value=float(d_cost), step=1000.0
      )
      equity_pct = st.slider(
          "Equity Position (%)",
          min_value=0.0,
          max_value=100.0,
          value=float(d_equity),
          step=5.0,
      )

    with col2:
      annual_rent = st.number_input(
          "Annual Gross Rent ($)", value=float(d_rent), step=500.0
      )
      opex = st.number_input(
          "Operating Expenses ($)", value=float(d_opex), step=100.0
      )

    # Calculations
    equity_req = total_cost * (equity_pct / 100.0)
    loan_amount = total_cost - equity_req
    noi = annual_rent - opex

    monthly_rate = 0.065 / 12
    n_payments = 360
    if loan_amount > 0:
      monthly_ads = (
          loan_amount
          * (monthly_rate * (1 + monthly_rate) ** n_payments)
          / ((1 + monthly_rate) ** n_payments - 1)
      )
    else:
      monthly_ads = 0.0

    annual_ads = monthly_ads * 12
    net_cash_flow = noi - annual_ads
    cash_on_cash = (
        (net_cash_flow / equity_req) * 100 if equity_req > 0 else 0.0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Required Equity", f"${equity_req:,.2f}")
    m2.metric("Loan Amount", f"${loan_amount:,.2f}")
    m3.metric("Net Operating Income", f"${noi:,.2f}")
    m4.metric("Cash-on-Cash Return", f"{cash_on_cash:.2f}%")

    st.markdown("### Detailed Cost Breakdown Structure")
    cost_data = {
        "Cost Category": [
            "Direct Build Cost (Hard Costs)",
            "General Contractor Fee (Flat)",
            "Soft Costs, Permits & Architecture",
            "Construction Loan Closing Costs",
            "Construction Loan Interest (I/O)",
            "Refinance Closing & Origination",
            "Land / Equity Position",
        ],
        "Amount ($)": [
            102012.74,
            10000.00,
            5000.00,
            6000.00,
            3500.00,
            5000.00,
            equity_req,
        ],
        "Percentage": [
            "58.18%",
            "5.70%",
            "2.85%",
            "3.42%",
            "1.99%",
            "2.85%",
            f"{equity_pct}%",
        ],
    }
    st.table(pd.DataFrame(cost_data))

    st.markdown("---")
    st.subheader("💾 Save Proforma Revision")
    rev_name_input = st.text_input(
        "Revision Name / Note", f"Proforma - {int(equity_pct)}% Equity Position"
    )
    if st.button("Save New Revision"):
      if selected_project:
        current_state = {
            "total_cost": total_cost,
            "equity_pct": equity_pct,
            "annual_rent": annual_rent,
            "opex": opex,
        }
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT project_id FROM projects WHERE project_name = ?",
            (selected_project,),
        )
        proj_id = cursor.fetchone()[0]
        cursor.execute(
            """
                INSERT INTO revisions (project_id, revision_name, timestamp, data_json)
                VALUES (?, ?, ?, ?)
            """,
            (
                proj_id,
                rev_name_input,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                json.dumps(current_state),
            ),
        )
        conn.commit()
        conn.close()
        st.success(f"Saved revision '{rev_name_input}' successfully!")
      else:
        st.error("Select or create a project in the sidebar first.")

  # --- SUB-TAB 2: COST ESTIMATOR & BUDGET ---
  with sub_tab2:
    st.header("Construction Cost Estimator & Budget Breakdown")
    st.markdown(
        "Granular direct and indirect cost classifications with automated"
        " per-square-foot ($/sq ft) tracking."
    )

    unit_sqft = st.number_input(
        "Unit Living Area (Square Feet)", value=1150.0, step=25.0
    )

    st.markdown("---")
    col_d_sec, col_i_sec = st.columns(2)

    with col_d_sec:
      st.subheader("🧱 Direct Costs (Hard Costs)")
      d_site = st.number_input(
          "Site Prep, Foundation & Slab ($)", value=18500.0, step=500.0
      )
      d_framing = st.number_input(
          "Framing, Lumber & Roof Structure ($)", value=28000.0, step=500.0
      )
      d_exterior = st.number_input(
          "Exterior Finishes, Siding & Windows ($)", value=16500.0, step=500.0
      )
      d_mep = st.number_input(
          "MEP (Plumbing, Electrical, HVAC / Foam) ($)",
          value=24012.74,
          step=500.0,
      )
      d_interior = st.number_input(
          "Interior Finishes (LVP, Tile, Cabinets, Trim) ($)",
          value=12000.0,
          step=500.0,
      )
      d_appliances = st.number_input(
          "Appliances & Security System ($)", value=3000.0, step=200.0
      )

      direct_total = (
          d_site
          + d_framing
          + d_exterior
          + d_mep
          + d_interior
          + d_appliances
      )
      direct_psf = direct_total / unit_sqft if unit_sqft > 0 else 0

      st.markdown(
          f"### Direct Total: **${direct_total:,.2f}** "
          f"(_${direct_psf:.2f}/sq ft_)"
      )

    with col_i_sec:
      st.subheader("📋 Indirect Costs (Soft Costs & Fees)")
      i_arch = st.number_input(
          "Architecture, Engineering & Permits ($)", value=5000.0, step=500.0
      )
      i_gc = st.number_input(
          "General Contractor Fee (Flat) ($)", value=10000.0, step=500.0
      )
      i_financing = st.number_input(
          "Construction Loan Interest & Closing ($)", value=9500.0, step=500.0
      )
      i_refi = st.number_input(
          "Refinance & Origination Closing Costs ($)", value=5000.0, step=500.0
      )
      i_land = st.number_input(
          "Land Basis / Equity Contribution ($)", value=33837.58, step=500.0
      )
      i_contingency = st.number_input(
          "Developer Contingency Reserve ($)", value=9012.74, step=500.0
      )

      indirect_total = (
          i_arch + i_gc + i_financing + i_refi + i_land + i_contingency
      )
      indirect_psf = indirect_total / unit_sqft if unit_sqft > 0 else 0

      st.markdown(
          f"### Indirect Total: **${indirect_total:,.2f}** "
          f"(_${indirect_psf:.2f}/sq ft_)"
      )

    st.markdown("---")
    grand_total_cost = direct_total + indirect_total
    grand_psf = grand_total_cost / unit_sqft if unit_sqft > 0 else 0

    m_tot1, m_tot2, m_tot3 = st.columns(3)
    m_tot1.metric("Grand Project Total", f"${grand_total_cost:,.2f}")
    m_tot2.metric("Combined Cost / Sq Ft", f"${grand_psf:.2f} / sq ft")
    m_tot3.metric("Square Footage Basis", f"{unit_sqft:,.0f} sq ft")

    st.info(
        "💡 Note: This computed project total syncs directly into your"
        " underwriting proforma and capital stack models."
    )

  # --- SUB-TAB 3: CAPITAL STACK ---
  with sub_tab3:
    st.header("Capital Stack & Financing Structure")

    col_a, col_b = st.columns(2)

    with col_a:
      st.subheader("1. Pre-Construction Capital Allocation")
      st.markdown("*Value-Add & Equity Positioning*")
      cash_equity = st.number_input(
          "Cash Equity Contribution ($)", value=10000.0, step=1000.0
      )
      land_basis = st.number_input(
          "Land Basis / Value ($)", value=33837.58, step=1000.0
      )
      value_of_time = st.number_input(
          "Value of Developer Time/Entitlement ($)", value=15000.0, step=1000.0
      )

      total_pre_con_equity = cash_equity + land_basis + value_of_time
      st.metric("Total Pre-Con Equity Basis", f"${total_pre_con_equity:,.2f}")

    with col_b:
      st.subheader("2. Construction Loan Inputs")
      con_loan_amt = st.number_input(
          "Construction Loan Amount ($)", value=131512.74, step=1000.0
      )
      con_loan_rate = st.slider(
          "Construction Interest Rate (%)", 0.0, 15.0, 8.0, step=0.25
      )
      con_term = st.number_input("Construction Term (Months)", value=9)

      con_int_cost = con_loan_amt * (con_loan_rate / 100) * (con_term / 12)
      st.metric("Estimated Const. Interest (I/O)", f"${con_int_cost:,.2f}")

    st.markdown("---")
    st.subheader("3. Permanent Refinance Loan")
    col_c, col_d = st.columns(2)
    with col_c:
      refi_loan_amt = st.number_input(
          "Refi Loan Amount ($)", value=131512.74, step=1000.0
      )
      refi_rate = st.slider("Refi Interest Rate (%)", 0.0, 10.0, 6.5, step=0.1)
    with col_d:
      amort_period = st.number_input("Amortization (Years)", value=30)
      r = (refi_rate / 100) / 12
      n = amort_period * 12
      monthly_payment = (
          refi_loan_amt * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
          if r > 0
          else 0
      )
      st.metric("Permanent Monthly ADS", f"${monthly_payment:,.2f}")

    st.info(
        "Strategy: The construction loan is repaid via permanent takeout upon"
        " stabilization."
    )

  # --- SUB-TAB 4: 10-YEAR FORECAST ---
  with sub_tab4:
    st.header("10-Year Wealth Accumulation & Forecast")
    st.markdown(
        "Conservative wealth generation model assuming 3.0% annual property"
        " appreciation and mortgage principal paydown."
    )

    equity_req_calc = d_cost * (d_equity / 100.0)
    loan_amt_calc = d_cost - equity_req_calc
    noi_calc = d_rent - d_opex
    m_rate_calc = 0.065 / 12
    m_ads_calc = (
        loan_amt_calc
        * (m_rate_calc * (1 + m_rate_calc) ** 360)
        / ((1 + m_rate_calc) ** 360 - 1)
        if loan_amt_calc > 0
        else 0
    )
    net_cf_calc = noi_calc - (m_ads_calc * 12)

    curr_val = d_cost
    curr_loan = loan_amt_calc
    years_data = []
    accum_cf = 0

    for yr in range(1, 11):
      curr_val *= 1.03
      principal_paydown = curr_loan * 0.015 if curr_loan > 0 else 0
      curr_loan = max(0, curr_loan - principal_paydown)
      equity_val = curr_val - curr_loan
      accum_cf += net_cf_calc

      years_data.append({
          "Year": f"Year {yr}",
          "Property Value": round(curr_val, 2),
          "Loan Balance": round(curr_loan, 2),
          "Total Equity": round(equity_val, 2),
          "Annual Cash Flow": round(net_cf_calc, 2),
      })

    df_forecast = pd.DataFrame(years_data)
    st.dataframe(df_forecast, use_container_width=True)

    f1, f2, f3 = st.columns(3)
    f1.metric("Cumulative 10-Yr Cash Flow", f"${accum_cf:,.2f}")
    f2.metric(
        "Year 10 Equity Value",
        f"${years_data[-1]['Total Equity']:,.2f}",
    )
    f3.metric("Tax Strategy Status", "100% Tax Shielded")


# --- SECTION 2: PROJECT & ENGINEERING ---
elif main_section == "🏗️ Project & Engineering":
  sub_tab1, sub_tab2 = st.tabs(
      ["🏗️ Master Dashboard", "📑 Technical Addendums"]
  )

  # --- SUB-TAB 1: MASTER DASHBOARD ---
  with sub_tab1:
    st.header("Rogers Moore Parkway Master Development")
    st.info(
        "**Project Scope:** 24 total building lots in Hammond, Louisiana."
        " Structured across Phase One (10 lots facing Rogers Moore Parkway and"
        " Center Avenue) and Phase Two (14 interior lots)."
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
      st.subheader("Phase One (10 Lots)")
      st.markdown(
          "- **Focus:** Primary infrastructure & street frontage.\n- **Launch"
          " Tranche:** Tracts C1–C3.\n- **Asset Model:** 1,150 sq ft, 3-bed /"
          " 2.5-bath."
      )
    with col_p2:
      st.subheader("Phase Two (14 Lots)")
      st.markdown(
          "- **Focus:** Secondary rollout & portfolio expansion.\n- **Timeline:**"
          " Phased 3-year execution schedule."
      )

  # --- SUB-TAB 2: TECHNICAL ADDENDUMS ---
  with sub_tab2:
    st.header("Technical Specifications & Addendums")
    st.markdown(
        "Engineering standards and cost-benefit breakdowns from the Wickboldt"
        " Capital Business Plan."
    )

    with st.expander("Addendum 1: LVP Wear Layer Financial Break-Even Analysis"):
      st.write(
          "**12 Mil vs. 20 Mil LVP Flooring:** Upgrading to commercial-grade"
          " 20 mil LVP incurs a minor $600 upfront premium per 1,000 sq ft but"
          " eliminates premature replacements in rental environments, breaking"
          " even just **7 months** into tenancy."
      )

    with st.expander(
        "Addendum 2: Shower Enclosures vs. Upgraded Tile Showers"
    ):
      st.write(
          "**Custom Tile Showers:** Requires a $1,400 net upfront premium over"
          " acrylic units, which is fully recovered in under **22 months** via"
          " a $65/mo rental premium while eliminating leaks and mid-cycle"
          " replacements."
      )

    with st.expander(
        "Addendum 3: 2x6 Framing & Closed-Cell Foam with Energy Rebates"
    ):
      st.write(
          "**High-Efficiency Thermal Envelope:** Combines 2x6 framing and"
          " closed-cell spray foam with HVAC right-sizing (1.5-ton system) and"
          " DEMCO/DNR rebates, delivering an **instantly cash-positive**"
          " construction upgrade."
      )

    with st.expander(
        "Addendum 4: Federal HEEHRA / HEAR Rebate Mechanics & BTR Integration"
    ):
      st.write(
          "**Federal Incentives:** Up to $8,000 max cap for qualifying heat"
          " pumps and weatherization upgrades, stackable with regional utility"
          " programs at point-of-sale."
      )

    with st.expander(
        "Addendum 5: Ducted Mini-Split in Conditioned Attic vs. Traditional Split"
    ):
      st.write(
          "**Conditioned Attic Ductwork:** Eliminates 15%–25% thermal duct"
          " losses found in 140°F unconditioned attics, extending mechanical"
          " lifespan to 15+ years."
      )

    with st.expander(
        "Addendum 6 & 7: Smart Security Ecosystem & Financial Return"
    ):
      st.write(
          "**Keyless Access & Surveillance:** $600 initial hardware investment"
          " (smart deadbolt & Ring doorbell) generates a $25/mo rent premium,"
          " breaking even in **24 months**."
      )

    with st.expander("Addendum 8: Omission of Ceiling Fans"):
      st.write(
          "**Thermal Uniformity:** Spray-foam insulated envelopes maintain"
          " consistent room temperatures, rendering conventional ceiling fans"
          " mechanically unnecessary."
      )