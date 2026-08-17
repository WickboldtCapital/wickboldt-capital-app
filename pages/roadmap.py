import streamlit as st

st.set_page_config(page_title="Enterprise Roadmap", layout="wide")

# --- SECURITY GUARD ---
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Access Restricted: Please log in.")
    st.stop()

st.title("🚀 Enterprise Development Roadmap & Master Log")
st.markdown("### WickboldtApp Internal Development Tracking")
st.caption("Live tracking of architectural updates, feature deployments, and upcoming development phases.")
st.divider()

st.markdown("""
### 📋 Summary of Changes (Current Revision: Rev 6.0)
*August 2026*

* **Complete MEP Engineering Suite:** Deployed enterprise-grade Mechanical, Electrical, and Plumbing modules. Includes ACCA Manual J/S/D HVAC load calculations, IPC WSFU/DFU plumbing sizing with gas loads, and NEC Article 220 electrical service load modeling.
* **Structural & Foundation Engineering:** Swapped ICF logic for a dynamic monolithic/stem-wall concrete yardage calculator with FEMA BFE tracking. Deployed comprehensive framing takeoffs including 24" O.C. Advanced Framing (OVE) and hybrid SIPs panel configurations.
* **Proforma ERP Integration:** Hard-wired the new engineering modules directly into the Proforma. The financial engine now intercepts granular MEP and Framing budgets, dynamically replacing generic baselines within the Variance Report.
* **Dual-Audience Submittals:** Upgraded all engineering modules to automatically generate both municipal-ready Code Compliance submittals (for inspectors) and granular Scope of Work checklists (for subcontractor bidding).

---

### 🗺️ Enterprise Roadmap

#### ✅ Phase 1: Core Architecture & Foundation (Completed)
- [x] Initial Streamlit App Scaffold & Cloud Deployment.
- [x] Secure multi-tenant login system with role-based access.
- [x] Robust internal SQLite database with automated backup protocols.
- [x] Dynamic Sidebar Navigation, Auth-Gating, and Session State management.
- [x] UI/UX Flash suppression on login screen.

#### ✅ Phase 2: Financials & Investment (Completed)
- [x] Executive Dashboard with high-level portfolio metrics.
- [x] Real-time Proforma & Underwriting module with Budget vs. Actuals variance.
- [x] Automated, pure-Python PDF Deal Packet Generator with live Capital Stack logic.
- [x] User Management Module (`pages/user_management.py`) & Audit Logs.
- [x] Cash Flow Forecasting & Lender Draw Schedules (`pages/forecasting.py`).
- [x] AI Bid Ingestion and interactive data parsing (`pages/bid_intake.py`).

#### 🏗️ Phase 3: Engineering & Operations (Active)
- [x] Civil & Foundation Concrete Engineering (`pages/eng_foundation.py`).
- [x] Structural Framing & SIPs Configuration (`pages/eng_framing.py`).
- [x] ACCA Manual J/S/D HVAC Calculations (`pages/eng_hvac.py`).
- [x] IPC Plumbing, Water & Gas Load Engineering (`pages/eng_plumbing.py`).
- [x] NEC Article 220 Electrical Panel Sizing (`pages/eng_electrical.py`).
- [ ] Master Architecture & Specs (`pages/architecture.py`).
- [ ] Quality Control & Phase Inspections (`pages/quality.py`).
- [ ] Jobsite Safety & OSHA Compliance (`pages/safety.py`).

#### 🏢 Phase 4: Master Company Library & Governance (Upcoming)
- [ ] Subcontractor CRM & Bid Management (`pages/subs.py`).
- [ ] Secure Document Vault for Deeds, Loans, and Permits.
- [ ] Standard Operating Procedures (SOP) & LMS tracking.
- [ ] Marketing & Due Diligence asset management.

---

### 📜 Master Update Log

* **Rev 6.0 (Aug 2026):** Deployed complete MEP suite (HVAC, Plumbing, Electrical), Structural/Foundation upgrades, and live Proforma ERP synchronization.
* **Rev 5.0 (Aug 2026):** User Management, Security Logs, AI Bid Ingestion, Live Proforma Variance, Cash Flow Forecasting, UI Flash Suppression.
* **Rev 4.0 (Aug 2026):** Strict Auth-gating, FPDF2 Deal Packets, Capital Stack calculations, Full Sidebar restoration.
* **Rev 3.0 (Aug 2026):** Multi-tenant DB integration, session state architecture overhaul.
* **Rev 2.0 (Aug 2026):** Executive dashboard deployment, base estimating tools.
* **Rev 1.0 (Jul 2026):** Project initiation, repository creation, brand asset injection.

""")

st.divider()
st.info("🔗 **Workspace Link:** Access this document live at `https://portal.wickboldtcapital.com/roadmap`")