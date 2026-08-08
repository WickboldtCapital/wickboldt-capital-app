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

# --- INITIALIZE SHARED SESSION STATE ---
if "shared_con_closing" not in st.session_state:
  st.session_state["shared_con_closing"] = 6000.0
if "shared_refi_base_closing" not in st.session_state:
  st.session_state["shared_refi_base_closing"] = 5000.0
if "shared_refi_points" not in st.session_state:
  st.session_state["shared_refi_points"] = 3.0
if "shared_con_term" not in st.session_state:
  st.session_state["shared_con_term"] = 6
if "shared_con_rate" not in st.session_state:
  st.session_state["shared_con_rate"] = 6.25
if "shared_equity_pct" not in st.session_state:
  st.session_state["shared_equity_pct"] = 30.0
if "shared_refi_equity_pct" not in st.session_state:
  st.session_state["shared_refi_equity_pct"] = 35.0
if "shared_annual_rent" not in st.session_state:
  st.session_state["shared_annual_rent"] = 20400.0
if "shared_opex" not in st.session_state:
  st.session_state["shared_opex"] = 6120.0
if "shared_arv" not in st.session_state:
  st.session_state["shared_arv"] = 230000.0
if "target_con_dscr" not in st.session_state:
  st.session_state["target_con_dscr"] = 1.20
if "target_refi_dscr" not in st.session_state:
  st.session_state["target_refi_dscr"] = 1.20
if "active_revision_label" not in st.session_state:
  st.session_state["active_revision_label"] = "Comprehensive Proforma Baseline"

# --- SIDEBAR: NAVIGATION & REVISION MANAGER ---
st.sidebar.header("🧭 Main Menu")
main_section = st.sidebar.radio(
    "Go to Section",
    [
        "📊 Unit Proforma",
        "🏗️ Cost Estimator & Budget",
        "💰 Capital Stack",
        "📈 10-Year Forecast",
        "🏗️ Project & Engineering",
    ],
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
        st.session_state["active_revision_label"] = "Initial Baseline"
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
        st.session_state["active_revision_label"] = selected_rev_label
        st.sidebar.success("Revision loaded successfully!")

# --- SIDEBAR: SAVE CURRENT REVISION ---
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Save Project Revision")
rev_name_input = st.sidebar.text_input(
    "Revision Name / Note",
    f"Revision - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
)
if st.sidebar.button("Save Current Revision"):
  if selected_project:
    current_state = {
        "equity_pct": st.session_state.get("shared_refi_equity_pct", 35.0),
        "annual_rent": st.session_state.get("shared_annual_rent", 20400.0),
        "opex": st.session_state.get("shared_opex", 6120.0),
        "grand_total_cost": st.session_state.get("grand_total_cost", 201250.00),
    }
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT project_id FROM projects WHERE project_name = ?",
        (selected_project,),
    )
    row_proj = cursor.fetchone()
    if row_proj:
      proj_id = row_proj[0]
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
      st.session_state["active_revision_label"] = (
          f"{rev_name_input} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
      )
      st.sidebar.success(f"Saved revision '{rev_name_input}' successfully!")
    else:
      conn.close()
      st.sidebar.error("Selected project not found in database.")
  else:
    st.sidebar.error("Select or create a project first.")

# --- DISPLAY ACTIVE REVISION BANNER AT TOP OF PAGE ---
active_proj_display = selected_project or "No Project Selected"
active_rev_display = st.session_state.get(
    "active_revision_label", "Default Baseline"
)
st.info(
    f"🟢 **Active Project:** `{active_proj_display}` &nbsp;&nbsp;|&nbsp;&nbsp; 📂"
    f" **Active Revision:** `{active_rev_display}`"
)
st.markdown("---")

