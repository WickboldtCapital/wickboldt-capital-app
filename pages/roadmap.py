import streamlit as st
import pandas as pd

st.set_page_config(page_title="Enterprise Roadmap", layout="wide")

st.title("Enterprise Development Roadmap & Master Log 🚀")
st.markdown("Official master tracking log and architectural roadmap for **Wickboldt Capital** (`WickboldtApp`).")

# --- QUICK LINKS ---
st.markdown("### 🔗 Quick Links & Resources")
st.markdown("""
* **Live Enterprise Portal:** [portal.wickboldtcapital.com](https://portal.wickboldtcapital.com)
* **GitHub Repository:** [WickboldtCapital/wickboldt-capital-app](https://github.com/WickboldtCapital/wickboldt-capital-app)
* **Public Marketing Site:** [wickboldtcapital.com](https://wickboldtcapital.com) (Hosted on Netlify)
""")

st.divider()

# --- ROADMAP SECTIONS ---
st.markdown("## Phase 0: Infrastructure & Deployment")
st.markdown("""
- **Local Scaffold:** Built core multi-page Python/Streamlit framework with dynamic routing. *(Status: Completed)*
- **Database Migration:** Upgraded from local SQLite to a production-grade Supabase PostgreSQL instance. *(Status: Completed)*
- **Version Control:** Established enterprise Git repositories tracking main and development branches under the `WickboldtCapital` organization handle. *(Status: Completed)*
- **Cloud Hosting:** Successfully deployed the live application to Railway with automated GitHub CI/CD webhooks and HTTPS security interceptors. *(Status: Completed)*
- **Authentication Foundation:** Established robust login session states, admin overrides, and role-based routing. *(Status: Completed)*
- **Asset Management:** Resolved Linux/Windows case-sensitivity conflicts for media assets (custom SVG logo injection and favicon). *(Status: Completed)*
""")

st.markdown("## Phase 1: Enterprise Security & Governance")
phase1_data = pd.DataFrame([
    {"Task / Module": "Role-Based Access Control (RBAC)", "Description": "Assign database roles (Admin, Investor, Superintendent) to restrict sidebar navigation and project views.", "Status": "Completed"},
    {"Task / Module": "Audit Logging Ledger", "Description": "Implement a hidden database ledger to track user actions (who, what, when) for critical changes.", "Status": "Completed"},
    {"Task / Module": "Secure Cloud File Storage", "Description": "Integrate Supabase Storage (S3-equivalent) and Google Workspace service accounts for secure document delivery.", "Status": "Completed"}
])
st.table(phase1_data)

st.markdown("## Phase 2: Performance & Scalability")
phase2_data = pd.DataFrame([
    {"Task / Module": "Aggressive Caching", "Description": "Implement Streamlit caching (@st.cache_data) for heavy underwriting computations, proforma models, and document libraries.", "Status": "Completed"},
    {"Task / Module": "Connection Pooling", "Description": "Configure SQLAlchemy connection pooling globally via @st.cache_resource to protect the Supabase PostgreSQL instance from exhaustion.", "Status": "Completed"}
])
st.table(phase2_data)

st.markdown("## Phase 3: Advanced Functions & Automation")
phase3_data = pd.DataFrame([
    {"Task / Module": "Dynamic Scenario Modeling", "Description": "Upgrade Proforma & Underwriting with live sliders (units, rent rolls, equity targets, opex) to instantly recalculate cash flow forecasts.", "Status": "Completed"},
    {"Task / Module": "Automated PDF Generation", "Description": "Integrate Python PDF libraries to compile project data into branded Wickboldt Capital investment packets and proformas.", "Status": "Completed"},
    {"Task / Module": "Triggered Alerts & Milestones", "Description": "Link operational milestones to scheduling completion, unlocking subsequent phases automatically.", "Status": "Completed"}
])
st.table(phase3_data)

st.markdown("## Phase 4: Domain Architecture & DNS Routing")
phase4_data = pd.DataFrame([
    {"Task / Module": "Porkbun DNS Split", "Description": "Route root domain (wickboldtcapital.com) to Netlify, and subdomain (portal.wickboldtcapital.com) to Railway.", "Status": "Completed"}
])
st.table(phase4_data)

