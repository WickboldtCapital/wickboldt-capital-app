import streamlit as st
import urllib.parse
import os

# ==========================================
# 🛑 1. CHECK LOGIN STATUS FIRST
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "active_project" not in st.session_state: st.session_state["active_project"] = None
if "email" not in st.session_state: st.session_state["email"] = "steve.wickboldt.jr@gmail.com"
if "role" not in st.session_state: st.session_state["role"] = "Admin"

# OVERRIDE: Force master email to always be Admin
if st.session_state.get("email") == "steve.wickboldt.jr@gmail.com":
    st.session_state["role"] = "Admin"

# ==========================================
# 🛑 2. DYNAMIC PAGE CONFIG (INSTANT UI)
# ==========================================
current_sidebar_state = "expanded" if st.session_state["logged_in"] else "collapsed"

st.set_page_config(
    page_title="Wickboldt Capital - Development Portal",
    page_icon="assets/logo.svg",
    layout="wide",
    initial_sidebar_state=current_sidebar_state, 
)

# ==========================================
# 🚦 3. NUCLEAR CSS LOCK
# ==========================================
if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
            /* 1. Nuke Sidebar & Header completely */
            [data-testid="stSidebar"] { display: none !important; visibility: hidden !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            [data-testid="stHeader"] { display: none !important; }
            
            /* 2. Nuke the top Streamlit Decoration line (the thin grey bar) */
            [data-testid="stDecoration"] { display: none !important; }
            
            /* 3. Nuke the 'Running...' status indicator */
            [data-testid="stStatusWidget"] { display: none !important; }
            
            /* 4. Nuke all Skeleton Loaders */
            .stAppSkeleton, [data-testid="stAppSkeleton"], [data-testid="stSkeleton"] { 
                display: none !important; 
                opacity: 0 !important; 
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🚀 4. HEAVY IMPORTS (BACKGROUND LOADING)
# ==========================================
from core_backend import auto_backup_db, init_db, inject_custom_theme
from db_ops import get_library_state

# Force HTTPS
try:
    host = st.context.headers.get("Host", "")
    if "portal.wickboldtcapital.com" in host:
        proto = st.context.headers.get("X-Forwarded-Proto", "https")
        if proto == "http":
            st.markdown('<meta http-equiv="refresh" content="0;url=https://portal.wickboldtcapital.com/">', unsafe_allow_html=True)
            st.stop()
except Exception:
    pass

# Setup DB
if "system_initialized" not in st.session_state:
    init_db()
    auto_backup_db()
    st.session_state["system_initialized"] = True

# ==========================================
# 🎨 5. CLEAN CSS INJECTIONS & THEME
# ==========================================
st.markdown("""
    <style>
        /* Fix 'View more' button color clash in sidebar */
        [data-testid="stSidebarNavItems"] button {
            color: #ffffff !important;
            background-color: rgba(255,255,255,0.1) !important;
        }
    </style>
""", unsafe_allow_html=True)

inject_custom_theme()

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
# 🚦 MASTER ROUTING ENGINE
# ==========================================
if not st.session_state["logged_in"]:
    pg = st.navigation([st.Page("pages/login.py", title="Sign In", icon="🔒")], position="hidden")
    pg.run()

elif not st.session_state.get("active_project"):
    with st.sidebar:
        st.markdown("### 🏗️ Wickboldt Capital")
        st.caption(f"**User:** `{st.session_state.get('email', '')}`")
        st.caption(f"**Role:** `{st.session_state.get('role', 'Admin').capitalize()}`")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["role"] = "viewer"
            st.rerun()
        st.markdown("---")
        st.warning("⚠️ No active project loaded. Select or create one below to unlock the workspace.")
        
    pg = st.navigation([st.Page("pages/control.py", title="Project Control", icon="📁")])
    pg.run()

else:
    with st.sidebar:
        st.markdown("### 🏗️ Wickboldt Capital")
        st.markdown(f"👤 `{st.session_state.get('email', '')}`")
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
                st.rerun()
        st.markdown("---")

    workspace_pages = {
        "Project Management": [
            st.Page("pages/dashboard.py", title="Executive Dashboard", icon="📊", default=True),
            st.Page("pages/scheduling.py", title="Scheduling & Milestones", icon="🗓️"),
        ],
        "Financials & Underwriting": [
            st.Page("pages/proforma.py", title="Proforma & Underwriting", icon="📈"),
            st.Page("pages/estimation.py", title="Cost Estimation", icon="🧮"),
            st.Page("pages/deal_packet.py", title="Deal Packet Generator", icon="📄"),
            st.Page("pages/bid_intake.py", title="AI Bid Ingestion", icon="🤖"),
            st.Page("pages/forecasting.py", title="Cash Flow Forecasting", icon="🔮"),
            st.Page("pages/capital_stack.py", title="Capital Stack & Debt", icon="🏦"),
        ],
        "Architecture & Specs": [
            st.Page("pages/architecture.py", title="Master Architecture", icon="📐"),
        ],
        "Engineering Disciplines": [
            st.Page("pages/eng_foundation.py", title="Foundation & Concrete", icon="🧱"),
            st.Page("pages/eng_framing.py", title="Structural Framing", icon="🪵"),
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
            st.Page("pages/due_diligence.py", title="Due Diligence", icon="📑"),
            st.Page("pages/marketing.py", title="Marketing Library", icon="📢"),
            st.Page("pages/governance.py", title="Master Company Library", icon="🏢"),
            st.Page("pages/roadmap.py", title="Enterprise Roadmap", icon="🚀"),
            st.Page("pages/user_management.py", title="User Management", icon="🔐"),
            st.Page("pages/settings.py", title="Account Settings", icon="⚙️"),
        ]
    }

    pg = st.navigation(workspace_pages)
    pg.run()