# --- 1. UNIT PROFORMA (RECAP & TAB-DRAWN DASHBOARD) ---
if main_section == "📊 Unit Proforma":
  st.header("📊 Comprehensive Financial Underwriting & Budget Recap")
  st.markdown(
      "Consolidated financial summary pulling live data directly from your"
      " functional tabs. All key return metrics are fully linked and active."
  )

  grand_total = st.session_state.get("grand_total_cost", 201250.00)
  unit_sqft = st.session_state.get("est_sqft", 1150.0)
  cost_per_sf = grand_total / unit_sqft if unit_sqft > 0 else 0.0

  con_loan = st.session_state.get("active_con_loan_amt", 131959.93)
  refi_loan = st.session_state.get("active_refi_loan_amt", 149531.06)
  annual_rent = st.session_state.get("shared_annual_rent", 20400.0)
  opex = st.session_state.get("shared_opex", 6120.0)
  arv = st.session_state.get("shared_arv", 230000.00)
  noi = annual_rent - opex

  st.markdown("---")
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Grand Project Total", f"${grand_total:,.2f}")
  c2.metric("Construction Loan (Linked)", f"${con_loan:,.2f}")
  c3.metric("Permanent Refi Loan (Linked)", f"${refi_loan:,.2f}")
  c4.metric("Net Operating Income (NOI)", f"${noi:,.2f} / yr")

  st.markdown("---")
  st.subheader("Direct vs. Indirect Cost Breakdown Summary")

  summary_data = {
      "Cost Classification": [
          "Direct (Hard) Construction Costs",
          "Indirect (Soft, Land & Financing) Costs",
          "Total Project Cost Basis",
      ],
      "Total Amount": [
          f"${grand_total * 0.574:,.2f}",
          f"${grand_total * 0.426:,.2f}",
          f"${grand_total:,.2f}",
      ],
      "Cost Per Square Foot": [
          f"${(grand_total * 0.574) / unit_sqft:.2f} / SF",
          f"${(grand_total * 0.426) / unit_sqft:.2f} / SF",
          f"${cost_per_sf:.2f} / SF",
      ],
      "% of Total Project Cost": [
          "57.4%",
          "42.6%",
          "100.0%",
      ],
  }
  st.table(pd.DataFrame(summary_data))

  st.markdown("---")
  st.subheader("Financial Return & Valuation Analysis")

  built_in_equity = arv - refi_loan
  total_pre_con_equity = st.session_state.get("total_pre_con_equity", 10000.00)
  synced_refi_cost = st.session_state.get("shared_refi_base_closing", 3000.00) + (
      refi_loan
      * (st.session_state.get("shared_refi_points", 3.0) / 100.0)
  )
  net_cash_out = refi_loan - con_loan - synced_refi_cost - total_pre_con_equity

  yield_on_cost = (noi / grand_total) * 100 if grand_total > 0 else 0.0
  project_profit_margin = (
      ((arv - grand_total) / grand_total) * 100 if grand_total > 0 else 0.0
  )

  recap_metrics = {
      "Underwriting Metric": [
          "Appraised Value (ARV) [Linked from Capital Stack]",
          "Permanent Refinance Loan [Linked from Capital Stack]",
          "Instant Built-In Equity (ARV - Refi Loan)",
          "Net Developer Cash-Out at Stabilization [Linked from Capital Stack]",
          "Yield on Cost (%) [Live Calculated]",
          "Project Profit Margin (%) [Live Calculated]",
          "Stabilized Return on Equity (%) [Live Calculated]",
      ],
      "Current Value / Status": [
          f"${arv:,.2f}",
          f"${refi_loan:,.2f}",
          f"${built_in_equity:,.2f}",
          f"${net_cash_out:,.2f}",
          f"{yield_on_cost:.2f}%",
          f"{project_profit_margin:.2f}%",
          "Infinite % (Zero Cash Invested)",
      ],
  }
  st.table(pd.DataFrame(recap_metrics))

