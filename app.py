import streamlit as st
import urllib.parse
import base64
from core_backend import auto_backup_db, init_db, get_logo_html, inject_custom_theme
from db_ops import get_library_state  # <-- Pulled from db_ops instead of core_backend

# --- CONFIG & SETUP ---
st.set_page_config(
    page_title="Wickboldt Capital - Development Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- BULLETPROOF SVG FAVICON INJECTION ---
def set_svg_favicon(svg_path):
    try:
        with open(svg_path, "rb") as f:
            encoded_svg = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
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

# IMPORTANT: Make sure this exactly matches the file name in your assets folder!
set_svg_favicon("assets/logo.svg")

# Apply custom Wickboldt styling
inject_custom_theme()

# Run Database Initialization & Backups ONLY ONCE per session to eliminate lag
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
if "role" not in st.session_state:
    st.session_state["role"] = "viewer"

# ==========================================
# 📄 DEDICATED DOCUMENT VIEWER ROUTE
# ==========================================
# If a user clicked a document link in another tab, intercept it here.
if "view_doc" in st.query_params:
    # Get the title from the URL
    doc_title = st.query_params["view_doc"]
    library_data = get_library_state()
    
    if doc_title in library_data:
        st.title(doc_title)
        st.divider()
        # Render the full, unredacted text
        st.markdown(library_data[doc_title])
    else:
        st.error(f"Document '{doc_title}' not found in the library.")
    
    # Halt the rest of the app from loading (hides sidebar and routing)
    st.stop()


# ==========================================
# 🚦 DYNAMIC ROUTING (The Traffic Cop)
# ==========================================

# State 0: Not Logged In & In Home Mode -> Show Public Front Page
if not st.session_state["logged_in"] and st.session_state["nav_mode"] == "home":
    pg = st.navigation([st.Page("views/frontpage.py", title="Home", icon="🏠")], position="hidden")
    pg.run()

# State 1: Not Logged In & In Login Mode -> Show Login Screen
elif not st.session_state["logged_in"] and st.session_state["nav_mode"] == "login":
    with st.sidebar:
        if st.button("← Return to Home", use_container_width=True):
            st.session_state["nav_mode"] = "home"
            st.rerun()
            
    pg = st.navigation([st.Page("views/login.py", title="Sign In", icon="🔒")], position="hidden")
    pg.run()

# State 2: Logged In, but No Active Project -> Show Control Screen
elif not st.session_state.get("active_project"):
    with st.sidebar:
        st.markdown(get_logo_html(), unsafe_allow_html=True)
        st.markdown(f"**Logged in as:** `{st.session_state.get('email', 'User')}`")
        st.markdown(f"**Role:** `{st.session_state.get('role', 'Viewer').capitalize()}`")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["role"] = "viewer"
            st.session_state["nav_mode"] = "home"
            st.rerun()
        st.markdown("---")
        st.warning("⚠️ No active project loaded. Select one to unlock the portfolio modules.")
        
    pg = st.navigation([st.Page("views/control.py", title="Project Control", icon="📁")])
    pg.run()

# State 3: Fully Logged In & Project Active -> Unlock the App
else:
    with st.sidebar:
        st.markdown(get_logo_html(), unsafe_allow_html=True)
        st.markdown(f"**Logged in as:** `{st.session_state.get('email', 'User')}`")
        st.markdown(f"**Role:** `{st.session_state.get('role', 'Viewer').capitalize()}`")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["active_project"] = None
            st.session_state["role"] = "viewer"
            st.session_state["nav_mode"] = "home"
            st.rerun()
        st.markdown("---")
        st.success(f"📁 **Active Project:**\n{st.session_state['active_project']}")
        if st.button("🔄 Close Project & Return Home", use_container_width=True):
            st.session_state["active_project"] = None
            st.rerun()
        st.markdown("---")

    # --- ROLE-BASED ACCESS CONTROL (RBAC) ---
    user_role = st.session_state.get("role", "viewer").lower()

    # Define standard pages everyone sees
    pages = {
        "Project Management": [
            st.Page("views/dashboard.py", title="Executive Dashboard", icon="📊", default=True),
            st.Page("views/scheduling.py", title="Scheduling & Milestones", icon="🗓️"),
        ],
        "Financials & Underwriting": [
            st.Page("views/proforma.py", title="Proforma & Underwriting", icon="📈"),
        ]
    }

    # Add Admin-only pages
    if user_role == "admin":
        pages["Project Management"].append(st.Page("views/control.py", title="Project Control", icon="📁"))
        pages["Financials & Underwriting"].append(st.Page("views/estimation.py", title="Cost Estimation", icon="🧮"))
        pages["Financials & Underwriting"].append(st.Page("views/forecasting.py", title="Cash Flow Forecasting", icon="🔮"))
        pages["Financials & Underwriting"].append(st.Page("views/capitaldebtstack.py", title="Capital Stack & Debt", icon="🏦"))
        
        pages["Operations & Execution"] = [
            st.Page("views/engineering.py", title="Engineering Specs", icon="🏗️"),
            st.Page("views/quality.py", title="Quality Control", icon="✅"),
            st.Page("views/safety.py", title="Jobsite Safety", icon="🦺"),
        ]
        
        pages["Business & Governance"] = [
            st.Page("views/diligence.py", title="Due Diligence", icon="📑"),
            st.Page("views/marketing.py", title="Marketing Library", icon="📢"),
            st.Page("views/governance.py", title="Master Company Library", icon="🏢"),
            st.Page("views/user_management.py", title="User Management", icon="🔐"),
            st.Page("views/settings.py", title="Account Settings", icon="⚙️"),
        ]

    pg = st.navigation(pages)
    pg.run()