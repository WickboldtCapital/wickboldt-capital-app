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
### 📋 Summary of Changes (Current Revision: Rev 4.0)
*August 2026*

* **Authentication & Routing:** Enforced strict, direct-to-login routing, completely eliminating UI "blinking" and separating public marketing from the secure portal.
* **PDF Engine Overhaul:** Replaced `weasyprint` with `fpdf2` (pure Python) to bypass Linux dependency crashes on cloud deployment.
* **Deal Packet Enhancements:** Injected a live Capital Stack & Loan-to-Value (LTV) calculator directly into the dynamic PDF generation.
* **Enterprise Menu Restoration:** Restored the full suite of operational modules (Engineering, Architecture, Operations, Business & Governance) to the secure sidebar.
* **Database Resilience:** Added automated SQLite cold-start catches to prevent app crashes when loading new or empty modules.

---

### 🗺️ Enterprise Roadmap

#### ✅ Phase 1: Core Architecture & Foundation (Completed)
- [x] Initial Streamlit App Scaffold & Cloud Deployment.
- [x] Secure multi-tenant login system with role-based access (Admin vs. standard user).
- [x] Robust internal SQLite database with automated backup protocols.
- [x] Dynamic Sidebar Navigation, Auth-Gating, and Session State management.

#### 🏗️ Phase 2: Financials & Investment (Active)
- [x] Executive Dashboard with high-level portfolio metrics.
- [x] Real-time Proforma & Underwriting module.
- [x] Automated, pure-Python PDF Deal Packet Generator.
- [ ] **NEXT UP:** User Management Module (`pages/user_management.py`) to invite crew and lenders.
- [ ] Cash Flow Forecasting (`pages/forecasting.py`).
- [ ] AI Bid Ingestion and OCR parsing (`pages/bid_intake.py`).

#### 📐 Phase 3: Engineering & Operations (Upcoming)
- [ ] ACCA Manual J/S/D HVAC Calculations Integration.
- [ ] Structural Framing & Foundation Concrete volume estimators.
- [ ] Safety & Quality Control logging (Toolbox Talks, Audits).
- [ ] Master Architecture & Specs (`pages/architecture.py`).

#### 🏢 Phase 4: Master Company Library & Governance (Planned)
- [ ] Secure Document Vault for Deeds, Loans, and Permits.
- [ ] Standard Operating Procedures (SOP) & LMS tracking.
- [ ] Marketing & Due Diligence asset management.

---

### 📜 Master Update Log

* **Rev 4.0 (Aug 2026):** Auth-gating, FPDF2 Deal Packets, Capital Stack calculations, UI blink fix, Full Sidebar restoration.
* **Rev 3.0 (Aug 2026):** Multi-tenant DB integration, session state architecture overhaul.
* **Rev 2.0 (Aug 2026):** Executive dashboard deployment, base estimating tools.
* **Rev 1.0 (Jul 2026):** Project initiation, repository creation, brand asset injection.

""")

st.divider()
st.info("🔗 **Workspace Link:** Access this document live at `https://portal.wickboldtcapital.com/roadmap`")