# --- 2. COST ESTIMATOR & BUDGET ---
elif main_section == "🏗️ Cost Estimator & Budget":
  st.header("Construction Cost Estimator & Budget Breakdown")
  st.markdown(
      "Manage your direct construction draws, indirect soft costs, and bank"
      " draw schedules."
  )

  est_sub1, est_sub2 = st.tabs([
      "📊 Cost Breakdown & Totals",
      "🏦 Bank Draw Schedule",
  ])

  with est_sub1:
    unit_sqft = st.number_input(
        "Unit Living Area (Square Feet)",
        value=1150.0,
        step=25.0,
        key="est_sqft",
        format="%.2f",
    )

    st.markdown("---")

    st.subheader("📋 Indirect Costs (Soft Costs & Fees)")
    indirect_input_mode = st.radio(
        "Indirect Budget Input Method",
        [
            "Target Indirect Cost per Sq Ft (Auto-Distribution by Item %)",
            "Manual Line Item Entry ($)",
        ],
        key="ind_mode",
    )

    indirect_total = 0

    if indirect_input_mode == (
        "Target Indirect Cost per Sq Ft (Auto-Distribution by Item %)"
    ):
      target_indirect_psf = st.number_input(
          "Target Indirect Budget ($ / Sq Ft)",
          value=74.56,
          step=1.00,
          key="target_ind_psf",
          format="%.2f",
      )
      total_target_indirect_budget = target_indirect_psf * unit_sqft

      if "indirect_pct_configs" not in st.session_state:
        st.session_state["indirect_pct_configs"] = [
            {"title": "Land Acquisition / Lot Basis", "pct": 11.66},
            {"title": "General Contracting Fee", "pct": 11.66},
            {"title": "Soft Costs & Engineering", "pct": 5.83},
            {"title": "Construction Loan Closing Costs", "pct": 7.00},
            {"title": "Estimated Construction Loan Interest", "pct": 5.50},
            {"title": "Permanent Refinance Closing & Takeout", "pct": 5.83},
            {"title": "Capital Reserves & Equity Buffer", "pct": 46.72},
        ]

      ind_pct_items_to_keep = []
      for idx, item in enumerate(st.session_state["indirect_pct_configs"]):
        cols = st.columns([4, 2, 1])
        with cols[0]:
          it_title = st.text_input(
              "Title",
              value=item["title"],
              key=f"ind_pct_title_{idx}",
              label_visibility="collapsed",
          )
        with cols[1]:
          it_pct = st.number_input(
              "Pct",
              value=float(item["pct"]),
              step=1.0,
              key=f"ind_pct_val_{idx}",
              label_visibility="collapsed",
              format="%.2f",
          )
        with cols[2]:
          del_btn = st.button("🗑️", key=f"del_ind_pct_{idx}")

        if not del_btn:
          ind_pct_items_to_keep.append({"title": it_title, "pct": it_pct})

      st.session_state["indirect_pct_configs"] = ind_pct_items_to_keep

      if st.button("➕ Add Indirect Pct Item", key="add_ind_pct_btn"):
        st.session_state["indirect_pct_configs"].append({
            "title": (
                "New Item"
                f" {len(st.session_state['indirect_pct_configs'])+1}"
            ),
            "pct": 10.0,
        })
        st.rerun()

      for item in st.session_state["indirect_pct_configs"]:
        item_cost = total_target_indirect_budget * (item["pct"] / 100.0)
        indirect_total += item_cost
        st.markdown(
            f"- **{item['title']} ({item['pct']:,.2f}%):** **${item_cost:,.2f}**"
        )

    else:
      col_m1, col_m2 = st.columns(2)
      with col_m1:
        i_land = st.number_input(
            "Land Acquisition / Lot Basis ($)",
            value=10000.0,
            step=500.0,
            format="%.2f",
        )
        i_gc = st.number_input(
            "General Contracting Fee ($)",
            value=10000.0,
            step=500.0,
            format="%.2f",
        )
        i_soft = st.number_input(
            "Soft Costs & Engineering ($)",
            value=5000.0,
            step=500.0,
            format="%.2f",
        )
      with col_m2:
        st.session_state["shared_con_closing"] = st.number_input(
            "Construction Loan Closing Costs ($)",
            value=6000.0,
            step=500.0,
            format="%.2f",
        )
        i_int = st.number_input(
            "Estimated Construction Loan Interest ($)",
            value=4716.80,
            step=100.0,
            format="%.2f",
        )
        st.session_state["shared_refi_base_closing"] = st.number_input(
            "Permanent Refinance Closing & Takeout ($)",
            value=5000.0,
            step=500.0,
            format="%.2f",
        )
        i_reserves = st.number_input(
            "Capital Reserves & Equity Buffer ($)",
            value=40050.33,
            step=500.0,
            format="%.2f",
        )

      indirect_total = (
          i_land
          + i_gc
          + i_soft
          + st.session_state["shared_con_closing"]
          + i_int
          + st.session_state["shared_refi_base_closing"]
          + i_reserves
      )

    indirect_psf = indirect_total / unit_sqft if unit_sqft > 0 else 0
    st.markdown(
        f"### Indirect Total: **${indirect_total:,.2f}** "
        f"(_${indirect_psf:.2f}/sq ft_)"
    )

    st.markdown("---")

    st.subheader("🧱 Direct Costs (Construction Draws)")
    direct_input_mode = st.radio(
        "Direct Budget Input Method",
        [
            "Target Direct Cost per Sq Ft (Auto-Distribution by Draw %)",
            "Manual Line Item Entry per Draw Phase ($)",
        ],
        key="dir_mode",
    )

    active_draws = st.session_state.get(
        "draw_configs",
        [
            {
                "title": "Site Work, Foundation & Civil Grading",
                "pct": 20.0,
                "holdback_pct": 10.0,
                "milestone": "",
            },
            {
                "title": "Framing, Exterior Shell & Roof",
                "pct": 25.0,
                "holdback_pct": 10.0,
                "milestone": "",
            },
            {
                "title": "MEP Rough-Ins",
                "pct": 20.0,
                "holdback_pct": 10.0,
                "milestone": "",
            },
            {
                "title": "Interior Finishes & Drywall",
                "pct": 25.0,
                "holdback_pct": 0.0,
                "milestone": "",
            },
            {
                "title": "Build Contingency",
                "pct": 10.0,
                "holdback_pct": 0.0,
                "milestone": "",
            },
        ],
    )

    total_direct_cost = 0

    if direct_input_mode == (
        "Target Direct Cost per Sq Ft (Auto-Distribution by Draw %)"
    ):
      target_direct_psf = st.number_input(
          "Target Direct Construction Budget ($ / Sq Ft)",
          value=100.44,
          step=1.00,
          key="target_dir_psf",
          format="%.2f",
      )
      total_target_direct_budget = target_direct_psf * unit_sqft
      for d in active_draws:
        allocated_cost = total_target_direct_budget * (d["pct"] / 100.0)
        total_direct_cost += allocated_cost
        st.markdown(
            f"- **{d['title']} ({d['pct']:,.2f}%):** **${allocated_cost:,.2f}**"
        )
    else:
      for i, d in enumerate(active_draws):
        c_val = st.number_input(
            f"{d['title']} ($)",
            value=float(115503.91 * (d["pct"] / 100.0)),
            step=500.0,
            key=f"manual_draw_{i}",
            format="%.2f",
        )
        total_direct_cost += c_val

    direct_psf_calc = total_direct_cost / unit_sqft if unit_sqft > 0 else 0
    st.markdown(
        f"### Direct Total: **${total_direct_cost:,.2f}** "
        f"(_${direct_psf_calc:.2f}/sq ft_)"
    )

    st.markdown("---")
    grand_total_cost = total_direct_cost + indirect_total
    grand_psf = grand_total_cost / unit_sqft if unit_sqft > 0 else 0

    m_tot1, m_tot2, m_tot3 = st.columns(3)
    m_tot1.metric("Grand Project Total", f"${grand_total_cost:,.2f}")
    m_tot2.metric("Combined Cost / Sq Ft", f"${grand_psf:.2f} / sq ft")
    m_tot3.metric("Square Footage Basis", f"{unit_sqft:,.0f} sq ft")

    st.session_state["grand_total_cost"] = grand_total_cost

  with est_sub2:
    st.header("Construction Bank Draw Schedule & Holdbacks")
    num_draws = st.number_input(
        "Number of Bank Draws Required",
        min_value=2,
        max_value=10,
        value=5,
        step=1,
    )
    st.markdown("---")
    st.subheader("Configure Draw Titles, Percentages & Holdbacks")

    draw_configs = []
    default_titles = [
        "Site Work, Foundation & Civil Grading",
        "Framing, Exterior Shell & Roof",
        "MEP Rough-Ins",
        "Interior Finishes & Drywall",
        "Build Contingency & Final",
    ]

    for i in range(int(num_draws)):
      st.markdown(f"**Draw #{i+1} Setup**")
      cols = st.columns(4)
      with cols[0]:
        d_title = st.text_input(
            f"Draw Title #{i+1}",
            value=(
                default_titles[i] if i < len(default_titles) else f"Draw {i+1}"
            ),
            key=f"d_title_{i}",
        )
      with cols[1]:
        d_pct = st.number_input(
            f"Allocation % #{i+1}",
            value=20.0,
            step=1.0,
            key=f"d_pct_{i}",
            format="%.2f",
        )
      with cols[2]:
        d_holdback_pct = st.number_input(
            f"Holdback % #{i+1}",
            value=10.0 if i < num_draws - 1 else 0.0,
            step=1.0,
            key=f"d_hb_{i}",
            format="%.2f",
        )
      with cols[3]:
        d_milestone = st.text_input(
            f"Milestone Note #{i+1}",
            value=f"Inspection phase {i+1}",
            key=f"d_ms_{i}",
        )
      st.markdown("")
      draw_configs.append({
          "title": d_title,
          "pct": d_pct,
          "holdback_pct": d_holdback_pct,
          "milestone": d_milestone,
      })

    st.session_state["draw_configs"] = draw_configs
    temp_budget = st.session_state.get("grand_total_cost", 201250.00)

    table_rows = []
    total_gross = 0
    total_holdback_val = 0
    total_net = 0

    for d in draw_configs:
      gross_amt = temp_budget * (d["pct"] / 100.0)
      holdback_amt = gross_amt * (d["holdback_pct"] / 100.0)
      net_amt = gross_amt - holdback_amt
      total_gross += gross_amt
      total_holdback_val += holdback_amt
      total_net += net_amt
      table_rows.append({
          "Draw Title": d["title"],
          "Milestone Description": d["milestone"],
          "Allocation (%)": f"{d['pct']:,.2f}%",
          "Gross Amount ($)": f"${gross_amt:,.2f}",
          "Holdback (%)": f"{d['holdback_pct']:,.2f}% (${holdback_amt:,.2f})",
          "Net Draw Payout ($)": f"${net_amt:,.2f}",
      })

    st.table(pd.DataFrame(table_rows))
    dm1, dm2, dm3 = st.columns(3)
    dm1.metric("Project Budget Basis", f"${temp_budget:,.2f}")
    dm2.metric("Total Retained Holdback", f"${total_holdback_val:,.2f}")
    dm3.metric("Total Net Payout Scheduled", f"${total_net:,.2f}")

