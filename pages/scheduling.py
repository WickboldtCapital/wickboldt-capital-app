import streamlit as st
import pandas as pd
from datetime import date
from db_ops import get_project_milestones, add_enterprise_milestone, complete_enterprise_milestone, delete_enterprise_milestone, init_milestones_table

st.set_page_config(page_title="Scheduling & Milestones", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# Ensure table exists on load
init_milestones_table()

st.header("🗓️ Master Scheduling & Critical Path")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Manage structured construction phases, assign trade accountability, track target dates, and monitor project progress.")
st.divider()

# Standard General Contracting Phases
PHASE_CATEGORIES = [
    "1. Pre-Construction & Permitting",
    "2. Site Work, Grading & Foundation",
    "3. Structural Framing & Exterior Shell",
    "4. MEP Rough-Ins (Mechanical, Electrical, Plumbing)",
    "5. Insulation & Drywall",
    "6. Interior Finishes, Trim & Paint",
    "7. Final Inspection & Turnover"
]

col_form, col_dashboard = st.columns([1, 2], gap="large")

# ==========================================
# LEFT COLUMN: ADD ENTERPRISE MILESTONE
# ==========================================
with col_form:
    st.subheader("Add Master Milestone")
    with st.form("enterprise_schedule_form", clear_on_submit=True):
        phase_cat = st.selectbox("Construction Phase", PHASE_CATEGORIES)
        task_name = st.text_input("Milestone Task Name (e.g., Pour Grade Beam)")
        assigned_trade = st.text_input("Responsible Trade / Subcontractor", placeholder="e.g., Acadiana Concrete LLC")
        
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Target Start", value=date.today())
        due_date = c2.date_input("Target Due", value=date.today())
        
        submitted = st.form_submit_button("💾 Save to Master Schedule", type="primary", use_container_width=True)
        
        if submitted:
            if not task_name or not assigned_trade:
                st.error("Please provide both a task name and a responsible trade.")
            elif start_date > due_date:
                st.error("⚠️ The Target Due date cannot be earlier than the Target Start date.")
            else:
                add_enterprise_milestone(active_project, phase_cat, task_name, assigned_trade, start_date, due_date)
                st.success(f"Milestone '{task_name}' successfully added!")
                st.rerun()

# ==========================================
# RIGHT COLUMN: MASTER TIMELINE DASHBOARD
# ==========================================
with col_dashboard:
    st.subheader("Project Timeline & Accountability")
    milestones_df = get_project_milestones(active_project)
    
    if milestones_df.empty:
        st.info("No milestones tracked yet for this project. Add your first phase on the left.")
    else:
        # Sort chronologically by start_date so the schedule flows logically
        milestones_df = milestones_df.sort_values(by='start_date')
        
        # Calculate Metrics
        total_tasks = len(milestones_df)
        completed_tasks = len(milestones_df[milestones_df['is_complete'] == 1])
        progress_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # High-level Progress Bar
        st.progress(progress_ratio, text=f"Overall Project Completion: {int(progress_ratio * 100)}% ({completed_tasks} of {total_tasks} milestones complete)")
        st.write("")
        
        # Metric Cards
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Milestones", total_tasks)
        m2.metric("Completed Phases", completed_tasks)
        m3.metric("Critical Path Status", "On Schedule ✅" if progress_ratio < 1.0 else "Finished 🏆")
        
        st.divider()
        
        # Group and Render by Phase Category
        for phase in PHASE_CATEGORIES:
            phase_df = milestones_df[milestones_df['phase_category'] == phase]
            if phase_df.empty:
                continue
                
            phase_completed = len(phase_df[phase_df['is_complete'] == 1])
            phase_total = len(phase_df)
            badge = "✅" if phase_completed == phase_total else "⏳"
            
            with st.expander(f"{badge} {phase} ({phase_completed}/{phase_total})", expanded=(phase_completed < phase_total)):
                for _, row in phase_df.iterrows():
                    rc1, rc2, rc3 = st.columns([3, 2, 1.5])
                    
                    with rc1:
                        status_icon = "✅" if row['is_complete'] == 1 else "🔲"
                        st.markdown(f"{status_icon} **{row['task_name']}**")
                        st.caption(f"Target: {row['start_date']} to {row['due_date']}")
                        
                    with rc2:
                        st.markdown(f"**Trade:** `{row['assigned_trade']}`")
                        if row['is_complete'] == 1 and row['completed_by']:
                            st.caption(f"Done by {row['completed_by']}")
                            
                    with rc3:
                        if row['is_complete'] == 0:
                            if st.button("Complete", key=f"btn_{row['id']}", type="primary", use_container_width=True):
                                user = st.session_state.get("email", "Superintendent")
                                complete_enterprise_milestone(row['id'], user)
                                st.balloons()
                                st.success("Locked in!")
                                st.rerun()
                            if st.button("🗑️ Delete", key=f"del_{row['id']}", use_container_width=True):
                                delete_enterprise_milestone(row['id'])
                                st.warning("Milestone removed.")
                                st.rerun()
                        else:
                            st.caption("Completed")
                    st.markdown("---")