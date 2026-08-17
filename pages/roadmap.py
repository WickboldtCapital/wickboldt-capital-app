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
### 📋 Summary of Changes (Current Revision: Rev 5.0)
*August 2026*

* **User Management & Security:** Deployed the admin-only User Management console with active role assignment (Admin, Manager, Investor, Viewer) and a live Security Audit Log.
* **AI Bid Ingestion Pipeline:** Built the `bid_intake` module for multi-line extraction, interactive verification, and bulk database commits of real-world contractor costs.
* **Live Variance Reporting:** Rewired the Proforma to pull AI-ingested actuals against baseline estimates, creating an automated Hard Cost Variance tracker and dynamic Yield on Cost (YOC) calculation.
* **Cash Flow Forecasting:** Launched the interactive draw schedule generator, enabling precise capital allocation mapping and S-Curve visualization for lender presentations.
* **UI Flash Eradication:** Applied conditional `initial_sidebar_state` page configurations and CSS delay tactics to completely mask the Streamlit sidebar React flash on the authentication screen.

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
- [ ] ACCA Manual J/S/D HVAC Calculations Integration.
- [ ] Structural Framing & Foundation Concrete volume estimators.
- [ ] Safety & Quality Control logging (Toolbox Talks, Audits).
- [ ] Master Architecture & Specs (`pages/architecture.py`).

#### 🏢 Phase 4: Master Company Library & Governance (Upcoming)
- [ ] Secure Document Vault for Deeds, Loans, and Permits.
- [ ] Standard Operating Procedures (SOP) & LMS tracking.
- [ ] Marketing & Due Diligence asset management.

---

### 📜 Master Update Log

* **Rev 5.0 (Aug 2026):** User Management, Security Logs, AI Bid Ingestion, Live Proforma Variance, Cash Flow Forecasting, UI Flash Suppression.
* **Rev 4.0 (Aug 2026):** Strict Auth-gating, FPDF2 Deal Packets, Capital Stack calculations, Full Sidebar restoration.
* **Rev 3.0 (Aug 2026):** Multi-tenant DB integration, session state architecture overhaul.
* **Rev 2.0 (Aug 2026):** Executive dashboard deployment, base estimating tools.
* **Rev 1.0 (Jul 2026):** Project initiation, repository creation, brand asset injection.

""")

st.divider()
st.info("🔗 **Workspace Link:** Access this document live at `https://portal.wickboldtcapital.com/roadmap`")