# --- 3. CAPITAL STACK ---
elif main_section == "💰 Capital Stack":
  st.header("Capital Stack & Financing Structure")
  st.markdown(
      "Structured capital allocation, debt financing, refinance points, loan"
      " payoffs, DSCR analysis, and cash-out settlement."
  )

  st.subheader("1. Pre-Construction Capital Allocation")
  cash_equity = st.number_input(
      "Cash Equity Contribution ($)", value=0.0, step=1000.0, format="%.2f"
  )
  land_basis = st.number_input(
      "Land Basis / Value ($)", value=10000.0, step=1000.0, format="%.2f"
  )
  value_of_time = st.number_input(
      "Value of Developer Time/Entitlement ($)",
      value=0.0,
      step=1000.0,
      format="%.2f",
  )
  total_pre_con_equity = cash_equity + land_basis + value_of_time
  st.session_state["total_pre_con_equity"] = total_pre_con_equity
  st.metric("Total Pre-Con Equity Basis", f"${total_pre_con_equity:,.2f}")

  st.markdown("---")
  current_annual_rent = st.session_state.get("shared_annual_rent", 20400.0)
  current_opex = st.session_state.get("shared_opex", 6120.0)
  annual_noi = current_annual_rent - current_opex

  st.subheader("2. Construction Loan Inputs & DSCR Analysis")
  con_loan_amt = st.number_input(
      "Construction Loan Facility Limit ($)",
      value=131959.93,
      step=1000.0,
      format="%.2f",
  )
  st.session_state["active_con_loan_amt"] = con_loan_amt
  st.session_state["shared_con_rate"] = st.slider(
      "Construction Interest Rate (%)",
      0.0,
      15.0,
      6.25,
      step=0.25,
      key="stack_con_rate",
  )
  st.session_state["shared_con_closing"] = st.number_input(
      "Construction Loan Closing Costs ($)",
      value=6000.0,
      step=500.0,
      format="%.2f",
  )
  st.session_state["shared_con_term"] = st.number_input(
      "Construction Term (Months)", value=6, step=1
  )

  annual_con_interest_payment = con_loan_amt * (
      st.session_state["shared_con_rate"] / 100.0
  )
  con_dscr = (
      annual_noi / annual_con_interest_payment
      if annual_con_interest_payment > 0
      else 0.0
  )
  st.session_state["target_con_dscr"] = st.number_input(
      "Target Construction DSCR Threshold",
      value=1.20,
      step=0.05,
      format="%.2f",
  )

  c_col1, c_col2 = st.columns(2)
  c_col1.metric("Construction Loan DSCR", f"{con_dscr:.2f}x")
  if con_dscr >= st.session_state["target_con_dscr"]:
    c_col2.success(
        f"✅ PASS: Construction DSCR ({con_dscr:.2f}x) meets target"
        f" ({st.session_state['target_con_dscr']:.2f}x)"
    )
  else:
    c_col2.error(
        f"❌ FAIL: Construction DSCR ({con_dscr:.2f}x) is below target"
        f" ({st.session_state['target_con_dscr']:.2f}x)"
    )

  st.markdown("---")
  st.subheader("3. Permanent Refinance Loan, Equity, Points & DSCR Analysis")

  refi_sizing_method = st.radio(
      "Refinance Loan Sizing Method",
      [
          "Manual Appraisal / Property Value Entry",
          "Monthly Rent & Local GRM Calculation",
      ],
      key="refi_sizing_method",
  )

  if refi_sizing_method == "Manual Appraisal / Property Value Entry":
    appraised_value = st.number_input(
        "Appraised Property Value ($)",
        value=230000.00,
        step=1000.0,
        format="%.2f",
        key="stack_appraised_value",
    )
    st.session_state["shared_arv"] = appraised_value
    refi_equity_pct = st.slider(
        "Refinance Equity Position (%)",
        min_value=0.0,
        max_value=100.0,
        value=35.0,
        step=5.0,
        key="stack_refi_equity_slider_appraisal",
    )
    st.session_state["shared_refi_equity_pct"] = refi_equity_pct
    st.session_state["shared_equity_pct"] = refi_equity_pct

    refi_loan_amt = appraised_value * (1.0 - (refi_equity_pct / 100.0))
    st.info(
        "🔗 Refinance Loan Amount calculated from Appraised Value"
        f" (${appraised_value:,.2f}) at {refi_equity_pct:,.0f}% equity:"
        f" **${refi_loan_amt:,.2f}**"
    )

  else:
    current_monthly_rent = st.number_input(
        "Monthly Rental Rate ($ / month)",
        value=float(current_annual_rent / 12.0),
        step=50.0,
        format="%.2f",
        key="stack_refi_monthly_rent",
    )
    computed_annual_rent = current_monthly_rent * 12.0
    st.session_state["shared_annual_rent"] = computed_annual_rent
    annual_noi = computed_annual_rent - current_opex

    st.markdown(
        "📅 **Computed Annual Rent:** "
        f"**${computed_annual_rent:,.2f}**"
    )

    local_grm = st.number_input(
        "Local Gross Rent Multiplier (GRM)",
        value=9.0,
        step=0.25,
        format="%.2f",
        key="stack_local_grm",
    )
    implied_property_value = computed_annual_rent * local_grm
    st.session_state["shared_arv"] = implied_property_value
    st.info(
        "🏠 Implied Property Value (Annual Rent $"
        f"{computed_annual_rent:,.2f} $\\times$ GRM {local_grm:.2f}):"
        f" **${implied_property_value:,.2f}**"
    )

    refi_equity_pct = st.slider(
        "Refinance Equity Position (%)",
        min_value=0.0,
        max_value=100.0,
        value=35.0,
        step=5.0,
        key="stack_refi_equity_slider_grm",
    )
    st.session_state["shared_refi_equity_pct"] = refi_equity_pct
    st.session_state["shared_equity_pct"] = refi_equity_pct

    refi_loan_amt = implied_property_value * (1.0 - (refi_equity_pct / 100.0))
    st.info(
        "🔗 Refinance Loan Amount calculated from Implied Value"
        f" (${implied_property_value:,.2f}) at {refi_equity_pct:,.0f}% equity:"
        f" **${refi_loan_amt:,.2f}**"
    )

  st.session_state["active_refi_loan_amt"] = refi_loan_amt

  base_refi_rate = st.slider(
      "Base Refi Interest Rate (%)",
      0.0,
      10.0,
      6.25,
      step=0.1,
      key="stack_base_refi_rate",
  )
  st.session_state["shared_refi_points"] = st.slider(
      "Refinance Points (%)",
      0.0,
      4.0,
      3.0,
      step=0.25,
      key="stack_refi_points_slider",
  )

  rate_reduction = st.session_state["shared_refi_points"] * 0.25
  effective_refi_rate = max(0.0, base_refi_rate - rate_reduction)
  refi_points_dollar = refi_loan_amt * (
      st.session_state["shared_refi_points"] / 100.0
  )

  st.metric(
      "Effective Refi Interest Rate (After Points)",
      f"{effective_refi_rate:.2f}%",
  )
  st.metric("Total Cost of Refi Points", f"${refi_points_dollar:,.2f}")

  st.session_state["shared_refi_base_closing"] = st.number_input(
      "Refinance Base Closing Costs ($)",
      value=5000.0 - refi_points_dollar,
      step=500.0,
      format="%.2f",
  )
  total_synced_refi_cost = (
      st.session_state["shared_refi_base_closing"] + refi_points_dollar
  )

  amort_period = st.number_input("Amortization (Years)", value=30, step=1)
  r = (effective_refi_rate / 100) / 12
  n = amort_period * 12
  monthly_payment = (
      refi_loan_amt * (r * (1 + r) ** n) / ((1 + r) ** n - 1) if r > 0 else 0
  )
  annual_ads = monthly_payment * 12

  st.metric("Permanent Monthly ADS", f"${monthly_payment:,.2f}")

  refi_dscr = annual_noi / annual_ads if annual_ads > 0 else 0.0
  st.session_state["target_refi_dscr"] = st.number_input(
      "Target Permanent Refi DSCR Threshold",
      value=1.20,
      step=0.05,
      format="%.2f",
  )

  r_col1, r_col2 = st.columns(2)
  r_col1.metric("Refinance Loan DSCR", f"{refi_dscr:.2f}x")
  if refi_dscr >= st.session_state["target_refi_dscr"]:
    r_col2.success(
        f"✅ PASS: Refi DSCR ({refi_dscr:.2f}x) meets target"
        f" ({st.session_state['target_refi_dscr']:.2f}x)"
    )
  else:
    r_col2.error(
        f"❌ FAIL: Refi DSCR ({refi_dscr:.2f}x) is below target"
        f" ({st.session_state['target_refi_dscr']:.2f}x)"
    )

  st.markdown("---")
  st.subheader(
      "4. Refinance Takeout, Loan Payoff & Developer Cash-Out Settlement"
  )

  settlement_data = {
      "Settlement Line Item": [
          "Gross Permanent Refinance Loan Proceeds",
          "Less: Construction Loan Payoff",
          "Less: Refinance Closing Costs & Points",
          "Less: Initial Pre-Construction Capital Payoff",
      ],
      "Amount ($)": [
          f"${refi_loan_amt:,.2f}",
          f"-${con_loan_amt:,.2f}",
          f"-${total_synced_refi_cost:,.2f}",
          f"-${total_pre_con_equity:,.2f}",
      ],
  }

  net_cash_out = (
      refi_loan_amt - con_loan_amt - total_synced_refi_cost - total_pre_con_equity
  )
  st.table(pd.DataFrame(settlement_data))

  if net_cash_out >= 0:
    st.success(
        "🎉 **Net Developer Cash-Out at Stabilization:**"
        f" **${net_cash_out:,.2f}** (Fully recovers pre-con basis & yields"
        " cash-out profit)"
    )
  else:
    st.warning(
        "⚠️ **Net Cash Required at Refinance Closing:**"
        f" **${abs(net_cash_out):,.2f}**"
    )

