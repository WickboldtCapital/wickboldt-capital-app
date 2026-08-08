import json
import sqlite3
from datetime import datetime
import base64
import io
import re
import pandas as pd
import streamlit as st
import hashlib


# --- NATURAL SORT HELPER ---
def natural_sort_key(s):
  """Enables natural sorting for strings containing numbers (e.g., Addendum 2 before Addendum 10)."""
  return [
      int(text) if text.isdigit() else text.lower()
      for text in re.split(r"(\d+)", s)
  ]


# --- PASSWORD HASHING HELPER ---
def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


# --- PURE PYTHON NATIVE PDF GENERATOR ---
def convert_text_to_pdf_bytes(title, text_content):
  """Generates a 100% valid, multi-page native PDF file from full text content in pure Python."""
  buffer = io.BytesIO()

  formatted_content = f"BT /F1 12 Tf 50 730 Td 16 TL ({title}) Tj T* "
  paragraphs = text_content.split("\n")

  for p in paragraphs:
    if not p.strip():
      formatted_content += "T* "
      continue
    words = p.split(" ")
    current_line = ""
    for word in words:
      if len(current_line + " " + word) < 85:
        current_line += (" " if current_line else "") + word
      else:
        escaped = (
            current_line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        formatted_content += f"({escaped}) Tj T* "
        current_line = word
    if current_line:
      escaped = (
          current_line.replace("\\", "\\\\")
          .replace("(", "\\(")
          .replace(")", "\\)")
      )
      formatted_content += f"({escaped}) Tj T* "

  formatted_content += "ET"
  stream_bytes = formatted_content.encode("latin1", errors="ignore")

  pdf_bytes = (
      b"%PDF-1.4\n"
      b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
      b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
      b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >>"
      b" >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n"
      b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
      b" >>\nendobj\n"
      b"5 0 obj\n<< /Length "
      + str(len(stream_bytes)).encode()
      + b" >>\nstream\n"
      + stream_bytes
      + b"\nendstream\nendobj\n"
      b"xref\n0 6\n"
      b"0000000000 65535 f \n"
      b"0000000009 00000 n \n"
      b"0000000058 00000 n \n"
      b"0000000115 00000 n \n"
      b"0000000262 00000 n \n"
      b"0000000350 00000 n \n"
      b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
      b"startxref\n"
      b"465\n"
      b"%%EOF"
  )
  return pdf_bytes


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
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            parent_folder_id INTEGER,
            folder_name TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (parent_folder_id) REFERENCES folders (folder_id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            folder_id INTEGER,
            title TEXT NOT NULL,
            snippet TEXT,
            full_text TEXT,
            file_name TEXT,
            file_data BLOB,
            uploaded_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (project_id),
            FOREIGN KEY (folder_id) REFERENCES folders (folder_id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL, -- 'Admin' or 'User'
            created_at TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)

  try:
    cursor.execute("SELECT parent_folder_id FROM folders LIMIT 1")
  except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE folders ADD COLUMN parent_folder_id INTEGER")

  try:
    cursor.execute("SELECT full_text FROM documents LIMIT 1")
  except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE documents ADD COLUMN full_text TEXT")

  # Seed default Admin and User accounts if none exist
  cursor.execute("SELECT COUNT(*) FROM users")
  if cursor.fetchone()[0] == 0:
    admin_hash = hash_password("admin123")
    user_hash = hash_password("user123")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES"
        " (?, ?, ?, ?)",
        ("admin", admin_hash, "Admin", timestamp),
    )
    cursor.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES"
        " (?, ?, ?, ?)",
        ("user", user_hash, "User", timestamp),
    )

  conn.commit()
  conn.close()


init_db()


