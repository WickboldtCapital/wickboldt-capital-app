import streamlit as st
import pandas as pd
from db_ops import (
    get_all_training_modules, 
    add_training_module, 
    update_training_module, 
    delete_training_module,
    get_user_completed_modules, 
    mark_module_completed
)

st.title("Enterprise Training & SOPs 📚")
user_email = st.session_state.get("email", "Unknown")
user_role = st.session_state.get("role", "viewer").lower()

modules_df = get_all_training_modules()

# --- ADMIN ROUTING: TABS ---
if user_role == "admin":
    tab_library, tab_admin = st.tabs(["📚 Training Library", "⚙️ Admin Management Dashboard"])
else:
    tab_library = st.container()

# ==========================================
# ⚙️ ADMIN MANAGEMENT DASHBOARD
# ==========================================
if user_role == "admin":
    with tab_admin:
        st.subheader("Manage Training Content")
        st.markdown("Create nested structures: **Category** (e.g. Safety) ➔ **Chapter** (e.g. Scaffolding) ➔ **Module** (e.g. Inspection Rules).")
        
        # --- PUBLISH NEW MODULE ---
        with st.expander("➕ Publish New Sub-Section / Module", expanded=False):
            with st.form("new_training_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    t_category = st.selectbox("Category (Level 1)", ["Safety", "Standard Operating Procedure (SOP)", "Onboarding", "Technical Guide"])
                with col2:
                    t_chapter = st.text_input("Chapter/Course (Level 2)", placeholder="e.g., Module 1: Basics")
                with col3:
                    t_title = st.text_input("Sub-Section Title (Level 3)")
                
                vid_col1, vid_col2 = st.columns(2)
                with vid_col1:
                    t_video = st.text_input("Video URL (Optional)")
                with vid_col2:
                    t_sort = st.number_input("Display Order (Within Chapter)", value=0, step=1)
                
                t_content = st.text_area("Written Content (Markdown supported)", height=150)
                
                if st.form_submit_button("Publish Module", type="primary"):
                    # Default chapter to General if left blank
                    chapter_val = t_chapter if t_chapter else "General Overview"
                    if t_title and t_content:
                        add_training_module(t_title, t_category, chapter_val, t_content, t_video, t_sort, user_email)
                        st.success("Published successfully!")
                        st.rerun()
                    else:
                        st.error("Title and Content are required.")
                        
        st.divider()
        
        # --- EDIT & REORDER EXISTING MODULES ---
        st.subheader("Revise Existing Modules")
        if modules_df.empty:
            st.info("No modules exist yet.")
        else:
            for _, row in modules_df.iterrows():
                with st.expander(f"Edit: {row['title']} (Chapter: {row.get('chapter', 'General')})"):
                    with st.form(f"edit_form_{row['id']}"):
                        e_col1, e_col2, e_col3 = st.columns(3)
                        with e_col1:
                            categories = ["Safety", "Standard Operating Procedure (SOP)", "Onboarding", "Technical Guide"]
                            if row['category'] not in categories:
                                categories.append(row['category'])
                            e_category = st.selectbox("Category", categories, index=categories.index(row['category']))
                        with e_col2:
                            current_chapter = row.get('chapter', 'General Overview')
                            e_chapter = st.text_input("Chapter/Course", value=current_chapter)
                        with e_col3:
                            e_title = st.text_input("Title", value=row['title'])
                            
                        vid_col1, vid_col2 = st.columns(2)
                        with vid_col1:
                            current_video = row['video_url'] if pd.notna(row['video_url']) else ""
                            e_video = st.text_input("Video URL", value=current_video)
                        with vid_col2:
                            e_sort = st.number_input("Display Order", value=int(row['sort_order']), step=1)
                            
                        e_content = st.text_area("Content", value=row['content'], height=150)
                        
                        btn_col1, btn_col2 = st.columns([1, 1])
                        with btn_col1:
                            if st.form_submit_button("💾 Save Revisions", type="primary"):
                                update_training_module(row['id'], e_title, e_category, e_chapter, e_content, e_video, e_sort, user_email)
                                st.success("Module updated!")
                                st.rerun()
                        with btn_col2:
                            delete_check = st.checkbox("Check here to confirm deletion")
                            if st.form_submit_button("🗑️ Delete Module"):
                                if delete_check:
                                    delete_training_module(row['id'], user_email)
                                    st.success("Module deleted.")
                                    st.rerun()
                                else:
                                    st.error("Please check the box to confirm deletion.")

# ==========================================
# 📚 TRAINING LIBRARY (USER VIEW)
# ==========================================
with tab_library:
    st.markdown("Navigate through the categories and chapters below to review required materials.")
    completed_ids = get_user_completed_modules(user_email)

    if modules_df.empty:
        st.info("No training modules have been published yet.")
    else:
        # Level 1: Categories
        categories = modules_df['category'].unique()
        
        for cat in categories:
            st.header(f"📂 {cat}")
            cat_modules = modules_df[modules_df['category'] == cat]
            
            # Level 2: Chapters within Category
            chapters = cat_modules['chapter'].fillna('General Overview').unique()
            
            for chap in chapters:
                st.subheader(f"📖 {chap}")
                chap_modules = cat_modules[cat_modules['chapter'] == chap]
                
                # Level 3: Modules/Subsections within Chapter
                for _, row in chap_modules.iterrows():
                    is_done = row['id'] in completed_ids
                    status_icon = "✅" if is_done else "⚠️"
                    
                    with st.expander(f"{status_icon} {row['title']}"):
                        
                        if pd.notna(row.get('video_url')) and row['video_url'].strip() != "":
                            try:
                                st.video(row['video_url'])
                                st.divider()
                            except Exception:
                                st.error("Failed to load video. Ensure the URL is valid.")
                        
                        st.markdown(row['content'])
                        st.divider()
                        
                        if is_done:
                            st.success(f"You have completed this sub-section.")
                        else:
                            if st.button("Mark as Read & Understood", key=f"read_{row['id']}"):
                                mark_module_completed(user_email, row['id'], row['title'])
                                st.balloons()
                                st.rerun()