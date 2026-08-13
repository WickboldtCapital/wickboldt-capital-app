import streamlit as st
from db_ops import get_project_milestones, add_milestone, complete_milestone

st.title("Scheduling & Milestones 🗓️")
active_project = st.session_state.get("active_project")

if not active_project:
    st.warning("Please select an active project from the Project Control page first.")
    st.stop()

st.markdown(f"**Tracking progress for:** `{active_project}`")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

# --- ADD NEW MILESTONES (LEFT COLUMN) ---
with col1:
    st.subheader("Add Phase")
    with st.form("add_milestone_form", clear_on_submit=True):
        new_task = st.text_input("Milestone Name (e.g., Foundation Poured, Framing Complete)")
        submitted = st.form_submit_button("Add to Schedule", use_container_width=True)
        
        if submitted:
            if new_task:
                add_milestone(active_project, new_task)
                st.success("Milestone added!")
                st.rerun()
            else:
                st.error("Please enter a milestone name.")

# --- TRACKING DASHBOARD (RIGHT COLUMN) ---
with col2:
    st.subheader("Project Tracker")
    milestones_df = get_project_milestones(active_project)
    
    if milestones_df.empty:
        st.info("No milestones tracked yet for this project. Add one on the left.")
    else:
        # Separate into pending and completed
        pending = milestones_df[~milestones_df['is_complete']]
        completed = milestones_df[milestones_df['is_complete']]
        
        # Calculate progress
        progress = len(completed) / len(milestones_df)
        st.progress(progress, text=f"Overall Completion: {int(progress * 100)}%")
        st.write("")
        
        # Display Pending Tasks
        st.markdown("### ⏳ Pending Actions")
        if pending.empty:
            st.success("All current milestones are complete!")
        else:
            for _, row in pending.iterrows():
                row_col1, row_col2 = st.columns([3, 1])
                with row_col1:
                    st.write(f"🔲 **{row['task_name']}**")
                with row_col2:
                    if st.button("Mark Complete", key=f"complete_{row['id']}", type="primary"):
                        complete_milestone(row['id'], st.session_state.get("email", "Unknown User"))
                        st.balloons()  # Visual celebration trigger
                        st.success(f"Alert: {row['task_name']} has been locked in as completed!")
                        st.rerun()
        
        st.divider()
        
        # Display Completed Tasks
        st.markdown("### ✅ Completed Phases")
        if not completed.empty:
            for _, row in completed.iterrows():
                st.caption(f"✅ **{row['task_name']}** — *Completed by {row['completed_by']}*")