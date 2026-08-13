import streamlit as st
import re
import io
import urllib.parse
from db_ops import get_library_state, save_library_state
# Imports the data blocks safely
from governance_data import SEED_TEXT_DB, FOLDER_STRUCTURE

# --- RICH TEXT EDITOR & PDF ENGINE ---
try:
    from streamlit_quill import st_quill
    HAS_QUILL = True
except ImportError:
    HAS_QUILL = False

try:
    from xhtml2pdf import pisa
    HAS_PDF_ENGINE = True
except ImportError:
    HAS_PDF_ENGINE = False

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# --- HEADER STYLING ---
st.markdown("### 🏢 Wickboldt Capital: Master Company Library")
st.markdown("Central repository containing company-wide governance procedures and master specifications.")

if st.session_state.get("role") == "Admin":
    st.success("🔓 **Administrator Mode:** You have full read/write access to modify the database.")
else:
    st.info("🔒 **Viewing Mode:** Read-only access. Admin login required to edit.")

st.write("")

# ==========================================
# 📑 TABBED NAVIGATION (Protects existing features)
# ==========================================
tab_arch, tab_lib = st.tabs(["🏗️ Architecture & AI Thesis", "📚 Master Specification Library"])

with tab_arch:
    st.markdown("""
# 🏗️ Wickboldt Capital: Enterprise Deployment & Architecture Brief

**Version:** 3.5 (Multi-Entity Flat Subdomain Architecture & Governance)  
**Status:** Active Implementation  
**Objective:** Deploy a highly scalable, secure, and performant multi-entity digital presence for Wickboldt Capital, utilizing specialized microservices to route traffic, deliver front-end marketing, compute backend workflows, and isolate operational divisions. 

## Executive Summary: The AI-Leveraged Micro-Enterprise Thesis

**Company Development Thesis:** *To build a highly leveraged, lean real estate development firm capable of competing with massive, multi-employee organizations while operating as a one-man or micro-team entity. This is achieved by developing a proprietary, full-stack application that captures, controls, and drastically accelerates complex development workflows. By integrating emerging AI capabilities directly into the company-owned portal, the firm not only automates daily operations (proformas, scheduling, document control) but critically captures the intellectual property and equity of that AI automation within its own digital asset. This microservices architecture ensures the firm operates with Fortune 500-level speed, security, and infinite scalability at a near-zero baseline cost, turning the proprietary software itself into a core company asset.*

The traditional technical tradeoff for a solo founder has always been between cost and capability. This architecture eliminates that compromise. By decoupling the digital infrastructure into specialized, best-in-class microservices (Netlify for frontend, Railway for backend, Supabase for data), Wickboldt Capital builds an enterprise-grade technology stack maintained on a startup budget. As the real estate portfolio expands, the software acts as the firm's digital workforce, scaling operations without the need to scale headcount.

---

## The Founder's Vision: Steve Wickboldt, Jr.

The technical architecture of Wickboldt Capital is a direct manifestation of its founder's vision. Steve Wickboldt, Jr. brings 30 years of extensive construction experience to the firm—including 22 years operating in the high-stakes, precision-driven offshore oil and gas industry, alongside years of residential construction as a licensed general contractor in Louisiana. 

This deep operational background exposed a critical industry inefficiency: traditional construction and real estate development scale linearly through human headcount, invariably leading to margin erosion, communication silos, and bloated overhead. The vision driving Wickboldt Capital is born from the rigor of offshore engineering, where systems-level thinking, safety, and flawless execution are paramount. 

Wickboldt’s objective is to fuse decades of hard-hat, on-the-ground reality with cutting-edge cloud computing and artificial intelligence. Rather than hiring a massive back-office team to manage master-planned developments—like the 24-lot build-to-rent project at Rogers Moore Parkway or multi-unit high-efficiency portfolios—the firm is building an autonomous "digital backbone." This ensures the company remains fiercely lean and highly profitable, possessing the operational firepower and risk-management capabilities of a massive enterprise while being commanded by a highly leveraged solo operator.

---

## 1. System Architecture Map

The infrastructure relies on a "Subdomain Split," utilizing four platforms to handle specific responsibilities, ensuring zero single points of failure and preparing the environment for future AI integrations.

| Component | Platform | URL Assignment | Primary Responsibility | Estimated Base Cost |
| :--- | :--- | :--- | :--- | :--- |
| **DNS Routing** | Porkbun | `wickboldtcapital.com` | Traffic direction, domain registrar. | ~$10 / year |
| **Marketing Site** | Netlify | `wickboldtcapital.com` | Global CDN delivery of fast, static marketing pages. | $0 / month |
| **Developer Portal** | Railway | `portal.wickboldtcapital.com` | 24/7 serverless computing for the Streamlit/AI app. | ~$5 / month |
| **Database & Storage**| Supabase | *Internal API* | Persistent PostgreSQL database, auth, and storage. | $0 / month |

---

## 2. Phase 1: Data & Persistence (Supabase)

**Phase 1 Executive Summary:** 
*Supabase was chosen to completely decouple the application's data from its codebase by providing a dedicated cloud PostgreSQL database and S3-compatible file storage. This executes the **Company Development Thesis** by creating a highly structured, secure data environment required to train and leverage future AI models. It ensures the firm's proprietary workflows and project data are securely captured and owned as an internal asset, scaling infinitely without requiring a dedicated database administrator.*

*   **Database (PostgreSQL):** Replaces the local SQLite file. Handles all user data, proformas, schedules, and project metadata securely, structuring it perfectly for future AI workflow automation.
*   **Object Storage (S3-Compatible):** Replaces the local assets folder. All PDFs, architectural plans, and site photos are uploaded to Supabase Storage buckets, serving them via CDN.
*   **Authentication (Supabase Auth):** Replaces hardcoded logins with enterprise-grade JWT security, automating user role management without manual oversight.

**Phase 1 Conclusion:**
By anchoring all proprietary data and document assets in Supabase, Wickboldt Capital successfully builds the essential "digital brain" of the company. This layer guarantees that as the firm’s data grows, the solo founder never has to manually manage servers or worry about catastrophic data loss, ensuring the foundation for future AI automation is perfectly structured, fully owned, and inherently scalable.

---

## 3. Phase 2: Application Backend (Streamlit on Railway)

**Phase 2 Executive Summary:** 
*Railway was selected to host the Python backend because its ephemeral Docker containers provide 24/7 serverless computing. This directly advances the **Company Development Thesis** by acting as the engine room for the firm's digital workforce. It provides the professional speed and scalable compute power necessary to run complex financial modeling and custom AI support tools, allowing a single developer to operate a system that typically requires a full IT department, all while charging only for exact CPU usage.*

*   **Deployment Trigger:** Automated CI/CD. Pushing code to GitHub instantly triggers a new container build on Railway, eliminating manual server maintenance.
*   **Environment:** Ephemeral Docker containers. Railway provisions RAM and CPU dynamically based on usage, ensuring the app handles heavy workflow automation without crashing.
*   **Connection:** The app connects to Supabase via secure API keys stored strictly in Environment Variables, keeping the proprietary AI logic and data connections secure.

**Phase 2 Conclusion:**
Deploying on Railway effectively replaces the need for a dedicated IT operations team. It provides a frictionless, zero-maintenance computing environment that allows the solo developer to focus strictly on building workflow-accelerating features rather than fighting with server configurations, keeping the firm lean while operating at maximum velocity.

---

## 4. Phase 3: Public Frontend (Netlify)

**Phase 3 Executive Summary:** 
*Netlify was chosen to host the marketing site on its global edge network. This serves the **Company Development Thesis** by establishing a blazing-fast, enterprise-tier public brand presence at exactly zero cost. By offloading marketing traffic to Netlify, all paid compute resources on Railway are reserved strictly for the heavy lifting of the proprietary backend portal and AI workflow execution.*

*   **Deployment:** Static site generation deployed to Netlify's global edge network for maximum speed.
    *   **Integration Point:** The primary navigation bar includes a secure "Client/Partner Login" button, redirecting users to the proprietary backend portal where the core workflows live.

**Phase 3 Conclusion:**
The Netlify integration ensures that Wickboldt Capital projects a massive, hyper-professional public image that loads instantly for investors and clients worldwide. By physically separating this public marketing layer from the private operational portal, the firm drastically reduces security risks and eliminates unnecessary hosting costs.

---

## 5. Phase 4: DNS Configuration (Porkbun)

**Phase 4 Executive Summary:** 
*Porkbun acts as the foundational traffic controller via the "Subdomain Split." This realizes the **Company Development Thesis** by cleanly decoupling the frontend marketing from the backend operations. It gives the firm the flexibility to scale, upgrade, or swap out underlying AI servers in the future without ever changing the public-facing URLs or causing downtime for partners and investors.*

*   **A-Record:** Points the root domain directly to Netlify's IP addresses.
*   **CNAME Record:** Points the `portal` subdomain to Railway's production URL.
*   **SSL/TLS Security:** Both platforms automatically provision and auto-renew HTTPS certificates, removing manual security maintenance from the lean team's workload.

**Phase 4 Conclusion:**
Porkbun’s routing logic is the glue that makes the microservices architecture invisible to the end user. It ensures that regardless of how radically the underlying AI or database technology evolves over the next decade, the firm retains total control over its digital real estate, projecting a unified, seamless brand experience at all times.

---

## 6. Enterprise Security & AI Scaling Upgrades

**Security & AI Executive Summary:** 
*To safely operate a high-level real estate firm with a reduced headcount, proactive security and automation must be hardcoded into the architecture. This completes the **Company Development Thesis** by guaranteeing data isolation, platform stability, and workflow capture. It ensures the infrastructure operates autonomously, protecting the firm's proprietary digital assets as it scales.*

1.  **Row Level Security (RLS):** Configured inside Supabase. RLS acts as a database-level firewall, physically rejecting any unauthorized request for data.
2.  **Telemetry & Logging:** Proactive error tracking logs crashes and slow queries silently in the background, allowing the solo developer to fix bugs before they impact operations.
3.  **Application Caching & AI Integration:** Extensive use of caching ensures dashboards load instantly. The architecture is explicitly designed to integrate custom LLM (Large Language Model) APIs directly into the Streamlit views, turning the portal into an active participant that accelerates underwriting, scheduling, and document control.

**Security & AI Conclusion:**
By treating security and AI telemetry as automated, built-in features rather than manual chores, the firm completely mitigates the operational risks of running lean. This layer ensures that as the company relies increasingly on AI agents to handle underwriting and scheduling, the system remains bulletproof, compliant, and structurally sound—allowing the founder to aggressively pursue growth with total peace of mind.

---

## 7. Future-Proofing & Multi-Entity Flat Subdomain Architecture

**Subdomain Governance Strategy:**
*As Wickboldt Capital expands its portfolio into distinct operational verticals—spanning Land Acquisition, Real Estate Development (RE), General Construction, Property Management, and Asset Finance—relying on a single monolithic web address creates severe technical debt and routing bottlenecks. To future-proof the digital infrastructure, the firm adopts a strict, hierarchical **flat subdomain taxonomy** anchored directly to the primary parent domain (`wickboldtcapital.com`).*

*   **The Multi-Entity Real Estate Ecosystem:** 
    Real estate operations naturally fracture into specialized functional entities. By designing a flat URL structure ahead of time, each division gains its own secure, isolated digital workspace while maintaining a unified institutional brand, completely avoiding complex and fragile nested subdomains (e.g., avoiding `portal.re.`).
*   **Master Subdomain Expansion Reference Table:**

| Subdomain | Target Platform | Operational Division & Primary Purpose |
| :--- | :--- | :--- |
| `wickboldtcapital.com` | Netlify (Global CDN) | Primary corporate parent landing page and institutional overview. |
| `re.wickboldtcapital.com` | Netlify / Static | Real Estate Development division public presence, portfolio highlights, and site acquisition pitch decks. |
| `portal.wickboldtcapital.com` | Railway (24/7 Compute) | Executive Command Center, proforma financial modeling, master library, and internal workflow execution. |
| `build.wickboldtcapital.com` | Railway / Future | General Contracting operations, field logs, municipal permitting, HVAC load calculations, and subcontractor management. |
| `pm.wickboldtcapital.com` | Railway / Future | Property Management division, lease tracking, maintenance ticketing, and tenant portal operations. |

*   **Strategic Benefits of Pre-Planned Subdomains:**
    *   **Namespace Collision Prevention:** Eliminates URL overlap as new software modules or independent company applications are spun up.
    *   **Isolated Security Perimeters:** Restricts contractor and tenant access to specific subdomains (e.g., limiting subcontractors to `build` without exposing executive proformas on `portal`).
    *   **Modular Microservice Scaling:** Allows individual divisions to upgrade their backend engines on Railway independently without disrupting other business units.

**Subdomain Conclusion:**
This proactive governance protocol ensures that as Wickboldt Capital scales into a multi-company enterprise, its digital architecture expands effortlessly without requiring costly domain restructuring or causing operational downtime.

---

## Document-Wide Conclusion: Realizing the Digital Workforce

The architecture outlined in this brief represents far more than a cost-saving measure for hosting a website; it is the structural blueprint for redefining how a modern real estate development firm operates. By deploying a decoupled, full-stack microservices environment, Wickboldt Capital shifts the burden of scaling from human capital to digital capital. 

Instead of hiring administrative, IT, and underwriting staff to manage growth, the firm invests that equity directly into its proprietary software. The integration of Netlify, Railway, Supabase, and Porkbun creates a highly secure, zero-maintenance "digital workforce" that captures workflows, accelerates execution, and integrates AI capabilities natively. This allows a solo founder to underwrite deals, manage contractors, and project a Fortune 500 image with the agility and low overhead of a micro-enterprise. 

Ultimately, this strategy ensures that Wickboldt Capital is not just building physical real estate assets, but simultaneously compounding the value of its own proprietary technology—creating a highly leveraged, immensely scalable business model primed to disrupt traditional industry operations.
    """)

