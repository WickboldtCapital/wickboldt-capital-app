import streamlit as st
import pandas as pd
from db_ops import get_all_projects_df, create_project, delete_project

st.title("📁 Project & Revision Control")
st.markdown("Manage your active developments or initialize a new project workspace.")

st.divider()

# ==========================================
# 1. SELECT EXISTING PROJECT
# ==========================================
st.subheader("1. Select Existing Project")

# Fetch projects from the database
projects_df = get_all_projects_df()

if projects_df.empty:
    st.info("No projects found in the database. Create one below to get started.")
else:
    # Show the projects in a clean table
    st.dataframe(projects_df, use_container_width=True, hide_index=True)
    
    selected_project = st.selectbox(
        "Select a project to load into your workspace:",
        options=projects_df["project_name"].tolist()
    )
    
    # Load Workspace Button with forced routing
    if st.button("Load Project Workspace", type="primary", use_container_width=True):
        st.session_state["active_project"] = selected_project
        # Instantly force the browser router to jump into the enterprise dashboard
        st.switch_page("views/dashboard.py")

st.divider()

# ==========================================
# 2. CREATE NEW PROJECT
# ==========================================
st.subheader("2. Create New Project")

with st.form("create_project_form"):
    new_proj_name = st.text_input("Project Name (e.g., Rogers Moore Parkway - Phase 1)")
    
    new_proj_phase = st.selectbox(
        "Development Phase", 
        ["Land Acquisition", "Entitlement", "Horizontal / Civil", "Vertical Construction", "Lease-Up & Stabilization"]
    )
    
    new_proj_notes = st.text_area("Initial Notes / Description")
    
    submit_create = st.form_submit_button("Initialize New Project", use_container_width=True)
    
    if submit_create:
        if not new_proj_name.strip():
            st.error("Project Name cannot be empty.")
        else:
            success, msg = create_project(new_proj_name, new_proj_phase, new_proj_notes)
            if success:
                # Automatically lock the new project into session and jump straight in!
                st.session_state["active_project"] = new_proj_name
                st.switch_page("views/dashboard.py")
            else:
                st.error(msg)

# ==========================================
# 3. ADMIN ZONE: DELETE PROJECT
# ==========================================
if st.session_state.get("role") == "Admin":
    st.markdown("---")
    with st.expander("⚠️ Admin: Delete a Project (Danger Zone)", expanded=False):
        st.error("Warning: Deleting a project is permanent. It will destroy all associated proformas and schedules.")
        
        if not projects_df.empty:
            project_names = [name for name in projects_df['project_name'].tolist() if name != "__MASTER_LIBRARY__"]
            
            if project_names:
                project_to_delete = st.selectbox("Select Project to Delete", project_names, key="del_proj_select")
                
                if st.button("🗑️ Permanently Delete Project", use_container_width=True):
                    current_user = st.session_state.get("user_email", "Admin")
                    success, msg = delete_project(project_to_delete, current_user)
                    
                    if success:
                        st.success(f"Project '{project_to_delete}' has been wiped from the cloud.")
                        if st.session_state.get("active_project") == project_to_delete:
                            st.session_state["active_project"] = None
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {msg}")
            else:
                st.info("No active projects available to delete.")
        else:
            st.info("No projects available to delete.")