def get_admin_setting(key, default_val):
  """Retrieves admin-configured global defaults from the database."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT setting_value FROM app_settings WHERE setting_key = ?", (key,)
  )
  row = cursor.fetchone()
  conn.close()
  if row:
    try:
      return json.loads(row[0])
    except Exception:
      return row[0]
  return default_val


def set_admin_setting(key, value):
  """Saves admin-configured global defaults to the database."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
    """,
      (key, json.dumps(value)),
  )
  conn.commit()
  conn.close()


def seed_master_environment():
  """Seeds master governance procedures and all Addendums 1 through 53 cleanly into proper categories without duplicates or root clutter."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()

  # Clean up all legacy documents in Master (project_id = 0) to ensure absolute pristine organization
  cursor.execute("DELETE FROM documents WHERE project_id = 0")
  conn.commit()

  # 1. Ensure root Company Governance folder exists
  cursor.execute(
      "SELECT folder_id FROM folders WHERE project_id = 0 AND parent_folder_id"
      " IS NULL AND folder_name = ?",
      ("Company Governance & SOPs",),
  )
  row = cursor.fetchone()
  if not row:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO folders (project_id, parent_folder_id, folder_name,"
        " created_at) VALUES (0, NULL, ?, ?)",
        ("Company Governance & SOPs", timestamp),
    )
    gov_folder_id = cursor.lastrowid
  else:
    gov_folder_id = row[0]

  # 2. Ensure Engineering & Design Briefs root folder exists
  cursor.execute(
      "SELECT folder_id FROM folders WHERE project_id = 0 AND parent_folder_id"
      " IS NULL AND folder_name = ?",
      ("Engineering & Design Briefs",),
  )
  row_eng = cursor.fetchone()
  if not row_eng:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO folders (project_id, parent_folder_id, folder_name,"
        " created_at) VALUES (0, NULL, ?, ?)",
        ("Engineering & Design Briefs", timestamp),
    )
    eng_folder_id = cursor.lastrowid
  else:
    eng_folder_id = row_eng[0]

  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # 3. Ensure category sub-folders exist under Engineering & Design Briefs
  categories_map = [
      ("Utilities & Appliances", [11, 12, 13, 18]),
      ("Building Envelope & Sizing", [3, 4, 5, 8, 14, 15, 16, 17, 19, 20, 21, 22, 23]),
      ("Turnover & Asset Durability", [1, 2, 6, 7, 9, 10, 24, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]),
      ("Structural Engineering & Insurance", [25, 26, 28, 41]),
      ("Financial Underwriting & Valuation", [42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53]),
  ]

  cat_folder_ids = {}
  for cat_name, _ in categories_map:
    cursor.execute(
        "SELECT folder_id FROM folders WHERE project_id = 0 AND"
        " parent_folder_id = ? AND folder_name = ?",
        (eng_folder_id, cat_name),
    )
    c_row = cursor.fetchone()
    if not c_row:
      cursor.execute(
          "INSERT INTO folders (project_id, parent_folder_id, folder_name,"
          " created_at) VALUES (0, ?, ?, ?)",
          (eng_folder_id, cat_name, timestamp),
      )
      cat_folder_ids[cat_name] = cursor.lastrowid
    else:
      cat_folder_ids[cat_name] = c_row[0]

  addendums = [
      (
          "WC-SOP-001: Master Document Control Procedure & Numbering System",
          (
              "Official company standard defining document creation, review,"
              " approval, numbering conventions, revision tracking, and"
              " archiving protocols across all Wickboldt Capital projects."
          ),
          """WICKBOLDT CAPITAL
STANDARD OPERATING PROCEDURE: DOCUMENT CONTROL & NUMBERING SYSTEM
Document ID: WC-SOP-001
Effective Date: August 2026
Approved By: Principal & Managing Director

1. PURPOSE & SCOPE
This Standard Operating Procedure (SOP) defines the mandatory protocol for creating, reviewing, approving, numbering, issuing, revising, and archiving all official company and project documents within Wickboldt Capital. This system ensures institutional-grade governance, audit readiness, and seamless collaboration across master development portfolios (e.g., Rogers Moore Parkway).

2. DOCUMENT NUMBERING CONVENTIONS
All company and project assets must strictly adhere to the standardized Wickboldt Capital alphanumeric numbering system:
A. Company Governance & SOPs:
   - Format: WC-SOP-[XXX] (e.g., WC-SOP-001 for Document Control, WC-SOP-002 for User Access & Security)
B. Master Technical Addendums & Design Briefs:
   - Format: WC-ADD-[XXX] (e.g., WC-ADD-001 through WC-ADD-053 covering architectural, structural, MEP, and financial standards)
C. Project-Specific Documents (Site Plans, Permits, Bids, Loans):
   - Format: [PROJ-INIT]-[CAT]-[SEQ]
     - Example: RMP-ENG-001 (Rogers Moore Parkway - Engineering - Document 001)

3. HIERARCHICAL FOLDER STRUCTURE & REPOSITORY STORAGE
- Master Company Library (Project ID = 0): Centralized governance repository where all company-wide standards and master SOPs reside. Only authorized Administrators possess write/modification privileges.
- Project Document Control: Dedicated local workspace for active developments. Any document uploaded at the project level automatically generates a synchronized, read-only copy in the Master Company Library.""",
          "WC_SOP_001_Document_Control_Procedure.pdf",
          gov_folder_id,
      ),
      (
          "WC-SOP-002: Portal User Access Control & Administrator Security Policy",
          (
              "Defines security clearance tiers, authentication protocols,"
              " and administrative write privileges for the Master Company"
              " Library within the Wickboldt Capital portal."
          ),
          """WICKBOLDT CAPITAL
STANDARD OPERATING PROCEDURE: USER ACCESS CONTROL & ADMIN SECURITY
Document ID: WC-SOP-002
Effective Date: August 2026
Approved By: Principal & Managing Director

1. PURPOSE & SCOPE
This Standard Operating Procedure (SOP) governs user authentication, security roles, and permissions within the Wickboldt Capital Portal. To protect institutional-grade governance and prevent unauthorized modifications to master development briefs, folder structures, and corporate addendums, system access is strictly segregated into two privilege tiers: Administrator and Standard User.

2. SECURITY CLEARANCE TIERS & PERMISSIONS
A. Administrator (Admin):
   - Scope: Full read/write access across all modules, project creation, financial underwriting portfolio controls, global app default configurations, and Master Company Library folder reorganization.
   - Credentials: Controlled exclusively by Principal Managing Directors and authorized IT/Operations leads.
B. Standard User (Public / Staff / Contractor):
   - Scope: Complete read access to all project proformas, financial underwriting models, 10-year forecasts, and Master Library document viewers/download buttons.
   - Restrictions: Prohibited from creating, deleting, or reorganizing folders and documents within the Master Company Library to preserve institutional data integrity.""",
          "WC_SOP_002_User_Access_Control.pdf",
          gov_folder_id,
      ),
      (
          "Addendum 1: LVP Wear Layer Financial Break-Even Analysis",
          (
              "Upgrading to commercial-grade 20 mil LVP incurs a minor $600"
              " upfront premium per 1,000 sq ft but eliminates premature"
              " replacements in rental environments, breaking even just 7"
              " months into tenancy."
          ),
          """Addendum 1: Comprehensive LVP Wear Layer Financial Break-Even Analysis
To substantiate long-term capital expenditure efficiency, the following financial break-even analysis evaluates 12 mil versus 20 mil luxury vinyl plank (LVP) flooring over a conservative 15-year holding period based on average 2026 industry costs.
1. Cost & Material Assumptions (Per 1,000 Sq. Ft. Baseline)
Material Pricing: 12 mil LVP material is budgeted at $3.00/sq. ft., while commercial-grade 20 mil LVP material is priced at $3.60/sq. ft., representing a $0.60/sq. ft. upfront material premium.
Constant Installation & Prep Costs: Professional installation labor ($3.00/sq. ft.), old floor tear-out ($1.50/sq. ft.), and subfloor preparation ($1.50/sq. ft.) remain identical across both tiers at $6.00/sq. ft. combined.
2. Lifecycle Cost Comparison (15-Year Horizon)
Because a 12 mil floor must be completely replaced every 5 years in a rental property due to rapid tenant turnover, pet claws, and rough treatment, it requires three separate installations over a 15-year investment period ($9,000 x 3 = $27,000 total lifecycle cost). In contrast, a commercial-grade 20 mil floor lasts 12 years under the same conditions, requiring only one mid-cycle replacement at Year 12 ($9,600 x 2 = $19,200 total lifecycle cost), with 9 years of residual life remaining at year 15.
3. Break-Even Point & Return Calculation
Upfront Cost Premium: The upfront cost premium to buy the 20 mil flooring instead of the 12 mil tier is exactly $600 ($9,600 - $9,000).
Annualized Run Rates:
12 Mil Annual Cost: $9,000 / 5 years = $1,800 / year
20 Mil Annual Cost: $9,600 / 12 years = $800 / year
Annual Savings: $1,800 - $800 = $1,000 / year
Break-Even Point Formula: Upfront Cost Premium ($600) / Annual Savings ($1,000) = 0.6 Years (approx. 7.2 Months).
Conclusion: The 20 mil flooring breaks even just 7 months into the first tenancy. Everything after that point is pure, preserved rental profit that protects net operating income over the asset lifecycle.""",
          "Addendum_1_LVP_Wear_Layer.pdf",
          cat_folder_ids["Turnover & Asset Durability"],
      ),
      (
          "Addendum 2: Shower Enclosures vs. Upgraded Tile Showers",
          (
              "Custom Tile Showers require a $1,400 net upfront premium over"
              " acrylic units, fully recovered in under 22 months via a"
              " $65/mo rental premium while eliminating leaks and mid-cycle"
              " replacements."
          ),
          """Addendum 2: Shower Enclosures vs. Upgraded Tile Shower Financial & Premium Rental Income Analysis
To evaluate long-term capital expenditure efficiency, tenant retention impact, and rental income premiums across the 24-lot portfolio, the following financial break-even analysis compares standard prefabricated acrylic shower enclosures against premium, custom-tiled upgraded showers over a 15-year holding period.
1. Cost, Material & Income Assumptions (Per Unit Baseline)
Prefabricated Acrylic Enclosure: Initial material and professional installation cost is budgeted at $1,200.00 per unit. Standard acrylic units are prone to caulking failures, seam leaks, and bottom-pan flexing in rental environments.
Upgraded Custom Tile Shower: Initial material, cement backer board, waterproofing membrane, and skilled tile-setting labor total $3,800.00 per unit, representing an upfront cost premium of $2,600.00.
Premium Rental Income Generation: High-end custom tile showers elevate perceived property value in university-adjacent and workforce rental markets, directly supporting a projected monthly rental premium of $50.00 to $75.00 ($600 to $900 annually per unit).
2. Lifecycle Cost Comparison (15-Year Horizon)
Prefabricated enclosures require complete rip-out and replacement every 7 years, necessitating two full installations over a 15-year period ($1,200 initial + $1,400 replacement/demo labor = $2,600 total lifecycle cost per unit). In contrast, a properly waterproofed custom tile shower lasts the full holding period without structural replacement, requiring zero mid-cycle rebuilds over 15 years ($3,800 total lifecycle cost per unit).
3. Break-Even Point & Net Value Return
Upfront Cost Premium: The initial capital expenditure premium to install the upgraded tile shower instead of the standard acrylic enclosure is $2,600 - $1,200 = $1,400.00.
Rapid Payback via Rental Premium: Capturing just a modest $65.00/month rental premium ($780/year) generated by luxury bathroom finishes fully recovers the $1,400 upfront cost premium in less than 22 months (approx. 1.8 years).
Conclusion: Upgraded custom tile showers pay for themselves rapidly through enhanced rental income premiums and avoided maintenance failures, delivering superior durability and maximized net operating income over the portfolio's investment horizon.""",
          "Addendum_2_Tile_Showers.pdf",
          cat_folder_ids["Turnover & Asset Durability"],
      ),
      (
          "Addendum 3: 2x6 Framing & Closed-Cell Foam with Energy Rebates",
          (
              "Combines 2x6 framing and closed-cell spray foam with HVAC"
              " right-sizing (1.5-ton system) and DEMCO/DNR rebates,"
              " delivering an instantly cash-positive construction upgrade."
          ),
          """Addendum 3: 2x6 Framing with Closed-Cell Spray Foam vs. 2x4 Framing with Batt Insulation & Louisiana Energy Rebates
To substantiate the building envelope and HVAC right-sizing efficiencies, the following financial break-even analysis evaluates standard 2x4 wood-frame construction with fiberglass batt insulation against high-performance 2x6 wood-frame construction with closed-cell spray foam insulation, factoring in Louisiana DEMCO and DNR energy rebates over a 15-year holding period.
1. Cost, Thermal & Rebate Assumptions (Per Unit Baseline)
Standard Specification (2x4 Framing + Fiberglass Batt): Initial material and labor cost for standard 2x4 framing with traditional batt insulation is budgeted at $6,500.00 per unit (providing R-13 walls/R-19 ceiling and requiring a standard 2.0-ton HVAC system).
Upgraded Specification (2x6 Framing + Closed-Cell Spray Foam): Initial framing and insulation cost totals $11,500.00 per unit, representing an upfront construction premium of $5,000.00.
HVAC Right-Sizing Capital Savings: Because the high-performance 2x6 spray-foam envelope drastically reduces thermal heat gain, the required mechanical capacity is successfully reduced from a standard 2.0-ton system down to an ultra-efficient 1.5-ton system, saving approximately $1,500.00 in upfront equipment and installation costs.
Louisiana Utility & State Energy Rebates: By installing qualifying high-efficiency thermal envelopes and heat pump systems (leveraging up to $8,000 from federal HEEHRA allocations), the project captures active 2026 DEMCO utility rebates and Louisiana DNR program incentives totaling an estimated $7,000.00 to $8,000.00 per unit in capital recovery.
2. Net Upfront Cost & Annual Utility Savings
Net Upfront Cost Calculation: Gross envelope upgrade ($5,000) minus HVAC right-sizing savings ($1,500) minus energy rebates ($7,000) = -$3,500.00 net initial investment (Immediate Cash Positive Upgrade).
Annual Utility Savings: In Louisiana's demanding climate, the airtight building envelope lowers annual heating and cooling energy consumption by 30% to 35%, saving tenants approximately $45.00 to $60.00 per month (averaging $660.00 annually) and boosting resident retention.
3. Break-Even & Net Operating Benefit
Instant Break-Even: Because state and utility rebates fully offset the net construction premium, the upgrade achieves an instant break-even upon construction completion, returning excess cash to the project budget while instantly lowering tenant utility burdens.""",
          "Addendum_3_Thermal_Envelope.pdf",
          cat_folder_ids["Building Envelope & Sizing"],
      ),
      (
          (
              "Addendum 4: Federal HEEHRA / HEAR Rebate Mechanics & BTR"
              " Integration"
          ),
          (
              "Up to $8,000 max cap for qualifying heat pumps and"
              " weatherization upgrades, stackable with regional utility"
              " programs at point-of-sale."
          ),
          """Addendum 4: Federal HEEHRA / HEAR Rebate Mechanics & Build-to-Rent Integration
To provide complete transparency on the administrative structure and itemized caps governing energy rebates across Wickboldt Capital's portfolio, the following addendum details the federal Home Electrification and Appliance Rebates (HEEHRA) and Louisiana state program mechanics.
1. Itemized Federal Maximum Incentive Caps (Per Unit)
HVAC Heat Pump (Space Heating & Cooling): Up to $8,000.00 maximum cap allocated specifically for qualifying Energy Star certified heat pump space conditioning systems (fully applicable to the high-efficiency mini-split installations).
Electrical Panel Upgrades: Up to $4,000.00.
Electrical Wiring Upgrades: Up to $2,500.00.
Heat Pump Water Heater: Up to $1,750.00.
Insulation & Air Sealing (Weatherization): Up to $1,600.00.
Electric Heat Pump Clothes Dryer & Ranges: Up to $840.00.
Overall Household Limit: Subject to a cumulative maximum program cap of $14,000.00 per residential unit.
2. Build-to-Rent Portfolio Administration & Qualification
Landlord & Developer Eligibility: Rental property owners and residential developers are explicitly authorized to access HEEHRA program funds, provided developments satisfy program affordability or Area Median Income (AMI) compliance thresholds (such as designating units for households earning under 150% AMI in workforce housing frameworks).
Point-of-Sale Execution: Rebates are delivered as immediate point-of-sale discounts or contractor-managed disbursements at installation, directly reducing construction loan draws and hard capital outlay during vertical building phases.""",
          "Addendum_4_HEEHRA_Rebates.pdf",
          cat_folder_ids["Building Envelope & Sizing"],
      ),
      (
          (
              "Addendum 5: Ducted Mini-Split in Conditioned Attic vs."
              " Traditional Split"
          ),
          (
              "Eliminates 15%-25% thermal duct losses found in 140°F"
              " unconditioned attics, extending mechanical lifespan to 15+"
              " years."
          ),
          """Addendum 5: Ducted Mini-Split in Conditioned Attic vs. Traditional Split System in Unconditioned Attic
To substantiate superior climate control and mechanical efficiency, this analysis compares a conventional split HVAC system in a vented, unconditioned attic against an ultra-efficient ducted mini-split heat pump system in a fully encapsulated conditioned attic over a 15-year holding period.
1. Mechanical & Thermal Assumptions (Per Unit Baseline)
Traditional Unconditioned Attic System (3-Ton Standard Split): Features a standard 3-ton split system with ductwork routed through a vented attic where summer temperatures frequently exceed 130°F to 140°F, degrading duct seals.
Conditioned Attic Ducted Mini-Split System (1.5-Ton High-Efficiency): Features an inverter-driven 1.5-ton ducted mini-split heat pump air handler and compact duct network installed entirely within the conditioned thermal envelope created by closed-cell spray foam applied directly to the roof deck.
2. Capital Cost & Installation Comparison
Traditional 3-Ton System Cost: Approximately $7,500.00 installed.
Conditioned Attic 1.5-Ton Ducted Mini-Split Cost: Initial equipment and installation total $9,200.00 ($1,700 upfront capital expenditure premium).
3. Operational Savings & Maintenance Longevity
Annual Energy Savings: Reduces annual cooling and heating energy consumption by 20% to 25%, saving tenants $35.00 to $50.00 per month (averaging $540.00 annually).
Equipment Lifespan: Extends reliable mechanical lifespan from 10-12 years up to 15+ years.
4. Break-Even Point: Achieved in approximately 3.1 Years (38 Months).""",
          "Addendum_5_Conditioned_Attic.pdf",
          cat_folder_ids["Building Envelope & Sizing"],
      ),
      (
          "Addendum 6 & 7: Smart Security Ecosystem & Financial Return",
          (
              "Keyless Access & Surveillance ($600 initial hardware"
              " investment generating a $25/mo rent premium, breaking even"
              " in 24 months)."
          ),
          """Addendum 6 & 7: Smart Security Ecosystem & Financial Return
To substantiate asset management and tenant attraction specifications, this analysis evaluates the integration of a hybrid DIY smart security ecosystem across the 24-lot portfolio.
1. System Architecture & Build Specifications
Access Control: Standalone smart deadbolts (Schlage or Ultraloq) to manage keyless entry codes for tenants, vendors, and property management staff without requiring locked-in proprietary enterprise monitoring contracts.
Perimeter Surveillance: Plug-and-play Ring Video Doorbell units providing high-definition surveillance at minimal hardware cost ($100-$250 per unit) and zero mandatory landlord monitoring fees.
2. Financial & Operational Return Analysis
Direct Rent Bump: Smart home features support a monthly rent increase of $15.00 to $30.00 ($180 to $360 annually per unit) and accelerate leasing velocity.
Turnover Savings: Programmable smart access codes eliminate traditional locksmith rekeying fees ($50 to $100 per turnover).
3. Break-Even Point & Return Calculation
Total Initial Hardware Investment: $600.00 per unit. Monthly Rent Bump: $25.00 ($300/year). Break-Even: Exactly 24 Months (2.0 Years).""",
          "Addendum_6_7_Smart_Security.pdf",
          cat_folder_ids["Turnover & Asset Durability"],
      ),
      (
          "Addendum 8: Omission of Ceiling Fans",
          (
              "Spray-foam insulated envelopes maintain consistent room"
              " temperatures, rendering conventional ceiling fans"
              " mechanically unnecessary."
          ),
          """Addendum 8: Omission of Ceiling Fans in High-Performance HVAC Build-to-Rent Homes
To substantiate operational streamlining and capital expenditure efficiency, this analysis evaluates the total cost and long-term liability savings of omitting ceiling fans in a high-performance build-to-rent (BTR) home equipped with 2x6 framing, closed-cell spray foam insulation, and a ducted mini-split system.
1. Mechanical & Thermal Justification (Why Fans Are Unnecessary)
Thermal Uniformity via Spray Foam: Encapsulating the home in closed-cell spray foam (2x6 walls and roof deck) eliminates convective air currents, thermal bridging, and severe hot/cold stratification.
Inverter Mini-Split Performance: Inverter-driven ducted mini-split systems run continuous, low-speed cycles that maintain precise, balanced airflow across all rooms.
2. Capital Cost & Installation Comparison
Standard Build: Equipping a home with standard ceiling fans averages $1,400.00 to $1,800.00 per unit.
High-Performance Build: Omitting ceiling fans entirely eliminates this capital expenditure, saving $1,600.00 upfront per unit ($38,400 across the 24-lot portfolio).
3. Ongoing Maintenance & Turnover Savings: Eliminates recurring minor service calls ($75-$150 per repair) and mid-cycle replacement outlays every 5 to 7 years.""",
          "Addendum_8_Ceiling_Fans.pdf",
          cat_folder_ids["Building Envelope & Sizing"],
      ),
      (
          (
              "Addendum 9: High-Durability Commercial Fixtures vs. Standard"
              " Builder-Grade Assets"
          ),
          (
              "Evaluates upgrading plumbing, hardware, and lighting to"
              " commercial-grade BTR assets across a 15-year holding period,"
              " achieving break-even in 3.8 years."
          ),
          """Addendum 9: High-Durability Commercial Fixtures vs. Standard Builder-Grade Assets (15-Year Maintenance Analysis)
To substantiate long-term maintenance reduction and turnover efficiency, this analysis evaluates upgrading key plumbing, hardware, and lighting fixtures from standard builder-grade tier to commercial-grade BTR assets across a 15-year holding period.
1. Asset Specifications & Cost Tier Comparison (Per Unit Baseline)
Plumbing Fixtures (Faucets & Shower Valves): Solid brass construction with ceramic-disc cartridges ($450 total per unit) rated for 500,000+ cycles compared to plastic-cartridge builder grade ($150).
Door Hardware: Heavy-duty Grade 2 cylindrical lever handles ($350 total per unit) exceeding 400,000 cycle testing.
Lighting Fixtures: Integrated sealed LED flush-mount fixtures ($320 total per unit) rated for 50,000+ hours with zero bulb changes.
2. Lifecycle Cost & Maintenance Savings (15-Year Horizon)
Builder-grade assets require 3 full replacement cycles over 15 years ($1,690 total lifecycle cost per unit), plus emergency water damage claims averaging $650 per incident. Commercial assets last 15+ years with zero mid-cycle rebuilds ($1,240 total lifecycle cost per unit).
3. Break-Even Point: Achieved in 3.8 Years (approx. 45 Months).""",
          "Addendum_9_Commercial_Fixtures.pdf",
          cat_folder_ids["Turnover & Asset Durability"],
      ),
      (
          (
              "Addendum 10: Interior Door Selection & Break-Even Financial"
              " Analysis"
          ),
          (
              "Evaluates standard hollow-core doors against high-durability"
              " solid-core engineered wood/MDF doors, achieving break-even in"
              " 4.2 years."
          ),
          """Addendum 10: Interior Door Selection & Break-Even Financial Analysis for Build-to-Rent Portfolios
To support institutional asset longevity and minimize recurring operational friction across Wickboldt Capital’s 24-lot portfolio, this analysis evaluates standard hollow-core doors against high-durability solid-core engineered wood/MDF doors over a 15-year holding period.
1. Material Performance & BTR Engineering Rationale
Hollow-Core Doors: Lightweight skin over honeycomb cardboard; easily punctured, warp from humidity, and experience hinge pull-out.
Solid-Core Engineered Wood / MDF Doors: Dense composite interior core providing superior acoustic sound dampening, dent resistance, and heavy premium feel.
2. Upfront Capital Cost & Replacement Assumptions
Hollow-Core Cost: ~$450 total across 6 interior doors per unit; requires full replacement every 4 to 5 years in rental service.
Solid-Core Cost: ~$1,100 total across 6 interior doors per unit, representing an upfront premium of $650.00 per unit.
3. Break-Even Point: 4.2 Years (approx. 50 Months).""",
          "Addendum_10_Interior_Doors.pdf",
          cat_folder_ids["Turnover & Asset Durability"],
      ),
  ]

  for i in range(11, 54):
    cat_name = "Engineering & Design Briefs"
    for c_title, c_list in categories_map:
      if i in c_list:
        cat_name = c_title
        break
    f_id = cat_folder_ids.get(cat_name, eng_folder_id)

    title_str = f"Addendum {i}: Portfolio Engineering & Underwriting Standard"
    snippet_str = (
        f"Official Wickboldt Capital standard specification for Addendum {i},"
        " detailing hard/soft economics, material compliance, and long-term NOI"
        " optimization."
    )
    full_text_str = f"""Wickboldt Capital Build-to-Rent Master Specification
Document ID: Addendum {i}
Portfolio Development: Rogers Moore Parkway (24 Units, Hammond, LA)

1. EXECUTIVE SUMMARY & ENGINEERING MANDATE
This specification outlines the institutional design, procurement, and financial underwriting parameters governing Addendum {i}. All general contractors and trade partners must execute construction in strict compliance with these performance standards.

2. MATERIAL & STRUCTURAL SPECIFICATIONS
- Quality Standard: Commercial-grade BTR tier exceeding standard residential builder-grade specifications by at least 40%.
- Durability & Maintenance: Engineered for zero mid-cycle replacement over a 15-year holding period, directly lowering tenant turnover operating costs from $2,500 down to $700 per event.
- Energy Efficiency: Fully integrated with closed-cell spray foam thermal envelopes, right-sized HVAC mini-split systems, and active HEEHRA/DEMCO rebate allocations.

3. FINANCIAL UNDERWRITING & RETURN IMPACT
- Upfront Capital Outlay: Offset entirely by energy rebates, utility bundling revenue deltas, or reduced turnover expenses.
- Net Operating Income (NOI) Expansion: Contributes directly to portfolio valuation scaling at a 6.5% capitalization rate, preserving a minimum 1.20 DSCR across all debt financing structures."""

    filename_str = f"Addendum_{i}_Specification.pdf"
    addendums.append(
        (title_str, snippet_str, full_text_str, filename_str, f_id)
    )

  for title, snippet, full_text, filename, folder_id in addendums:
    pdf_bytes = convert_text_to_pdf_bytes(title, full_text)
    cursor.execute(
        """
            INSERT INTO documents (project_id, folder_id, title, snippet, full_text, file_name, file_data, uploaded_at)
            VALUES (0, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            folder_id,
            title,
            snippet,
            full_text,
            filename,
            pdf_bytes,
            timestamp,
        ),
    )

  conn.commit()
  conn.close()


seed_master_environment()


def seed_project_environment(proj_id, proj_name):
  """Ensures new projects start with default root folders and admin-configured default values."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT COUNT(*) FROM folders WHERE project_id = ?", (proj_id,)
  )
  if cursor.fetchone()[0] == 0:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_folders = ["Engineering Specs", "Permits & Zoning", "Loan Documents"]
    for fname in default_folders:
      cursor.execute(
          "INSERT INTO folders (project_id, parent_folder_id, folder_name,"
          " created_at) VALUES (?, NULL, ?, ?)",
          (proj_id, fname, timestamp),
      )
    conn.commit()
  conn.close()


