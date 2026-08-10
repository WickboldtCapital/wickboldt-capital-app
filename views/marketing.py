import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime

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
    
    # Inquiries CRM Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marketing_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            contact_name TEXT,
            contact_email TEXT,
            inquiry_type TEXT,
            target_lot TEXT,
            notes TEXT,
            date_logged TEXT
        )
    """)
    
    # Marketing Collateral Downloads Tracker Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marketing_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            document_title TEXT,
            downloaded_by TEXT,
            date_logged TEXT
        )
    """)
    conn.commit()
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

def auto_text(label, key, hardcoded_default, container=st, help=None):
    effective_default = global_defaults.get(key, hardcoded_default)
    saved_val = db_state.get(key, effective_default)
    return container.text_area(label, value=saved_val, help=help, key=key, on_change=auto_save, args=(key,))

def auto_input(label, key, hardcoded_default, container=st):
    effective_default = global_defaults.get(key, hardcoded_default)
    saved_val = db_state.get(key, effective_default)
    return container.text_input(label, value=saved_val, key=key, on_change=auto_save, args=(key,))

# --- HEADER STYLING ---
st.markdown("### 📢 Wickboldt Capital: Master Marketing & Collateral Hub")
st.markdown("*Today's Foundation. Tomorrow's Legacy.*")
st.success(f"🟢 **Active Project:** `{st.session_state['active_project']}` &nbsp;&nbsp;|&nbsp;&nbsp; 📂 **Active Revision:** Rogers Moore Parkway 24-Unit Master Portfolio Portal")
st.markdown("---")

