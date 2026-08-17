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
### 📋 Summary of Changes (Current Revision: Rev 11.0)
*August 2026*

* **Multi-Tenant Security Architecture:** Integrated strict project-level data isolation across all modules. Authorized users can now only access projects explicitly mapped to their profile via the Project Control Center and User Management panel.
* **Master Document Vault (`pages/vault.py`):** Deployed a centralized, physical file management system. Securely upload and download PDF blueprints, site drawings, municipal permits, and legal deeds isolated by project.
* **Subcontractor CRM & Procurement (`pages/subs.py`):** Fully operationalized trade roster, Bid Requests (RFPs), a Quote Document Vault, and **live Bid Leveling against engineered targets** (automatically pulling MEP, Framing, and Architecture budgets from the database).
* **Enterprise Proforma 3-Tier Waterfall:** Upgraded the financial engine to prioritize Awarded Subcontractor Contracts over engineered estimates and generic baselines, dynamically tagging line items in the Variance Report.
* **SOP & Training LMS (`pages/training.py`):** Integrated a robust 5-level curriculum builder (Categories ➡️ Chapters ➡️ Modules ➡️ Topics ➡️ Sub-Topics) with rich text `st_quill` editing, media attachments, and multi-tenant isolated Jobsite Certification logs.

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

#### ✅ Phase 3: Engineering & Field Operations (Completed)
- [x] Civil & Foundation Concrete Engineering (`pages/eng_foundation.py`).
- [x] Structural Framing & SIPs Configuration (`pages/eng_framing.py`).
- [x] ACCA Manual J/S/D HVAC Calculations (`pages/eng_hvac.py`).
- [x] IPC Plumbing, Water & Gas Load Engineering (`pages/eng_plumbing.py`).
- [x] NEC Article 220 Electrical Panel Sizing (`pages/eng_electrical.py`).
- [x] Quality Control & Phase Inspections (`pages/quality.py`).
- [x] Jobsite Safety & OSHA Compliance (`pages/safety.py`).

#### ✅ Phase 4: Master Company Library & Governance (Completed)
- [x] Subcontractor CRM, RFPs, & Bid Leveling (`pages/subs.py`).
- [x] Master Document Vault with physical file handling (`pages/vault.py`).
- [x] Standard Operating Procedures & Enterprise LMS (`pages/training.py`).
- [x] Multi-Tenant Project Isolation & Role-Based Access Control.

#### 🏗️ Phase 5: Future Enhancements (Active)
- [ ] Executive Portfolio-Level Aggregation Dashboard (`pages/dashboard.py`).

---

### 📜 Master Update Log

* **Rev 11.0 (Aug 2026):** Completed Phase 10/Phase 4 Enterprise Governance. Deployed multi-tenant security architecture, Master Document Vault with disk uploads, Subcontractor procurement against engineered targets, and the Enterprise LMS training suite.
* **Rev 10.0 (Aug 2026):** Officially completed and deployed Phase 9 (Scheduling & Milestones module with live database hooks).
* **Rev 6.0 (Aug 2026):** Deployed complete MEP suite (HVAC, Plumbing, Electrical), Structural/Foundation upgrades, and live Proforma ERP synchronization.
* **Rev 5.0 (Aug 2026):** User Management, Security Logs, AI Bid Ingestion, Live Proforma Variance, Cash Flow Forecasting, UI Flash Suppression.
* **Rev 4.0 (Aug 2026):** Strict Auth-gating, FPDF2 Deal Packets, Capital Stack calculations, Full Sidebar restoration.
* **Rev 3.0 (Aug 2026):** Multi-tenant DB integration, session state architecture overhaul.
* **Rev 2.0 (Aug 2026):** Executive dashboard deployment, base estimating tools.
* **Rev 1.0 (Jul 2026):** Project initiation, repository creation, brand asset injection.

""")

st.divider()
st.info("🔗 **Workspace Link:** Access this document live at `https://portal.wickboldtcapital.com/roadmap`")