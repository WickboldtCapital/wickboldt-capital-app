import streamlit as st
import sqlite3
import json
import os
from db_ops import get_user_projects_df, create_project

st.set_page_config(page_title="Project Control Center", layout="wide")

# ==========================================
# 🔒 SECURITY GUARD
# ==========================================
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Access Restricted: Please log in.")
    st.stop()

# --- ENTERPRISE PERSISTENT STORAGE ROUTING ---
if os.path.exists("/app/data"):
    DB_FILE = "/app/data/wickboldt_projects.db"
else:
    DB_FILE = "wickboldt_projects.db"

user_email = st.session_state.get("email", st.session_state.get("username", "Unknown"))
role = st.session_state.get("role", "Viewer")

def init_local_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS projects (project_name TEXT PRIMARY KEY, project_data TEXT)")
    conn.commit()
    conn.close()

init_local_db()

# --- FETCH FROM ENTERPRISE POSTGRES CLOUD ---
def get_authorized_projects():
    # Uses db_ops.py to fetch the true source of truth from the cloud database
    df = get_user_projects_df(user_email, role)
    if not df.empty and 'project_name' in df.columns:
        return df['project_name'].tolist()
    return []

st.title("🎛️ Project Control Center")
st.markdown(f"**Logged in as:** `{user_email}` (Role: `{role}`)")
st.divider()

col1, col2 = st.columns(2, gap="large")

# --- SELECT ACTIVE PROJECT ---
with col1:
    st.subheader("Select Active Project")
    authorized_projects = get_authorized_projects()
    
    if authorized_projects:
        selected_project = st.selectbox("Your Authorized Developments:", authorized_projects)
        if st.button("🚀 Load Project Workspace", type="primary"):
            # Sync to local SQLite to ensure Capital Stack/Due Diligence have a save slot
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT OR IGNORE INTO projects (project_name, project_data) VALUES (?, ?)", (selected_project, "{}"))
            conn.commit()
            conn.close()

            st.session_state["active_project"] = selected_project
            st.success(f"Workspace loaded for: **{selected_project}**. You may now navigate the sidebar modules.")
            st.rerun() 
    else:
        st.warning("⚠️ You currently have no authorized projects assigned to your account. Create one below.")

# --- CREATE NEW PROJECT ---
with col2:
    if role and role.lower() in ["admin", "manager"]:
        st.subheader("Initialize New Development")
        with st.form("new_project_form", clear_on_submit=True):
            new_project_name = st.text_input("Project / Subdivision Name")
            if st.form_submit_button("🏗️ Create Project"):
                if new_project_name:
                    # 1. Save to Cloud Postgres (for Dashboard & Global Access)
                    success, msg = create_project(new_project_name, "Active", "", user_email)
                    
                    if success:
                        # 2. Sync to Local SQLite (for local JSON state)
                        conn = sqlite3.connect(DB_FILE)
                        conn.execute("INSERT OR IGNORE INTO projects (project_name, project_data) VALUES (?, ?)", (new_project_name, "{}"))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Project '{new_project_name}' successfully created in the Enterprise Cloud!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create project: {msg}")
                else:
                    st.error("Project name cannot be empty.")
    else:
        st.info("💡 Project creation is restricted to Administrators and Managers.")

st.divider()
if st.session_state.get("active_project"):
    st.success(f"✅ **Currently Active Workspace:** `{st.session_state['active_project']}`")