import streamlit as st
import base64
import os
from core_backend import auto_backup_db, init_db, inject_custom_theme
from db_ops import get_library_state

# ==========================================
# 🛑 INITIALIZATION & SECURITY GATES
# ==========================================
st.set_page_config(
    page_title="Wickboldt Capital - Development Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Force HTTPS
try:
    if "portal.wickboldtcapital.com" in st.context.headers.get("Host", ""):
        if st.context.headers.get("X-Forwarded-Proto", "https") == "http":
            st.markdown('<meta http-equiv="refresh" content="0;url=https://portal.wickboldtcapital.com/">', unsafe_allow_html=True)
            st.stop()
except Exception: pass

# Setup DB
if "system_initialized" not in st.session_state:
    init_db()
    auto_backup_db()
    st.session_state["system_initialized"] = True

# Logo Injector
def apply_custom_overrides(svg_path):
    if not os.path.exists(svg_path): return
    try:
        with open(svg_path, "rb") as f:
            encoded_svg = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <script>
                var targetDoc = window.parent.document;
                var link = targetDoc.querySelector("link[rel*='icon']") || targetDoc.createElement('link');
                link.type = 'image/svg+xml';
                link.rel = 'shortcut icon';
                link.href = 'data:image/svg+xml;base64,{encoded_svg}';
                targetDoc.getElementsByTagName('head')[0].appendChild(link);
            </script>""", unsafe_allow_html=True)
    except Exception: pass

apply_custom_overrides("assets/logo.svg")
inject_custom_theme()

# --- AUTH STATE ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "email" not in st.session_state: st.session_state["email"] = "steve.wickboldt.jr@gmail.com"
if "role" not in st.session_state: st.session_state["role"] = "Admin"

# ==========================================
# 🚦 AUTHENTICATION GATING (NO BLINKING)
# ==========================================
if not st.session_state["logged_in"]:
    pg = st.navigation([st.Page("pages/login.py", title="Sign In", icon="🔒")], position="hidden")
    pg.run()
    st.stop() # Force execution to halt here if not logged in

# ==========================================
# 📂 PROJECT LOAD GATE
# ==========================================
if not st.session_state.get("active_project"):
    pg = st.navigation([st.Page("pages/control.py", title="Project Control", icon="📁")], position="hidden")
    pg.run()
    st.stop()

# ==========================================
# 🚀 UNLOCKED WORKSPACE
# ==========================================
with st.sidebar:
    st.markdown("### 🏗️ Wickboldt Capital")
    st.success(f"📁 **Project:** {st.session_state.get('active_project')}")
    if st.button("🔄 Switch Project"):
        st.session_state["active_project"] = None
        st.rerun()

workspace_pages = {
    "Project Management": [
        st.Page("pages/dashboard.py", title="Executive Dashboard", icon="📊", default=True),
        st.Page("pages/scheduling.py", title="Scheduling & Milestones", icon="🗓️"),
    ],
    "Financials": [
        st.Page("pages/proforma.py", title="Proforma & Underwriting", icon="📈"),
        st.Page("pages/deal_packet.py", title="Deal Packet Generator", icon="📄"),
    ]
}
pg = st.navigation(workspace_pages)
pg.run()