def render_folder_tree_with_sorting(
    project_id,
    parent_id=None,
    level=0,
    sort_order="Alphabetical (A-Z)",
    is_admin=False,
):
  """Recursively renders folders, sub-layers, and naturally sorted documents."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()

  if parent_id is None:
    cursor.execute(
        "SELECT folder_id, folder_name FROM folders WHERE project_id = ? AND"
        " parent_folder_id IS NULL",
        (project_id,),
    )
  else:
    cursor.execute(
        "SELECT folder_id, folder_name FROM folders WHERE project_id = ? AND"
        " parent_folder_id = ?",
        (project_id, parent_id),
    )
  sub_folders = cursor.fetchall()

  sub_folders = sorted(
      sub_folders,
      key=lambda x: natural_sort_key(x[1]),
      reverse=(sort_order == "Alphabetical (Z-A)"),
  )

  if parent_id is None:
    cursor.execute(
        """
            SELECT doc_id, title, snippet, full_text, file_name, file_data, uploaded_at 
            FROM documents 
            WHERE project_id = ? AND (folder_id IS NULL OR folder_id NOT IN (SELECT folder_id FROM folders WHERE project_id = ?))
        """,
        (project_id, project_id),
    )
  else:
    cursor.execute(
        """
            SELECT doc_id, title, snippet, full_text, file_name, file_data, uploaded_at 
            FROM documents 
            WHERE project_id = ? AND folder_id = ? 
        """,
        (project_id, parent_id),
    )
  folder_docs = cursor.fetchall()
  conn.close()

  indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * level

  if folder_docs:
    doc_groups = {}
    for d in folder_docs:
      t = d[1]
      if t not in doc_groups:
        doc_groups[t] = []
      doc_groups[t].append(d)

    titles = list(doc_groups.keys())
    if sort_order == "Alphabetical (A-Z)":
      titles = sorted(titles, key=natural_sort_key)
    elif sort_order == "Alphabetical (Z-A)":
      titles = sorted(titles, key=natural_sort_key, reverse=True)
    elif sort_order == "Date Uploaded (Newest First)":
      titles = sorted(
          titles,
          key=lambda t: max(rev[6] for rev in doc_groups[t]),
          reverse=True,
      )
    elif sort_order == "Date Uploaded (Oldest First)":
      titles = sorted(
          titles, key=lambda t: min(rev[6] for rev in doc_groups[t])
      )

    for title in titles:
      revisions = doc_groups[title]
      latest_doc = revisions[0]
      doc_id, _, snippet, full_text, file_name, file_data, uploaded_at = (
          latest_doc
      )

      prefix = f"{indent}📄 "
      with st.expander(f"{prefix} {title}  *(Latest: {uploaded_at})*"):
        st.markdown(f"**Executive Description / Snippet:**\n> {snippet}")
        st.markdown(f"**File Name:** `{file_name}`")

        col_d1, col_d2 = st.columns([2, 6])
        with col_d1:
          if file_data:
            st.download_button(
                label="📥 Download PDF",
                data=file_data,
                file_name=file_name,
                mime="application/pdf",
                key=f"download_tree_doc_{doc_id}_{project_id}_{level}",
            )
        with col_d2:
          if file_data:
            view_key = f"view_tree_content_{doc_id}_{project_id}_{level}"
            if st.button(
                "👁️ View Full Document Text",
                key=f"btn_tree_view_{doc_id}_{project_id}_{level}",
            ):
              st.session_state[view_key] = not st.session_state.get(
                  view_key, False
              )

        if st.session_state.get(
            f"view_tree_content_{doc_id}_{project_id}_{level}", False
        ):
          display_text = full_text if full_text else snippet
          st.text_area(
              "Complete Document Text Content",
              display_text,
              height=350,
              key=f"txt_preview_{doc_id}_{project_id}_{level}",
          )

        if len(revisions) > 1:
          st.markdown("---")
          rev_toggle_key = f"show_tree_revs_{doc_id}_{project_id}_{level}"
          if st.button(
              f"🕒 View Old Revisions ({len(revisions)-1} previous version"
              f"{'s' if len(revisions)>2 else ''})",
              key=f"btn_tree_revs_{doc_id}_{project_id}_{level}",
          ):
            st.session_state[rev_toggle_key] = not st.session_state.get(
                rev_toggle_key, False
            )

          if st.session_state.get(rev_toggle_key, False):
            for old_rev in revisions[1:]:
              (
                  old_id,
                  _,
                  old_snippet,
                  old_full_text,
                  old_filename,
                  old_data,
                  old_timestamp,
              ) = old_rev
              sub_c1, sub_c2, sub_c3 = st.columns([3, 3, 4])
              with sub_c1:
                st.markdown(f"🗓️ `{old_timestamp}`")
              with sub_c2:
                old_view_key = f"view_tree_old_content_{old_id}_{level}"
                if st.button("👁️ View", key=f"btn_tree_old_view_{old_id}_{level}"):
                  st.session_state[old_view_key] = not st.session_state.get(
                      old_view_key, False
                  )
              with sub_c3:
                st.download_button(
                    label=f"📥 Download ({old_filename})",
                    data=old_data,
                    file_name=f"rev_{old_timestamp[:10]}_{old_filename}",
                    mime="application/pdf",
                    key=f"download_tree_old_{old_id}_{level}",
                )
              if st.session_state.get(
                  f"view_tree_old_content_{old_id}_{level}", False
              ):
                old_display = (
                    old_full_text if old_full_text else old_snippet
                )
                st.text_area(
                    f"Archived Version Text ({old_timestamp})",
                    old_display,
                    height=200,
                    key=f"old_txt_preview_{old_id}_{level}",
                )

  for f_id, f_name in sub_folders:
    folder_prefix = (
        f"{indent}📂 **{f_name}**"
        if level == 0
        else f"{indent}📁 {f_name}"
    )
    st.markdown(folder_prefix, unsafe_allow_html=True)
    render_folder_tree_with_sorting(
        project_id,
        parent_id=f_id,
        level=level + 1,
        sort_order=sort_order,
        is_admin=is_admin,
    )


# Page Config
st.set_page_config(
    page_title="Wickboldt Capital Portal", layout="wide", initial_sidebar_state="expanded"
)

st.title("🏗️ Wickboldt Capital: Rogers Moore Parkway Portal")
st.markdown("*Today's Foundation. Tomorrow's Legacy.*")

# --- USER AUTHENTICATION & SESSION STATE SETUP ---
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
if "username" not in st.session_state:
  st.session_state["username"] = ""
if "role" not in st.session_state:
  st.session_state["role"] = "User"

# --- SIDEBAR: USER AUTHENTICATION & LOGIN/LOGOUT ---
st.sidebar.header("🔐 User Authentication")

if not st.session_state["logged_in"]:
  with st.sidebar.form("login_form"):
    login_user = st.text_input("Username", "admin")
    login_pass = st.text_input("Password", type="password", value="admin123")
    submit_login = st.form_submit_button("Sign In")

    if submit_login:
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT role FROM users WHERE username = ? AND password_hash = ?",
          (login_user.strip(), hash_password(login_pass)),
      )
      user_row = cursor.fetchone()
      conn.close()

      if user_row:
        st.session_state["logged_in"] = True
        st.session_state["username"] = login_user.strip()
        st.session_state["role"] = user_row[0]
        st.sidebar.success(
            f"Logged in as {login_user.strip()} ({user_row[0]})!"
        )
        st.rerun()
      else:
        st.sidebar.error("Invalid username or password.")
  st.sidebar.info(
      "💡 *Default credentials:* &nbsp;\n- **Admin:** `admin` / `admin123`\n-"
      " **User:** `user` / `user123`"
  )
else:
  st.sidebar.success(
      f"👤 Logged in: **{st.session_state['username']}**"
      f" (*{st.session_state['role']}*)"
  )
  if st.sidebar.button("Sign Out"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = "User"
    st.rerun()

is_admin = (
    st.session_state["logged_in"] and st.session_state["role"] == "Admin"
)

# --- FETCH ADMIN DEFAULTS FROM DATABASE ---
def_sqft = get_admin_setting("default_sqft", 1150.0)
def_arv = get_admin_setting("default_arv", 230000.0)
def_rent = get_admin_setting("default_annual_rent", 20400.0)
def_opex = get_admin_setting("default_opex", 6120.0)
def_con_loan = get_admin_setting("default_con_loan", 131959.93)
def_refi_loan = get_admin_setting("default_refi_loan", 149531.06)
def_equity = get_admin_setting("default_equity_pct", 35.0)

# --- INITIALIZE SHARED SESSION STATE WITH ADMIN DEFAULTS ---
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
  st.session_state["shared_equity_pct"] = def_equity
if "shared_refi_equity_pct" not in st.session_state:
  st.session_state["shared_refi_equity_pct"] = def_equity
if "shared_annual_rent" not in st.session_state:
  st.session_state["shared_annual_rent"] = def_rent
if "shared_opex" not in st.session_state:
  st.session_state["shared_opex"] = def_opex
if "shared_arv" not in st.session_state:
  st.session_state["shared_arv"] = def_arv
if "target_con_dscr" not in st.session_state:
  st.session_state["target_con_dscr"] = 1.20
if "target_refi_dscr" not in st.session_state:
  st.session_state["target_refi_dscr"] = 1.20
if "active_revision_label" not in st.session_state:
  st.session_state["active_revision_label"] = "Comprehensive Proforma Baseline"

# --- SIDEBAR: NAVIGATION & REVISION MANAGER ---
st.sidebar.markdown("---")
st.sidebar.header("🧭 Main Menu")
nav_options = [
    "📊 Unit Proforma",
    "🏗️ Cost Estimator & Budget",
    "💰 Capital Stack",
    "📈 10-Year Forecast",
    "🏗️ Engineering",
    "🏢 Master Company Library",
    "📁 Project Document Control",
]
if is_admin:
  nav_options.append("⚙️ [ADMIN] Global Defaults")

main_section = st.sidebar.radio("Go to Section", nav_options)

st.sidebar.markdown("---")
st.sidebar.header("📁 Project & Revision Control")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT project_id, project_name FROM projects")
proj_records = cursor.fetchall()
conn.close()

projects = [row[1] for row in proj_records]
proj_id_map = {row[1]: row[0] for row in proj_records}

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
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        seed_project_environment(new_id, new_proj_name)
        st.session_state["active_revision_label"] = "Initial Baseline"
        st.sidebar.success(f"Initialized '{new_proj_name}'!")
        st.rerun()
      except sqlite3.IntegrityError:
        st.sidebar.error("Project name already exists.")

selected_project = None
selected_proj_id = None
if projects:
  selected_project = st.sidebar.selectbox("Select Project", projects)
  selected_proj_id = proj_id_map.get(selected_project)
  if selected_proj_id:
    seed_project_environment(selected_proj_id, selected_project)

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
  if selected_project and selected_proj_id:
    current_state = {
        "equity_pct": st.session_state.get(
            "shared_refi_equity_pct", def_equity
        ),
        "annual_rent": st.session_state.get("shared_annual_rent", def_rent),
        "opex": st.session_state.get("shared_opex", def_opex),
        "grand_total_cost": st.session_state.get("grand_total_cost", 201250.00),
    }
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO revisions (project_id, revision_name, timestamp, data_json)
            VALUES (?, ?, ?, ?)
        """,
        (
            selected_proj_id,
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

# --- 1. UNIT PROFORMA ---
if main_section == "📊 Unit Proforma":
  st.header("📊 Comprehensive Financial Underwriting & Budget Recap")
  st.markdown(
      "Consolidated financial summary pulling live data directly from your"
      " functional tabs. All key return metrics are fully linked and active."
  )

  grand_total = st.session_state.get("grand_total_cost", 201250.00)
  unit_sqft = st.session_state.get("est_sqft", def_sqft)
  cost_per_sf = grand_total / unit_sqft if unit_sqft > 0 else 0.0

  con_loan = st.session_state.get("active_con_loan_amt", def_con_loan)
  refi_loan = st.session_state.get("active_refi_loan_amt", def_refi_loan)
  annual_rent = st.session_state.get("shared_annual_rent", def_rent)
  opex = st.session_state.get("shared_opex", def_opex)
  arv = st.session_state.get("shared_arv", def_arv)
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
        value=def_sqft,
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
    m_tot3.metric(
        "Square Footage Basis",
        (
            f"{unit_sqft:,.0f} sq ft"
            if "unit_sqft" in locals()
            else "1,150 sq ft"
        ),
    )

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
  current_annual_rent = st.session_state.get("shared_annual_rent", def_rent)
  current_opex = st.session_state.get("shared_opex", def_opex)
  annual_noi = current_annual_rent - current_opex

  st.subheader("2. Construction Loan Inputs & DSCR Analysis")
  con_loan_amt = st.number_input(
      "Construction Loan Facility Limit ($)",
      value=def_con_loan,
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
        value=def_arv,
        step=1000.0,
        format="%.2f",
        key="stack_appraised_value",
    )
    st.session_state["shared_arv"] = appraised_value
    refi_equity_pct = st.slider(
        "Refinance Equity Position (%)",
        min_value=0.0,
        max_value=100.0,
        value=def_equity,
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
        value=def_equity,
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
  curr_val = st.session_state.get("shared_arv", def_arv)
  curr_loan = st.session_state.get("active_refi_loan_amt", def_refi_loan)
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

# --- 5. ENGINEERING ---
elif main_section == "🏗️ Engineering":
  sub_tab1, sub_tab2 = st.tabs(
      ["🏗️ Master Dashboard", "📑 Technical Addendums"]
  )

  with sub_tab1:
    st.header("Rogers Moore Parkway Master Development")
    st.info("**Project Scope:** 24 total building lots in Hammond, Louisiana.")

  with sub_tab2:
    st.header("Technical Specifications & Addendums")
    st.markdown("Engineering standards and cost-benefit breakdowns.")

# --- 6. MASTER COMPANY LIBRARY ---
elif main_section == "🏢 Master Company Library":
  st.header("🏢 Wickboldt Capital: Master Company Library")
  st.markdown(
      "Central repository containing company-wide governance procedures and"
      " master specifications organized in a Windows Explorer-style nested"
      " folder tree."
  )

  if not is_admin:
    st.info(
        "🔒 **Viewing Mode (Public / Standard User):** You have full read,"
        " search, and download access to the Master Company Library. Folder"
        " reorganization and management require Administrator credentials."
    )

  sort_m_col1, sort_m_col2 = st.columns([3, 3])
  with sort_m_col1:
    master_sort_order = st.selectbox(
        "Sort Master Library View By",
        [
            "Alphabetical (A-Z)",
            "Alphabetical (Z-A)",
            "Date Uploaded (Newest First)",
            "Date Uploaded (Oldest First)",
        ],
        key="master_sort_select",
    )

  if is_admin:
    with st.expander("📁 [ADMIN] Reorganize & Move Master Folders"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT folder_id, folder_name FROM folders WHERE project_id = 0 ORDER"
          " BY folder_name ASC"
      )
      m_all_folders = cursor.fetchall()
      conn.close()

      if m_all_folders:
        m_folder_dict = {f"{f[1]} (ID: {f[0]})": f[0] for f in m_all_folders}
        m_parent_dict = {"[Root Level / No Parent]": None}
        for f in m_all_folders:
          m_parent_dict[f"{f[1]} (ID: {f[0]})"] = f[0]

        with st.form("move_master_folder_form"):
          sel_move_folder = st.selectbox(
              "Select Folder to Move", list(m_folder_dict.keys())
          )
          sel_new_parent = st.selectbox(
              "Move Inside New Parent Folder", list(m_parent_dict.keys())
          )
          submit_move = st.form_submit_button("Move Folder Location")

          if submit_move:
            f_to_move_id = m_folder_dict[sel_move_folder]
            new_parent_id = m_parent_dict[sel_new_parent]
            if f_to_move_id == new_parent_id:
              st.error("A folder cannot be placed inside itself.")
            else:
              conn = sqlite3.connect(DB_FILE)
              cursor = conn.cursor()
              cursor.execute(
                  "UPDATE folders SET parent_folder_id = ? WHERE folder_id = ?",
                  (new_parent_id, f_to_move_id),
              )
              conn.commit()
              conn.close()
              st.success("Folder location updated successfully!")
              st.rerun()

    with st.expander("➕ [ADMIN] Create New Master Folders (Sub-Layers)"):
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT folder_id, folder_name FROM folders WHERE project_id = 0 ORDER"
          " BY folder_name ASC"
      )
      existing_m_folders = cursor.fetchall()
      conn.close()

      parent_m_options = {"[Root Level]": None}
      for f_id, f_name in existing_m_folders:
        parent_m_options[f"📁 {f_name} (ID: {f_id})"] = f_id

      with st.form("new_master_subfolder_form"):
        sub_m_name = st.text_input("New Folder Name", "e.g., Financial Policies")
        selected_m_parent_label = st.selectbox(
            "Parent Folder Location", list(parent_m_options.keys())
        )
        submit_m_sub = st.form_submit_button("Create Sub-Folder")
        if submit_m_sub and sub_m_name:
          p_id_val = parent_m_options[selected_m_parent_label]
          conn = sqlite3.connect(DB_FILE)
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO folders (project_id, parent_folder_id, folder_name,"
              " created_at) VALUES (0, ?, ?, ?)",
              (
                  p_id_val,
                  sub_m_name,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              ),
          )
          conn.commit()
          conn.close()
          st.success(f"Master sub-folder '{sub_m_name}' created successfully!")
          st.rerun()
    st.markdown("---")

  render_folder_tree_with_sorting(
      project_id=0,
      parent_id=None,
      level=0,
      sort_order=master_sort_order,
      is_admin=is_admin,
  )

# --- [ADMIN] GLOBAL DEFAULTS CONFIGURATION TAB ---
elif main_section == "⚙️ [ADMIN] Global Defaults":
  if not is_admin:
    st.error("Access Denied. Administrator credentials required.")
  else:
    st.header("⚙️ Admin Global Underwriting Defaults")
    st.markdown(
        "Configure the master default values that automatically populate across"
        " all tabs and newly initialized projects."
    )

    with st.form("admin_defaults_form"):
      c_ad1, c_ad2 = st.columns(2)
      with c_ad1:
        new_def_sqft = st.number_input(
            "Default Unit Square Footage (SF)",
            value=float(def_sqft),
            step=25.0,
            format="%.2f",
        )
        new_def_arv = st.number_input(
            "Default Appraised Value / ARV ($)",
            value=float(def_arv),
            step=1000.0,
            format="%.2f",
        )
        new_def_rent = st.number_input(
            "Default Annual Rental Income ($)",
            value=float(def_rent),
            step=500.0,
            format="%.2f",
        )
        new_def_opex = st.number_input(
            "Default Operating Expenses ($)",
            value=float(def_opex),
            step=100.0,
            format="%.2f",
        )
      with c_ad2:
        new_def_con = st.number_input(
            "Default Construction Loan Limit ($)",
            value=float(def_con_loan),
            step=1000.0,
            format="%.2f",
        )
        new_def_refi = st.number_input(
            "Default Permanent Refi Loan Limit ($)",
            value=float(def_refi_loan),
            step=1000.0,
            format="%.2f",
        )
        new_def_equity = st.number_input(
            "Default Refinance Equity Position (%)",
            value=float(def_equity),
            step=1.0,
            format="%.2f",
        )

      submit_admin_defs = st.form_submit_button("Save Global Defaults")

      if submit_admin_defs:
        set_admin_setting("default_sqft", new_def_sqft)
        set_admin_setting("default_arv", new_def_arv)
        set_admin_setting("default_annual_rent", new_def_rent)
        set_admin_setting("default_opex", new_def_opex)
        set_admin_setting("default_con_loan", new_def_con)
        set_admin_setting("default_refi_loan", new_def_refi)
        set_admin_setting("default_equity_pct", new_def_equity)
        st.success("Global underwriting defaults successfully updated!")
        st.rerun()

# --- 7. PROJECT DOCUMENT CONTROL ---
elif main_section == "📁 Project Document Control":
  st.header("📁 Project Document Control & Repository")
  st.markdown(
      "Manage project-specific folders and documents. Uploaded files are"
      " automatically synced as copies into the Master Company Library."
  )

  if not selected_project or not selected_proj_id:
    st.warning(
        "⚠️ Please select or create a project in the sidebar to manage its"
        " documents."
    )
  else:
    doc_tab1, doc_tab2, doc_tab3 = st.tabs([
        "📂 Upload Project Document",
        "📑 Project Document Library",
        "🏢 View Master Company Library",
    ])

    with doc_tab1:
      st.subheader(f"Upload Document for: {selected_project}")

      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute(
          "SELECT folder_id, folder_name FROM folders WHERE project_id = ?"
          " ORDER BY folder_name ASC",
          (selected_proj_id,),
      )
      proj_folders = cursor.fetchall()
      conn.close()

      folder_options = {f[1]: f[0] for f in proj_folders}

      with st.form("upload_doc_form"):
        doc_title = st.text_input(
            "Document Title", "e.g., RMP-ENG-001: Lot Specific Permit"
        )
        doc_snippet = st.text_area(
            "Executive Snippet / Description",
            "Brief summary of contents, specifications, or key guidelines...",
        )
        doc_full_text = st.text_area(
            "Full Document Text Content",
            "Paste or type the complete text content of the document here...",
        )
        selected_folder_name = st.selectbox(
            "Select Target Project Folder", list(folder_options.keys())
        )

        new_folder_input = st.text_input(
            "Or Create New Sub-Folder inside Project (Optional)", ""
        )

        uploaded_file = st.file_uploader(
            "Upload Document File (PDF, TXT, DOCX)",
            type=["pdf", "txt", "docx"],
        )

        submit_upload = st.form_submit_button(
            "Save to Project & Sync to Master Library"
        )

        if submit_upload:
          if doc_title and selected_proj_id:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if uploaded_file is not None:
              raw_bytes = uploaded_file.read()
              file_name = uploaded_file.name
              if not file_name.lower().endswith(".pdf"):
                try:
                  text_str = raw_bytes.decode("utf-8")
                except Exception:
                  text_str = doc_full_text or doc_snippet
                file_bytes = convert_text_to_pdf_bytes(doc_title, text_str)
                file_name = file_name.rsplit(".", 1)[0] + ".pdf"
              else:
                file_bytes = raw_bytes
              extracted_text = doc_full_text if doc_full_text.strip() else text_str
            else:
              file_name = f"{doc_title.replace(':', '').replace(' ', '_')}.pdf"
              extracted_text = (
                  doc_full_text if doc_full_text.strip() else doc_snippet
              )
              file_bytes = convert_text_to_pdf_bytes(doc_title, extracted_text)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            parent_f_id = folder_options[selected_folder_name]
            target_folder_id = parent_f_id
            target_folder_name = selected_folder_name

            if new_folder_input.strip():
              cursor.execute(
                  "INSERT INTO folders (project_id, parent_folder_id,"
                  " folder_name, created_at) VALUES (?, ?, ?, ?)",
                  (
                      selected_proj_id,
                      parent_f_id,
                      new_folder_input.strip(),
                      timestamp,
                  ),
              )
              target_folder_id = cursor.lastrowid
              target_folder_name = new_folder_input.strip()

            cursor.execute(
                """
                INSERT INTO documents (project_id, folder_id, title, snippet, full_text, file_name, file_data, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    selected_proj_id,
                    target_folder_id,
                    doc_title,
                    doc_snippet,
                    extracted_text,
                    file_name,
                    file_bytes,
                    timestamp,
                ),
            )

            cursor.execute(
                "SELECT folder_id FROM folders WHERE project_id = 0 AND"
                " folder_name = ?",
                (target_folder_name,),
            )
            m_f_row = cursor.fetchone()
            if m_f_row:
              master_target_folder_id = m_f_row[0]
            else:
              cursor.execute(
                  "INSERT INTO folders (project_id, parent_folder_id,"
                  " folder_name, created_at) VALUES (0, NULL, ?, ?)",
                  (target_folder_name, timestamp),
              )
              master_target_folder_id = cursor.lastrowid

            master_title = f"[{selected_project}] {doc_title}"
            cursor.execute(
                """
                INSERT INTO documents (project_id, folder_id, title, snippet, full_text, file_name, file_data, uploaded_at)
                VALUES (0, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    master_target_folder_id,
                    master_title,
                    doc_snippet,
                    extracted_text,
                    file_name,
                    file_bytes,
                    timestamp,
                ),
            )

            conn.commit()
            conn.close()
            st.success(
                f"Successfully saved '{doc_title}' to folder"
                f" '{target_folder_name}' in {selected_project} AND synced a"
                " copy to the Master Company Library!"
            )
          else:
            st.error("Please provide a document title.")

    with doc_tab2:
      st.subheader(f"Project Library for: {selected_project}")

      sort_p_col1, sort_p_col2 = st.columns([3, 3])
      with sort_p_col1:
        project_sort_order = st.selectbox(
            "Sort Project Library View By",
            [
                "Alphabetical (A-Z)",
                "Alphabetical (Z-A)",
                "Date Uploaded (Newest First)",
                "Date Uploaded (Oldest First)",
            ],
            key="proj_sort_select",
        )

      with st.expander("📁 Reorganize & Move Project Folders"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_id, folder_name FROM folders WHERE project_id = ?"
            " ORDER BY folder_name ASC",
            (selected_proj_id,),
        )
        p_all_folders = cursor.fetchall()
        conn.close()

        if p_all_folders:
          p_folder_dict = {f"{f[1]} (ID: {f[0]})": f[0] for f in p_all_folders}
          p_parent_dict = {"[Root Level / No Parent]": None}
          for f in p_all_folders:
            p_parent_dict[f"{f[1]} (ID: {f[0]})"] = f[0]

          with st.form("move_proj_folder_form"):
            sel_p_move = st.selectbox(
                "Select Project Folder to Move", list(p_folder_dict.keys())
            )
            sel_p_parent = st.selectbox(
                "Move Inside New Parent Folder", list(p_parent_dict.keys())
            )
            submit_p_move = st.form_submit_button("Move Project Folder")

            if submit_p_move:
              p_move_id = p_folder_dict[sel_p_move]
              p_new_parent_id = p_parent_dict[sel_p_parent]
              if p_move_id == p_new_parent_id:
                st.error("A folder cannot be placed inside itself.")
              else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE folders SET parent_folder_id = ? WHERE folder_id ="
                    " ?",
                    (p_new_parent_id, p_move_id),
                )
                conn.commit()
                conn.close()
                st.success("Project folder location updated successfully!")
                st.rerun()

      with st.expander("➕ Create New Project Folder / Sub-Layer"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT folder_id, folder_name FROM folders WHERE project_id = ?"
            " ORDER BY folder_name ASC",
            (selected_proj_id,),
        )
        proj_all_folders = cursor.fetchall()
        conn.close()

        parent_p_options = {"[Root Level]": None}
        for f_id, f_name in proj_all_folders:
          parent_p_options[f"📁 {f_name} (ID: {f_id})"] = f_id

        with st.form("new_proj_subfolder_form"):
          sub_p_name = st.text_input(
              "Folder / Sub-Layer Name", "e.g., Phase 1 Sub-Bids"
          )
          selected_p_parent_label = st.selectbox(
              "Parent Location", list(parent_p_options.keys())
          )
          submit_p_sub = st.form_submit_button("Create Folder Layer")
          if submit_p_sub and sub_p_name:
            p_id_val = parent_p_options[selected_p_parent_label]
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO folders (project_id, parent_folder_id,"
                " folder_name, created_at) VALUES (?, ?, ?, ?)",
                (
                    selected_proj_id,
                    p_id_val,
                    sub_p_name,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            conn.close()
            st.success(
                f"Project folder layer '{sub_p_name}' created successfully!"
            )
            st.rerun()

      st.markdown("---")
      render_folder_tree_with_sorting(
          project_id=selected_proj_id,
          parent_id=None,
          level=0,
          sort_order=project_sort_order,
          is_admin=is_admin,
      )

    with doc_tab3:
      st.subheader("🏢 Master Company Library (Company-Wide Access)")
      st.markdown(
          "Viewing master company folders and project-synced files organized in"
          " a Windows Explorer-style nested folder tree:"
      )
      render_folder_tree_with_sorting(
          project_id=0,
          parent_id=None,
          level=0,
          sort_order="Alphabetical (A-Z)",
          is_admin=is_admin,
      )