with tab_lib:
    col1, col2 = st.columns([2, 1])
    search_query = col1.text_input("🔍 Search Master Library...").lower()
    sort_method = col2.selectbox("Sort View By", ["Folder Structure", "Date Modified (Newest)", "Alphabetical (A-Z)"])
    st.markdown("---")

    # ==========================================
    # 🔄 DATABASE AUTO-SYNC
    # ==========================================
    db_library = get_library_state()
    needs_save = False

    # If the DB is missing documents, force-add them!
    for doc_key, doc_content in SEED_TEXT_DB.items():
        if doc_key not in db_library:
            db_library[doc_key] = doc_content
            needs_save = True

    # Save the full documents back to the database if any were added
    if needs_save:
        save_library_state(db_library)

    # ==========================================
    # 🛠️ ADMIN CONTROL PANEL
    # ==========================================
    if st.session_state.get("role") == "Admin":
        with st.expander("🛠️ Admin Document Editor"):
            doc_to_edit = st.selectbox("Select Document to Edit:", list(db_library.keys()))
            if HAS_QUILL:
                new_content = st_quill(value=db_library.get(doc_to_edit, ""), html=True, key=f"quill_{doc_to_edit}")
            else:
                new_content = st.text_area("Document Content:", value=db_library.get(doc_to_edit, ""), height=350)
                
            if st.button("💾 Save Changes to Master Database"):
                db_library[doc_to_edit] = new_content
                save_library_state(db_library)
                st.success(f"Successfully updated {doc_to_edit}!")
                st.rerun()
        st.markdown("---")

    # ==========================================
    # 🛠️ PDF GENERATOR 
    # ==========================================
    def generate_pro_pdf(title, date, content):
        if not HAS_PDF_ENGINE: return None
        html_template = f"""
        <html>
        <head>
            <style>
                @page {{ margin: 2cm; }}
                body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: #333; line-height: 1.5; }}
                h2 {{ color: #002D62; border-bottom: 2px solid #D4AF37; padding-bottom: 5px; }}
                .meta {{ font-size: 10px; color: #666; margin-bottom: 25px; }}
            </style>
        </head>
        <body>
            <h2>WICKBOLDT CAPITAL - MASTER SPECIFICATION</h2>
            <div class="meta"><b>Document:</b> {title}<br><b>Date Published:</b> {date}</div>
            <div class="content">{content}</div>
        </body>
        </html>
        """
        result_bytes = io.BytesIO()
        if pisa.CreatePDF(html_template, dest=result_bytes).err: return None
        return result_bytes.getvalue()

    # ==========================================
    # 🖥️ DYNAMIC RENDER ENGINE (New Tab Link Edition)
    # ==========================================
    def render_document(doc_key):
        content = db_library.get(doc_key, f"Standard specification for {doc_key}.")
        
        # 1. Clean the HTML out of the text
        clean_text = re.sub(r'<[^>]+>', '', content)
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        
        # 2. Extract the TRUE title (first line in your data)
        if lines:
            full_title = lines[0]
            body_lines = [line for line in lines if not line.startswith('Addendum') and not line.startswith('WC-SOP')]
            snippet = body_lines[0] if body_lines else clean_text[:150]
        else:
            full_title = doc_key
            snippet = "No description available."
            
        if len(snippet) > 180: 
            snippet = snippet[:177] + "..."
            
        file_name = f"{re.sub(r'[^a-zA-Z0-9]+', '_', doc_key)}_Spec.pdf"
        
        # Hide if it doesn't match the search query
        if search_query and search_query not in full_title.lower() and search_query not in content.lower():
            return False
            
        # 3. Render the UI cards
        with st.expander(f"📄 {full_title}"):
            st.markdown(f"**Executive Snippet:**\n{snippet}")
            col_dl, col_view = st.columns([1, 1])
            
            # PDF Download Button
            if HAS_PDF_ENGINE:
                pdf_bytes = generate_pro_pdf(doc_key, "2026-08-09", content)
                if pdf_bytes:
                    col_dl.download_button("📥 Download Native PDF", pdf_bytes, file_name=file_name, mime="application/pdf", key=f"dl_{doc_key}")
            else:
                col_dl.warning("⚠️ Run `pip install xhtml2pdf` to enable PDF downloads.")
                
            # Browser Viewer Link Button (Opens in New Tab)
            safe_key = urllib.parse.quote(doc_key)
            link_html = f'''
            <a href="/?view_doc={safe_key}" target="_blank" style="
                display: inline-block;
                padding: 7px 14px;
                background-color: #0047AB; 
                color: #FFFFFF !important;
                border: 1.5px solid #D4AF37;
                text-decoration: none !important;
                border-radius: 4px;
                font-family: sans-serif;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
            ">
                📖 Read Full Document in New Tab ↗
            </a>
            '''
            col_view.markdown(link_html, unsafe_allow_html=True)
            
        return True

    # Draw the Folder Structure
    for top_folder, sub_folders in FOLDER_STRUCTURE.items():
        st.markdown(f"#### {top_folder}")
        for sub_name, doc_keys in sub_folders.items():
            if sub_name:
                st.markdown(f"**{sub_name}**")
            for key in doc_keys:
                render_document(key)
        st.markdown("---")