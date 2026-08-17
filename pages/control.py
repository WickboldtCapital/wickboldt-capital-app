import streamlit as st
import sqlite3
import json

st.set_page_config(page_title="Project Control Center", layout="wide")

# ==========================================
# 🔒 SECURITY GUARD
# ==========================================
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Access Restricted: Please log in.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# Match your session state keys (defaults to checking email first, then username)
user_email = st.session_state.get("email", st.session_state.get("username", "Unknown"))
role = st.session_state.get("role", "Viewer")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS projects (project_name TEXT PRIMARY KEY, project_data TEXT)")
    conn.commit()
    conn.close()

def get_authorized_projects():
    conn = sqlite3.connect(DB_FILE)
    
    # 1. Get ALL projects
    try:
        cursor = conn.execute("SELECT project_name FROM projects")
        all_projects = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        all_projects = []
    
    # 2. Get User's authorized projects (Case-Insensitive Fix applied here)
    if role and role.lower() == "admin":
        conn.close()
        return all_projects
    else:
        try:
            # Safely query the assigned_projects column for this specific user
            cursor = conn.execute("SELECT assigned_projects FROM users WHERE email=?", (user_email,))
            row = cursor.fetchone()
            if not row:
                cursor = conn.execute("SELECT assigned_projects FROM users WHERE username=?", (user_email,))
                row = cursor.fetchone()
                
            conn.close()
            
            if row and row[0]:
                allowed = json.loads(row[0])
                # Return the intersection: ensures the project actually exists in the DB
                return [p for p in all_projects if p in allowed]
        except Exception:
            conn.close()
            return []
        return []

init_db()

st.title("🎛️ Project Control Center")
st.markdown(f"**Logged in as:** `{user_email}` (Role: `{role}`)")
st.divider()

col1, col2 = st.columns(2, gap="large")

# --- SELECT ACTIVE PROJECT (ISOLATED) ---
with col1:
    st.subheader("Select Active Project")
    authorized_projects = get_authorized_projects()
    
    if authorized_projects:
        selected_project = st.selectbox("Your Authorized Developments:", authorized_projects)
        if st.button("🚀 Load Project Workspace", type="primary"):
            st.session_state["active_project"] = selected_project
            st.success(f"Workspace loaded for: **{selected_project}**. You may now navigate the sidebar modules.")
            # FORCE APP REFRESH TO REDRAW SIDEBAR
            st.rerun() 
    else:
        st.warning("⚠️ You currently have no authorized projects assigned to your account. Please contact an Administrator.")

# --- CREATE NEW PROJECT (ADMIN/MANAGER ONLY) ---
with col2:
    # Case-Insensitive Check for project creation
    if role and role.lower() in ["admin", "manager"]:
        st.subheader("Initialize New Development")
        with st.form("new_project_form", clear_on_submit=True):
            new_project_name = st.text_input("Project / Subdivision Name")
            if st.form_submit_button("🏗️ Create Project"):
                if new_project_name:
                    conn = sqlite3.connect(DB_FILE)
                    try:
                        conn.execute("INSERT INTO projects (project_name, project_data) VALUES (?, ?)", (new_project_name, "{}"))
                        conn.commit()
                        st.success(f"Project '{new_project_name}' successfully created!")
                        
                        # If a Manager creates a project, automatically grant them access to it
                        if role and role.lower() == "manager":
                            try:
                                cursor = conn.execute("SELECT assigned_projects FROM users WHERE email=?", (user_email,))
                                row = cursor.fetchone()
                                if not row:
                                    cursor = conn.execute("SELECT assigned_projects FROM users WHERE username=?", (user_email,))
                                    row = cursor.fetchone()
                                
                                allowed = json.loads(row[0]) if row and row[0] else []
                                if new_project_name not in allowed:
                                    allowed.append(new_project_name)
                                    
                                try:
                                    conn.execute("UPDATE users SET assigned_projects=? WHERE email=?", (json.dumps(allowed), user_email))
                                except sqlite3.OperationalError:
                                    conn.execute("UPDATE users SET assigned_projects=? WHERE username=?", (json.dumps(allowed), user_email))
                                conn.commit()
                            except Exception:
                                pass # Admin can manually fix if mapping fails
                        
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Project '{new_project_name}' already exists.")
                    finally:
                        conn.close()
                else:
                    st.error("Project name cannot be empty.")
    else:
        st.info("💡 Project creation is restricted to Administrators and Managers. You have Viewer/Investor access only.")

st.divider()
if st.session_state.get("active_project"):
    st.success(f"✅ **Currently Active Workspace:** `{st.session_state['active_project']}`")