st.markdown("## Phase 5: Public Frontend & Marketing Pipeline")
phase5_data = pd.DataFrame([
    {"Task / Module": "Netlify Deployment", "Description": "Host static HTML/CSS landing page on Netlify's global edge network via the wickboldt-capital-frontend repository.", "Status": "Completed"}
])
st.table(phase5_data)

st.markdown("## Phase 6: AI Workflow Integration & Telemetry")
phase6_data = pd.DataFrame([
    {"Task / Module": "LLM API Bridge (Gemini Integration)", "Description": "Connect backend to the native Gemini API for automated PDF bid ingestion, OCR text parsing, and structured JSON extraction.", "Status": "Completed"},
    {"Task / Module": "Automated Proforma Ingestion", "Description": "Build an AI agent capable of reading raw construction bids and automatically populating financial models.", "Status": "Completed"},
    {"Task / Module": "Live Budget Database Hooks", "Description": "Created project_budgets table to permanently store AI-ingested hard costs.", "Status": "Completed"},
    {"Task / Module": "Engineering Modularization", "Description": "Split the massive engineering tool into isolated, trade-specific pages (architecture, hvac, plumbing, electrical).", "Status": "Completed"},
    {"Task / Module": "ACCA HVAC Engine", "Description": "Built an interactive Manual J, S, and D calculator tuned for specific framing and insulation assemblies.", "Status": "Completed"}
])
st.table(phase6_data)

st.markdown("## Phase 7: Foundation Specs & Operations (Current Focus)")
phase7_data = pd.DataFrame([
    {"Task / Module": "Foundation & Concrete Calculator", "Description": "Build algorithms to calculate cubic yardage for slabs, footings, and grade beams. Track site elevations.", "Status": "In Progress"},
    {"Task / Module": "Framing & Structural Takeoffs", "Description": "Calculate lumber takeoffs based on the strict 26-foot max footprint constraint.", "Status": "Pending"},
    {"Task / Module": "MEP Expansion", "Description": "Flesh out the Plumbing and Electrical engineering modules.", "Status": "Pending"},
    {"Task / Module": "Automated Deal Packets", "Description": "Finalize the pdf_ops module to generate branded PDF investment pitch decks.", "Status": "Pending"}
])
st.table(phase7_data)

st.markdown("## Phase 8: Field Execution & Compliance (Upcoming)")
phase8_data = pd.DataFrame([
    {"Task / Module": "Quality Control Checklists", "Description": "Phase-by-phase digital punch lists to ensure framing, insulation, and finish standards are met.", "Status": "Pending"},
    {"Task / Module": "Jobsite Safety Logs", "Description": "OSHA compliance tracking, daily toolbox talk logs, and hazard reporting.", "Status": "Pending"},
    {"Task / Module": "Cash Flow Forecasting", "Description": "Tie project scheduling milestones to the construction draw schedule.", "Status": "Pending"}
])
st.table(phase8_data)

st.divider()

# --- REVISION RECAP & LOG ---
st.markdown("## 📋 Revision Recap & Master Log (August 15, 2026)")
st.markdown("""
* **Engineering Modularization (Phase 6):** Refactored global navigation for a clean, GC-style table of contents and created dedicated `eng_hvac.py` with ACCA spec tracking.
* **Proforma Sync (Phase 6):** Wired the Proforma model to actively pull ingested bids, dynamically replacing estimated hard costs with real-world invoice data for live YOC recalculations.
* **Gemini API Bridge Integration (Phase 6):** Upgraded `ai_ops.py` to natively process contractor bid PDFs and supplier invoices using the Gemini API for direct multimodal financial extraction.
* **Milestone Engine Finalized (Phase 3):** Fully integrated database-backed scheduling and milestone tracking in `pages/scheduling.py`.
""")

if st.session_state.get("role") == "Admin":
    with st.expander("🛠️ Admin Roadmap Controls (Log New Update)"):
        with st.form("roadmap_update_form"):
            new_note = st.text_area("Add Revision Note / Status Update")
            if st.form_submit_button("Record Update"):
                st.success(f"Roadmap note recorded: {new_note}")