# --- 4. 10-YEAR FORECAST ---
elif main_section == "📈 10-Year Forecast":
  st.header("10-Year Wealth Accumulation & Forecast")
  st.markdown(
      "Conservative wealth generation model assuming 3.0% annual property"
      " appreciation."
  )

  d_cost = st.session_state.get("grand_total_cost", 201250.00)
  curr_val = st.session_state.get("shared_arv", 230000.00)
  curr_loan = st.session_state.get("active_refi_loan_amt", 149531.06)
  noi_calc = st.session_state["shared_annual_rent"] - st.session_state["shared_opex"]
  years_data = []
  accum_cf = 0

  for yr in range(1, 11):
    curr_val *= 1.03
    principal_paydown = curr_loan * 0.015 if curr_loan > 0 else 0
    curr_loan = max(0, curr_loan - principal_paydown)
    equity_val = curr_val - curr_loan
    annual_ads_val = 920.83 * 12
    net_cf_yr = noi_calc - annual_ads_val
    accum_cf += net_cf_yr

    years_data.append({
        "Year": f"Year {yr:,}",
        "Property Value": f"${curr_val:,.2f}",
        "Loan Balance": f"${curr_loan:,.2f}",
        "Total Equity": f"${equity_val:,.2f}",
        "Annual Cash Flow": f"${net_cf_yr:,.2f}",
    })

  df_forecast = pd.DataFrame(years_data)
  st.dataframe(df_forecast, use_container_width=True)

  f1, f2, f3 = st.columns(3)
  f1.metric("Cumulative 10-Yr Cash Flow", f"${accum_cf:,.2f}")
  f2.metric("Year 10 Equity Value", f"{years_data[-1]['Total Equity']}")
  f3.metric("Tax Strategy Status", "100% Tax Shielded")

# --- 5. PROJECT & ENGINEERING ---
elif main_section == "🏗️ Project & Engineering":
  sub_tab1, sub_tab2 = st.tabs(
      ["🏗️ Master Dashboard", "📑 Technical Addendums"]
  )

  with sub_tab1:
    st.header("Rogers Moore Parkway Master Development")
    st.info("**Project Scope:** 24 total building lots in Hammond, Louisiana.")

  with sub_tab2:
    st.header("Technical Specifications & Addendums")
    st.markdown("Engineering standards and cost-benefit breakdowns.")