import streamlit as st
import urllib.parse
import base64
from core_backend import auto_backup_db, init_db, inject_custom_theme
from db_ops import get_library_state  

# ==========================================
# 🔒 FORCE HTTPS SECURITY REDIRECT
# ==========================================
try:
    host = st.context.headers.get("Host", "")
    if "portal.wickboldtcapital.com" in host:
        proto = st.context.headers.get("X-Forwarded-Proto", "https")
        if proto == "http":
            st.markdown(
                '<meta http-equiv="refresh" content="0;url=https://portal.wickboldtcapital.com/">',
                unsafe_allow_html=True
            )
            st.stop()
except Exception:
    pass

# --- CONFIG & SETUP ---
st.set_page_config(
    page_title="Wickboldt Capital - Development Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- BULLETPROOF SVG FAVICON & SIDEBAR CSS INJECTION ---
def apply_custom_overrides(svg_path):
    try:
        with open(svg_path, "rb") as f:
            encoded_svg = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
                /* Fix 'View more' button color clash in sidebar */
                [data-testid="stSidebarNavItems"] button {{
                    color: #ffffff !important;
                    background-color: rgba(255,255,255,0.1) !important;
                }}
            </style>
            <script>
                var targetDoc = window.parent.document;
                var link = targetDoc.querySelector("link[rel*='icon']") || targetDoc.createElement('link');
                link.type = 'image/svg+xml';
                link.rel = 'shortcut icon';
                link.href = 'data:image/svg+xml;base64,{encoded_svg}';
                targetDoc.getElementsByTagName('head')[0].appendChild(link);
            </script>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        pass

apply_custom_overrides("assets/logo.svg")
inject_custom_theme()

if "system_initialized" not in st.session_state:
    init_db()
    auto_backup_db()
    st.session_state["system_initialized"] = True

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "active_project" not in st.session_state:
    st.session_state["active_project"] = None
if "nav_mode" not in st.session_state:
    st.session_state["nav_mode"] = "home"
if "email" not in st.session_state:
    st.session_state["email"] = "steve.wickboldt.jr@gmail.com"

# OVERRIDE: Force master email to always be Admin
if st.session_state.get("email") == "steve.wickboldt.jr@gmail.com":
    st.session_state["role"] = "Admin"
elif "role" not in st.session_state:
    st.session_state["role"] = "Admin"

# ==========================================
# 📄 DEDICATED DOCUMENT VIEWER ROUTE
# ==========================================
if "view_doc" in st.query_params:
    doc_title = st.query_params["view_doc"]
    library_data = get_library_state()
    
    if doc_title in library_data:
        st.title(doc_title)
        st.divider()
        st.markdown(library_data[doc_title])
    else:
        st.error(f"Document '{doc_title}' not found in the library.")
    st.stop()

# ==========================================
# 🚦 DYNAMIC ROUTING
# ==========================================
if not st.session_state["logged_in"] and st.session_state["nav_mode"] == "home":
    pg = st.navigation([st.Page("pages/frontpage.py", title="Home", icon="🏠")], position="hidden")
    pg.run()

elif not st.session_state["logged_in"] and st.session_state["nav_mode"] == "login":
    with st.sidebar:
        if st.button("← Return to Home", use_container_width=True):
            st.session_state["nav_mode"] = "home"
            st.rerun()
    pg = st.navigation([st.Page("pages/login.py", title="Sign In", icon="🔒")], position="hidden")
    pg.run()

elif not st.session_state.get("active_project"):
    with st.sidebar:
        st.markdown("### 🏗️ Wickboldt Capital")
        st.caption(f"**User:** `{st.session_state.get('email', 'steve.wickboldt.jr@gmail.com')}`")
        st.caption(f"**Role:** `{st.session_state.get('role', 'Admin').capitalize()}`")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["role"] = "viewer"
            st.session_state["nav_mode"] = "home"
            st.rerun()
        st.markdown("---")
        st.warning("⚠️ No active project loaded. Select or create one below to unlock the workspace.")
        
    pg = st.navigation([st.Page("pages/control.py", title="Project Control", icon="📁")])
    pg.run()

else:
    # --- ENTERPRISE SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🏗️ Wickboldt Capital")
        st.markdown(f"👤 `{st.session_state.get('email', 'steve.wickboldt.jr@gmail.com')}`")
        st.caption(f"🛡️ Role: {st.session_state.get('role', 'Admin').capitalize()}")
        st.markdown("---")
        st.success(f"📁 **Active Project:**\n{st.session_state.get('active_project', 'None')}")
        
        col_sw, col_out = st.columns(2)
        with col_sw:
            if st.button("🔄 Switch", use_container_width=True, help="Switch Project"):
                st.session_state["active_project"] = None
                st.rerun()
        with col_out:
            if st.button("🚪 Out", use_container_width=True, help="Sign Out"):
                st.session_state["logged_in"] = False
                st.session_state["active_project"] = None
                st.session_state["role"] = "viewer"
                st.session_state["nav_mode"] = "home"
                st.rerun()
        st.markdown("---")

    # --- UNLOCKED ENTERPRISE WORKSPACE NAVIGATION (Grouped) ---
    workspace_pages = {
        "Project Management": [
            st.Page("pages/dashboard.py", title="Executive Dashboard", icon="📊", default=True),
            st.Page("pages/scheduling.py", title="Scheduling & Milestones", icon="🗓️"),
        ],
        "Financials & Underwriting": [
            st.Page("pages/proforma.py", title="Proforma & Underwriting", icon="📈"),
            st.Page("pages/estimation.py", title="Cost Estimation", icon="🧮"),
            st.Page("pages/bid_intake.py", title="AI Bid Ingestion", icon="🤖"),
            st.Page("pages/forecasting.py", title="Cash Flow Forecasting", icon="🔮"),
            st.Page("pages/capitaldebtstack.py", title="Capital Stack & Debt", icon="🏦"),
        ],
        "Architecture & Specs": [
            st.Page("pages/architecture.py", title="Master Architecture", icon="📐"),
        ],
        "Engineering Disciplines": [
            st.Page("pages/eng_foundation.py", title="Foundation & Concrete", icon="🧱"),
            st.Page("pages/eng_hvac.py", title="HVAC (ACCA)", icon="❄️"),
            st.Page("pages/eng_plumbing.py", title="Plumbing & Water", icon="🚰"),
            st.Page("pages/eng_electrical.py", title="Electrical & Power", icon="⚡"),
        ],
        "Operations & Execution": [
            st.Page("pages/quality.py", title="Quality Control", icon="✅"),
            st.Page("pages/safety.py", title="Jobsite Safety", icon="🦺"),
            st.Page("pages/training.py", title="Training & SOPs", icon="📚"), 
        ],
        "Business & Governance": [
            st.Page("pages/documents.py", title="Secure Document Library", icon="🔒"),
            st.Page("pages/diligence.py", title="Due Diligence", icon="📑"),
            st.Page("pages/marketing.py", title="Marketing Library", icon="📢"),
            st.Page("pages/governance.py", title="Master Company Library", icon="🏢"),
            st.Page("pages/roadmap.py", title="Enterprise Roadmap", icon="🚀"),
            st.Page("pages/user_management.py", title="User Management", icon="🔐"),
            st.Page("pages/settings.py", title="Account Settings", icon="⚙️"),
        ]
    }

    pg = st.navigation(workspace_pages)
    pg.run()