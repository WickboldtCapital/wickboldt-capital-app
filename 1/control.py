import streamlit as st
import sqlite3
import pandas as pd

DB_FILE = "wickboldt_projects.db"

st.header("📁 Project & Revision Control Landing Page")
st.markdown("Select an existing project to unlock portfolio modules, or initialize a new development phase.")

if st.session_state.get("active_project"):
    st.success(f"Active Loaded Project: **{st.session_state['active_project']}**")
    if st.button("🚀 Open Executive Dashboard", use_container_width=True):
        st.switch_page("pages/dashboard.py")
    st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Select Active Project")
    conn = sqlite3.connect(DB_FILE)
    p_df = pd.read_sql("SELECT project_id, project_name, phase, notes FROM projects", conn)
    conn.close()
    
    if not p_df.empty:
        selected_proj_name = st.selectbox("Choose Project/Phase", p_df['project_name'].tolist())
        if st.button("🚀 Load Selected Project & Open Dashboard", use_container_width=True):
            st.session_state["active_project"] = selected_proj_name
            st.rerun()
    else:
        st.info("No projects registered yet. Please create one on the right.")

with col2:
    st.subheader("2. Initialize New Project")
    with st.form("new_project_form"):
        new_p_name = st.text_input("Project Name (e.g., Rogers Moore Parkway - Phase 1)")
        new_p_phase = st.selectbox("Phase Tag", ["Phase 1 (Lots 1-10)", "Phase 2 (Lots 11-24)", "Master Development", "Tracts C1-3"])
        new_p_notes = st.text_area("Scope & Underwriting Notes", value="Build-to-rent narrow-footprint residential development maintaining a 30% equity position standard.")
        create_btn = st.form_submit_button("Create, Activate & Open Dashboard", use_container_width=True)
        
        if create_btn:
            if new_p_name:
                conn = sqlite3.connect(DB_FILE)
                try:
                    conn.execute("INSERT INTO projects (project_name, phase, notes) VALUES (?, ?, ?)", 
                                 (new_p_name, new_p_phase, new_p_notes))
                    conn.commit()
                    st.session_state["active_project"] = new_p_name
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
                finally:
                    conn.close()
            else:
                st.error("Please provide a project name.")
