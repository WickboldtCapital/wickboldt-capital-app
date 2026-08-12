import streamlit as st
import pandas as pd
import base64
from streamlit_quill import st_quill
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
        st.markdown("Create nested structures: **Category** ➔ **Chapter** ➔ **Module**.")
        
        # --- PUBLISH NEW MODULE ---
        with st.expander("➕ Publish New Sub-Section / Module", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                t_category = st.selectbox("Category (Level 1)", ["Safety", "Standard Operating Procedure (SOP)", "Onboarding", "Technical Guide"], key="new_cat")
            with col2:
                t_chapter = st.text_input("Chapter/Course (Level 2)", placeholder="e.g., Module 1: Basics", key="new_chap")
            with col3:
                t_title = st.text_input("Sub-Section Title (Level 3)", key="new_title")
            
            vid_col1, vid_col2 = st.columns(2)
            with vid_col1:
                t_video = st.text_input("Video URL (Optional)", key="new_vid")
            with vid_col2:
                t_sort = st.number_input("Display Order (Within Chapter)", value=0, step=1, key="new_sort")
            
            st.markdown("**Module Content (Rich Text Editor)**")
            t_content = st_quill(placeholder="Type your rich text here...", html=True, key="new_quill")
            
            st.markdown("**File Attachment**")
            t_file = st.file_uploader("Upload a PDF, document, or spreadsheet", key="new_file")
            
            if st.button("Publish Module", type="primary", key="new_pub_btn"):
                chapter_val = t_chapter if t_chapter else "General Overview"
                
                # Encode file to Base64 if attached
                t_fname, t_fdata = None, None
                if t_file is not None:
                    t_fname = t_file.name
                    t_fdata = base64.b64encode(t_file.read()).decode('utf-8')
                
                if t_title and t_content:
                    add_training_module(t_title, t_category, chapter_val, t_content, t_video, t_sort, t_fname, t_fdata, user_email)
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
                    e_col1, e_col2, e_col3 = st.columns(3)
                    with e_col1:
                        categories = ["Safety", "Standard Operating Procedure (SOP)", "Onboarding", "Technical Guide"]
                        if row['category'] not in categories:
                            categories.append(row['category'])
                        e_category = st.selectbox("Category", categories, index=categories.index(row['category']), key=f"cat_{row['id']}")
                    with e_col2:
                        current_chapter = row.get('chapter', 'General Overview')
                        e_chapter = st.text_input("Chapter/Course", value=current_chapter, key=f"chap_{row['id']}")
                    with e_col3:
                        e_title = st.text_input("Title", value=row['title'], key=f"title_{row['id']}")
                        
                    vid_col1, vid_col2 = st.columns(2)
                    with vid_col1:
                        current_video = row['video_url'] if pd.notna(row['video_url']) else ""
                        e_video = st.text_input("Video URL", value=current_video, key=f"vid_{row['id']}")
                    with vid_col2:
                        e_sort = st.number_input("Display Order", value=int(row['sort_order']), step=1, key=f"sort_{row['id']}")
                        
                    st.markdown("**Module Content (Rich Text Editor)**")
                    e_content = st_quill(value=row['content'], html=True, key=f"quill_{row['id']}")
                    
                    st.markdown("**File Attachment**")
                    current_fname = row.get('attached_file_name')
                    remove_file = False
                    
                    if pd.notna(current_fname) and current_fname:
                        st.info(f"📎 Current Attachment: {current_fname}")
                        remove_file = st.checkbox("Remove current attachment", key=f"rm_file_{row['id']}")
                    
                    e_file = st.file_uploader("Upload new file (replaces current)", key=f"file_{row['id']}")
                    
                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        if st.button("💾 Save Revisions", type="primary", key=f"save_{row['id']}"):
                            # Handle file logic
                            e_fname = current_fname
                            e_fdata = row.get('attached_file_data')
                            
                            if e_file is not None:
                                e_fname = e_file.name
                                e_fdata = base64.b64encode(e_file.read()).decode('utf-8')
                            elif remove_file:
                                e_fname = None
                                e_fdata = None
                                
                            update_training_module(row['id'], e_title, e_category, e_chapter, e_content, e_video, e_sort, e_fname, e_fdata, user_email)
                            st.success("Module updated!")
                            st.rerun()
                    with btn_col2:
                        delete_check = st.checkbox("Check here to confirm deletion", key=f"del_chk_{row['id']}")
                        if st.button("🗑️ Delete Module", key=f"del_btn_{row['id']}"):
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
        categories = modules_df['category'].unique()
        
        for cat in categories:
            st.header(f"📂 {cat}")
            cat_modules = modules_df[modules_df['category'] == cat]
            
            chapters = cat_modules['chapter'].fillna('General Overview').unique()
            
            for chap in chapters:
                st.subheader(f"📖 {chap}")
                chap_modules = cat_modules[cat_modules['chapter'] == chap]
                
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
                        
                        # Render Rich HTML content
                        st.markdown(row['content'], unsafe_allow_html=True)
                        st.divider()
                        
                        # Render File Download Button if a file is attached
                        if pd.notna(row.get('attached_file_name')) and row['attached_file_name'] and pd.notna(row.get('attached_file_data')):
                            try:
                                file_bytes = base64.b64decode(row['attached_file_data'])
                                st.download_button(
                                    label=f"📄 Download Attached File: {row['attached_file_name']}",
                                    data=file_bytes,
                                    file_name=row['attached_file_name'],
                                    key=f"dl_{row['id']}"
                                )
                                st.divider()
                            except Exception:
                                st.error("Attached file corrupted or unable to be decoded.")
                        
                        if is_done:
                            st.success(f"You have completed this sub-section.")
                        else:
                            if st.button("Mark as Read & Understood", key=f"read_{row['id']}"):
                                mark_module_completed(user_email, row['id'], row['title'])
                                st.balloons()
                                st.rerun()