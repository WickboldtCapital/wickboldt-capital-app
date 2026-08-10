import streamlit as st
import pandas as pd
from db_ops import get_all_projects_df, create_project

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
    
    # Removed the st.form here to prevent the button from locking up!
    selected_project = st.selectbox(
        "Select a project to load into your workspace:",
        options=projects_df["project_name"].tolist()
    )
    
    # Standard button (no longer a form submit button)
    if st.button("Load Project Workspace", type="primary"):
        st.session_state["active_project"] = selected_project
        st.success(f"Successfully loaded '{selected_project}'! Unlocking portfolio modules...")
        st.rerun()

st.divider()

# ==========================================
# 2. CREATE NEW PROJECT
# ==========================================
st.subheader("2. Create New Project")

# We keep the form here because we are typing in multiple text boxes
with st.form("create_project_form"):
    new_proj_name = st.text_input("Project Name (e.g., Rogers Moore Parkway - Phase 1)")
    
    new_proj_phase = st.selectbox(
        "Development Phase", 
        ["Land Acquisition", "Entitlement", "Horizontal / Civil", "Vertical Construction", "Lease-Up & Stabilization"]
    )
    
    new_proj_notes = st.text_area("Initial Notes / Description")
    
    submit_create = st.form_submit_button("Initialize New Project")
    
    if submit_create:
        if not new_proj_name.strip():
            st.error("Project Name cannot be empty.")
        else:
            success, msg = create_project(new_proj_name, new_proj_phase, new_proj_notes)
            if success:
                st.success(f"Project '{new_proj_name}' created successfully!")
                st.rerun()
            else:
                st.error(msg)