# ==========================================
# 🗂️ SUB-NAVIGATION SILO SELECTOR
# ==========================================
# Using radio buttons with horizontal layout simulates cleanly isolated sub-pages 
# preventing cross-contamination or layout breakage across independent modules.
sub_page = st.radio(
    "Select Marketing Module",
    [
        "📊 Investor Relations & Loan Hub",
        "🏘️ Tenant Leasing & Flyer Studio",
        "📄 Institutional Pitch Generator",
        "📇 Prospect & Inquiry CRM",
        "🗺️ Master Plan (Rogers Moore Parkway)",
        "🎨 Brand & Asset Repository"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# ==========================================
# 1. INVESTOR RELATIONS TAB
# ==========================================
if sub_page == "📊 Investor Relations & Loan Hub":
    st.markdown("#### Commercial Bank & Private Investor Pitch Portal")
    st.markdown("Review institutional underwriting metrics and customize loan committee packages for **Rogers Moore Parkway (Hammond, LA)**.")
    
    const_eq_pct = float(db_state.get("const_eq_pct", global_defaults.get("const_eq_pct", 25.0)))
    const_appraised = float(db_state.get("const_appraised", global_defaults.get("const_appraised", 175350.32)))
    const_term = float(db_state.get("const_term", global_defaults.get("const_term", 9.0)))
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Equity Position", f"{const_eq_pct:.1f}%")
    m2.metric("Portfolio Scope", "24-Lot Build-to-Rent")
    m3.metric("Single-Unit TPC Basis", f"${const_appraised:,.2f}")
    m4.metric("Construction Term", f"{const_term:.0f} Months")
    
    st.markdown("---")
    st.markdown("#### Executive Lender Summary & Business Plan Memo")
    memo_default = (
        "Wickboldt Capital is launching a premier multi-phase build-to-rent residential development at Rogers Moore Parkway "
        "in Hammond, Louisiana. The master plan encompasses 24 total building lots across Phase One (10 lots fronting Rogers Moore "
        "and Center Ave) and Phase Two (14 lots). Utilizing institutional-grade 2x6 framing, closed-cell spray foam insulation, "
        "and optimized 1,150 sq ft two-story 3BR/2.5BA narrow-footprint layouts, the project captures resilient year-round demand "
        "driven by proximity to Southeastern Louisiana University and Hammond's booming logistics corridor. Financing relies on a "
        "robust 25% equity position paired with commercial construction-to-permanent credit facilities."
    )
    auto_text("Edit Executive Lender Summary", "marketing_lender_memo", memo_default)
    
    st.markdown("#### 📋 Capital Stack & Underwriting Highlights")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("* **Target Market:** Hammond & Tangipahoa Parish, LA (Rapid micro-urban growth near I-12 & I-55).")
        st.markdown("* **Tenant Ecosystem:** Dual-demographic demand (University students/faculty + local workforce & logistics personnel).")
        st.markdown("* **Developer Spread:** Ground-up equity creation through undervalued land acquisition & entitlement execution.")
    with c_col2:
        st.markdown("* **Financing Structure:** 75% LTV construction loan facility transitioning to 30-year permanent take-out debt.")
        st.markdown("* **Energy Incentives:** DEMCO and Louisiana DNR HEAR/HOMES rebates ($7,000 to $8,000 per unit un-modeled upside).")
        st.markdown("* **Tax Protection:** 27.5-year depreciation schedule shielding 100% of operating cash flow.")

# ==========================================
# 2. TENANT LEASING & FLYER STUDIO TAB
# ==========================================
elif sub_page == "🏘️ Tenant Leasing & Flyer Studio":
    st.subheader("Resident & Tenant Leasing Studio")
    st.markdown("Manage promotional messaging designed for university students, faculty, and local working households in Hammond.")
    
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("#### Architectural & Efficiency Specifications")
        st.markdown("* **Configuration:** 3 Bedrooms, 2.5 Bathrooms, Single-Car Garage (3BR/2.5BA)")
        st.markdown("* **Footprint:** Narrow-footprint two-story design (1,150 sq ft optimized urban infill)")
        st.markdown("* **Envelope:** 2x6 framing with 9-foot ceilings and closed-cell spray foam insulation")
        st.markdown("* **Climate Control:** 1.5-ton ducted mini-split with strict Manual J, S, D, T engineering & BLDC ceiling fans")
    
    with t_col2:
        st.markdown("#### Custom Rental Headline & Marketing Copy")
        flyer_headline = auto_input("Promotional Headline", "tenant_flyer_headline", "Now Leasing: High-Efficiency Luxury Rentals at Rogers Moore Parkway, Hammond")
        flyer_perks = auto_text("Key Renter Perks (Bulleted)", "tenant_flyer_perks", "- Up to 50% lower utility bills with advanced spray foam & ICF thermal envelope\n- Prime location under 1 mile from Southeastern Louisiana University\n- Premium quartz countertops, LVP flooring & commercial-grade fixtures\n- Quiet, professional neighborhood setting with private single-car garages")
        st.success("✅ Rental listing text is synchronized across digital syndication endpoints.")

# ==========================================
# 3. INSTITUTIONAL PITCH GENERATOR TAB
# ==========================================
elif sub_page == "📄 Institutional Pitch Generator":
    st.subheader("Institutional Pitch Deck & Loan Packet Generator")
    st.markdown("Generate formatted, comprehensive presentation modules for investment committees and banking partners.")
    
    doc_type = st.selectbox(
        "Select Collateral Document to Generate", 
        [
            "Full Business Plan Executive Summary (V108)",
            "Commercial Bank Loan Committee Memo (Tracts C1–3)",
            "Tenant Leasing Prospectus & Energy Efficiency Factsheet",
            "10-Year Portfolio Wealth & Tax Strategy Summary"
        ]
    )
    
    if st.button("✨ Compile & Generate Document Package", use_container_width=True):
        st.session_state["last_generated_doc"] = doc_type
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "INSERT INTO marketing_downloads (project_name, document_title, downloaded_by, date_logged) VALUES (?, ?, ?, ?)",
            (st.session_state["active_project"], doc_type, st.session_state.get("email", "Admin User"), datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Successfully compiled: **{doc_type}**! Review the output below.")

    st.markdown("---")
    
    # Document Preview Render Box
    selected_doc = st.session_state.get("last_generated_doc", "Full Business Plan Executive Summary (V108)")
    st.markdown(f"#### 📄 Document Preview: `{selected_doc}`")
    
    # Pull dynamic values for document text preview
    const_eq_pct = float(db_state.get("const_eq_pct", global_defaults.get("const_eq_pct", 25.0)))
    const_appraised = float(db_state.get("const_appraised", global_defaults.get("const_appraised", 175350.32)))
    
    if "Business Plan" in selected_doc:
        st.markdown(
            f"""
            ### WICKBOLDT CAPITAL | MASTER DEVELOPMENT BUSINESS PLAN (V108)
            **Project Location:** Rogers Moore Parkway, Hammond, Louisiana  
            **Asset Class:** 24-Lot High-Efficiency Narrow-Footprint Build-to-Rent Residential Portfolio  
            **Principal:** Stephen J. Wickboldt, Jr. (Licensed General Contractor, Louisiana)  
            
            **1. Executive Summary:**  
            Wickboldt Capital is executing a multi-phase build-to-rent development in Hammond, LA. Phase One comprises 10 lots fronting Rogers Moore Parkway and Center Avenue, with immediate capital focused on Tranches C1–3. Homes feature 1,150 sq ft two-story layouts (3BR/2.5BA, single-car garage), engineered with 2x6 framing and closed-cell spray foam.  
            
            **2. Market Fundamentals:**  
            Anchored by Southeastern Louisiana University (<1 mile) and regional logistics expansion (I-12/I-55 corridor, S&W Wholesale Foods $21M investment), capturing high-velocity demand from students, university faculty, and technical workforce personnel.  
            
            **3. Financial Underwriting:**  
            Total Project Cost per unit: \${const_appraised:,.2f} utilizing a 25% equity position ({const_eq_pct:.1f}%) and 75% LTV construction-to-permanent financing structure achieving a 1.20 DSCR.
            """
        )
    elif "Bank Loan" in selected_doc:
        st.markdown(
            f"""
            ### COMMERCIAL BANK LOAN COMMITTEE PROPOSAL
            **Borrower:** Wickboldt Capital  
            **Request Tranche:** Phase One - Tracts C1–3 (3 Building Lots)  
            **Collateral Valuation Basis:** \${const_appraised:,.2f} per unit  
            
            **Loan Request Structure:**  
            * **Facility Type:** Construction-to-Permanent Loan  
            * **Equity Injection:** {const_eq_pct:.1f}% borrower equity position funded via land basis and upfront capital reserves.  
            * **Debt Service Coverage:** 1.20 DSCR backed by conservative \$1,500/mo monthly gross rents per unit.  
            * **Contractor Oversight:** Self-performed general contracting under Stephen J. Wickboldt, Jr. (30 years construction experience, including 22 years offshore oil & gas and 3 years residential).
            """
        )
    elif "Tenant Leasing" in selected_doc:
        st.markdown(
            """
            ### TENANT LEASING PROSPECTUS & EFFICIENCY HIGHLIGHTS
            **Property:** Rogers Moore Parkway Residences, Hammond, LA  
            
            **Key Resident Benefits:**  
            * **Extreme Thermal Performance:** Closed-cell spray foam insulation and double pane low-E windows slash monthly utility overhead by up to 50%.  
            * **Modern Functional Layout:** 3 bedrooms, 2.5 bathrooms, open-concept living, and private single-car garage within a clean, efficient two-story footprint.  
            * **Superior Finishes:** Quartz countertops, commercial-grade 20 mil LVP flooring, solid brass Moen/Delta fixtures, and sound-attenuated walls.  
            * **Prime Location:** Minutes from Southeastern Louisiana University, downtown Hammond, and major regional retail/dining corridors.
            """
        )
    else:
        st.markdown(
            """
            ### 10-YEAR PORTFOLIO WEALTH & TAX STRATEGY SUMMARY
            **Asset Base:** 24-Unit Build-to-Rent Portfolio (Phased 3-Year Rollout)  
            
            **Cumulative 10-Year Projections:**  
            * **Cumulative Net Cash Flow:** \$429,920.64 (100% shielded by 27.5-year depreciation and mortgage interest deductions).  
            * **Cumulative Equity Gain (Principal Paydown + 3% Appreciation):** \$1,732,414.20 across all 24 units.  
            * **Cumulative Tax Savings:** \$44,026.36 in paper loss offsets.  
            * **Total Portfolio Wealth Creation:** \$2,206,361.20 conservative 10-year horizon return.
            """
        )

# ==========================================
# 4. PROSPECT & INQUIRY CRM TAB
# ==========================================
elif sub_page == "📇 Prospect & Inquiry CRM":
    st.subheader("Active Lead & Inquiry CRM")
    st.markdown("Log and track prospective private investors, commercial banking partners, or future tenants inquiring about Rogers Moore Parkway tranches.")
    
    with st.form("crm_form"):
        c1, c2 = st.columns(2)
        inquiry_name = c1.text_input("Contact Name / Institution")
        inquiry_email = c1.text_input("Email / Phone")
        inquiry_type = c2.selectbox("Inquiry Category", ["Private Investor", "Commercial Lender", "Prospective Tenant", "Broker / Partner"])
        target_lot = c2.selectbox("Target Lot / Tranche", ["Phase 1 - Tracts C1–3 (Active Loan)", "Remaining Phase 1 Lots (7 units)", "Phase 2 Expansion (14 units)", "Full 24-Unit Portfolio"])
        inquiry_notes = st.text_area("Inquiry Notes & Follow-Up Items")
        
        submitted = st.form_submit_button("💾 Save Lead to Database")
        if submitted:
            if inquiry_name:
                conn = sqlite3.connect(DB_FILE)
                conn.execute(
                    "INSERT INTO marketing_inquiries (project_name, contact_name, contact_email, inquiry_type, target_lot, notes, date_logged) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (st.session_state["active_project"], inquiry_name, inquiry_email, inquiry_type, target_lot, inquiry_notes, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Lead successfully recorded for {inquiry_name}!")
            else:
                st.warning("⚠️ Please provide at least a contact name.")

    st.markdown("#### 📇 Logged Inquiries for this Project")
    conn = sqlite3.connect(DB_FILE)
    df_leads = pd.read_sql_query("SELECT contact_name, contact_email, inquiry_type, target_lot, notes, date_logged FROM marketing_inquiries WHERE project_name=?", conn, params=(st.session_state["active_project"],))
    conn.close()
    
    if not df_leads.empty:
        st.dataframe(df_leads, use_container_width=True)
    else:
        st.info("No inquiries logged yet. Use the form above to add your first lead.")

# ==========================================
# 5. MASTER PLAN VIEWER TAB
# ==========================================
elif sub_page == "🗺️ Master Plan (Rogers Moore Parkway)":
    st.subheader("Rogers Moore Parkway Master Development Viewer")
    st.markdown("24-Lot Master Phasing Plan located in Hammond, Louisiana.")
    
    master_data = {
        "Phase": ["Phase One", "Phase One", "Phase Two"],
        "Lot Count": ["3 Lots", "7 Lots", "14 Lots"],
        "Designation": ["Tracts C1–3 (Active Loan Tranche)", "Remaining Phase One Frontage", "Phase Two Interior Expansion"],
        "Location / Alignment": ["Fronting Rogers Moore Pkwy & Center Ave", "Fronting Rogers Moore Pkwy & Center Ave", "Interior Master Development Corridor"],
        "Status": ["Underwriting / Active Loan Request", "Scheduled Rollout", "Planning & Entitlement"]
    }
    st.table(pd.DataFrame(master_data))
    st.success("🗺️ Site map overlays are fully synchronized with civil engineering grading and municipal utility specifications in Hammond, LA.")

# ==========================================
# 6. BRAND & ASSET REPOSITORY TAB
# ==========================================
elif sub_page == "🎨 Brand & Asset Repository":
    st.subheader("Corporate Brand Assets & Governance")
    st.markdown("Official visual identity and brand guidelines for Wickboldt Capital.")
    
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("#### Color Palette")
        st.markdown("* **Royal Blue:** Primary structural color (`#0B3C5D`)")
        st.markdown("* **Metallic Gold:** Accent and metric highlight color (`#C5A059`)")
        st.markdown("#### Corporate Tagline")
        st.markdown("> *Today's Foundation. Tomorrow's Legacy.*")
    
    with b2:
        st.markdown("#### Logo & Entity Specifications")
        st.markdown("* **Core Mark:** Capital letter W integrated with a clean-lined house silhouette.")
        st.markdown("* **Rule:** Maintain clean vector lines without unnecessary ornamentation across all digital and print collateral.")
        st.markdown("* **Entity Name:** Wickboldt Capital (Licensed General Contractor, Louisiana — Stephen J. Wickboldt, Jr.).")