import streamlit as st
import pandas as pd
import base64
from streamlit_quill import st_quill
from db_ops import (
    get_lms_categories, add_lms_category, delete_lms_category,
    get_lms_chapters, add_lms_chapter, delete_lms_chapter,
    get_lms_modules, add_lms_module, delete_lms_module,
    get_user_completed_modules, mark_module_completed
)

user_email = st.session_state.get("email", "Unknown")
user_role = st.session_state.get("role", "viewer").lower()

# --- STATE ROUTING ---
if "active_lms_module" not in st.session_state:
    st.session_state["active_lms_module"] = None

# Fetch active data
cats_df = get_lms_categories()
chaps_df = get_lms_chapters()
mods_df = get_lms_modules()
completed_ids = get_user_completed_modules(user_email)

# ==========================================
# 📖 FOCUS MODE: READING A MODULE
# ==========================================
if st.session_state["active_lms_module"] is not None:
    mod_id = st.session_state["active_lms_module"]
    mod_row = mods_df[mods_df['id'] == mod_id].iloc[0]
    
    if st.button("← Back to Training Library"):
        st.session_state["active_lms_module"] = None
        st.rerun()
    
    st.divider()
    st.caption(f"{mod_row['category_title']} / {mod_row['chapter_title']}")
    st.title(mod_row['title'])
    st.markdown(f"*{mod_row['description']}*")
    st.divider()
    
    if pd.notna(mod_row.get('video_url')) and mod_row['video_url'].strip() != "":
        try:
            st.video(mod_row['video_url'])
            st.divider()
        except:
            pass
            
    st.markdown(mod_row['content'], unsafe_allow_html=True)
    st.divider()
    
    if pd.notna(mod_row.get('attached_file_name')) and mod_row['attached_file_name']:
        if pd.notna(mod_row.get('attached_file_desc')) and mod_row['attached_file_desc'].strip():
            st.write(f"**Instructions:** {mod_row['attached_file_desc']}")
        file_bytes = base64.b64decode(mod_row['attached_file_data'])
        st.download_button(
            label=f"📄 Download Attached File: {mod_row['attached_file_name']}",
            data=file_bytes,
            file_name=mod_row['attached_file_name'],
            type="primary"
        )
        st.divider()
        
    if mod_id in completed_ids:
        st.success("✅ You have completed this module.")
    else:
        if st.button("Acknowledge: I have read and understood this material", type="primary"):
            mark_module_completed(user_email, mod_id)
            st.balloons()
            st.session_state["active_lms_module"] = None
            st.rerun()
            
    st.stop() # Prevents the rest of the page from rendering in Focus Mode

# ==========================================
# 📚 STANDARD VIEW: LIBRARY & ADMIN
# ==========================================
st.title("Enterprise Training & SOPs 📚")

if user_role == "admin":
    tab_library, tab_admin = st.tabs(["📚 Training Library", "⚙️ Admin Builder"])
else:
    tab_library = st.container()

# --- ADMIN BUILDER ---
if user_role == "admin":
    with tab_admin:
        st.info("Build your curriculum sequentially: Create a Category ➔ Create a Chapter ➔ Add Modules.")
        
        col_cat, col_chap = st.columns(2)
        with col_cat:
            with st.expander("1. Manage Categories"):
                with st.form("f_cat", clear_on_submit=True):
                    c_title = st.text_input("Category Title")
                    c_desc = st.text_input("Category Description")
                    c_sort = st.number_input("Sort Order", value=0)
                    if st.form_submit_button("Create Category"):
                        add_lms_category(c_title, c_desc, c_sort)
                        st.rerun()
                st.divider()
                for _, r in cats_df.iterrows():
                    st.write(f"📁 **{r['title']}**")
                    if st.button("Delete", key=f"dcat_{r['id']}", help="Warning: Deletes all linked chapters and modules."):
                        delete_lms_category(r['id'])
                        st.rerun()

        with col_chap:
            with st.expander("2. Manage Chapters"):
                if cats_df.empty:
                    st.warning("Create a Category first.")
                else:
                    with st.form("f_chap", clear_on_submit=True):
                        cat_opts = dict(zip(cats_df['title'], cats_df['id']))
                        sel_cat = st.selectbox("Belongs to Category", list(cat_opts.keys()))
                        ch_title = st.text_input("Chapter Title")
                        ch_desc = st.text_input("Chapter Description")
                        ch_sort = st.number_input("Sort Order", value=0)
                        if st.form_submit_button("Create Chapter"):
                            add_lms_chapter(cat_opts[sel_cat], ch_title, ch_desc, ch_sort)
                            st.rerun()
                st.divider()
                for _, r in chaps_df.iterrows():
                    st.write(f"📖 **{r['title']}** (in {r['category_title']})")
                    if st.button("Delete", key=f"dchap_{r['id']}", help="Warning: Deletes all linked modules."):
                        delete_lms_chapter(r['id'])
                        st.rerun()

        with st.expander("3. Manage Modules (Content & Files)", expanded=True):
            if chaps_df.empty:
                st.warning("Create a Chapter first.")
            else:
                with st.form("f_mod", clear_on_submit=True):
                    ch_opts = {f"{row['category_title']} -> {row['title']}": row['id'] for _, row in chaps_df.iterrows()}
                    sel_chap = st.selectbox("Belongs to Chapter", list(ch_opts.keys()))
                    
                    m_title = st.text_input("Module Title")
                    m_desc = st.text_input("Short Description (Visible on Library Tree)")
                    m_vid = st.text_input("Video URL (Optional)")
                    m_sort = st.number_input("Sort Order", value=0)
                    
                    st.write("**Rich Content Editor**")
                    m_content = st_quill(placeholder="Write your module content here...", html=True)
                    
                    st.write("**File Upload**")
                    m_file = st.file_uploader("Attach PDF or Document")
                    m_fdesc = st.text_input("File Instructions")
                    
                    if st.form_submit_button("Publish Module", type="primary"):
                        fname, fdata = None, None
                        if m_file:
                            fname = m_file.name
                            fdata = base64.b64encode(m_file.read()).decode('utf-8')
                        add_lms_module(ch_opts[sel_chap], m_title, m_desc, m_content, m_vid, m_sort, fname, fdata, m_fdesc)
                        st.success("Module Published!")
                        st.rerun()
                        
                st.divider()
                st.write("**Existing Modules**")
                for _, r in mods_df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 **{r['title']}** (in {r['chapter_title']})")
                    with col2:
                        if st.button("🗑️ Delete", key=f"dmod_{r['id']}"):
                            delete_lms_module(r['id'])
                            st.rerun()

# --- LIBRARY VIEW (THE TREE) ---
with tab_library:
    if cats_df.empty:
        st.info("No curriculum has been published yet.")
    else:
        for _, cat in cats_df.iterrows():
            st.header(f"📂 {cat['title']}")
            if pd.notna(cat.get('description')) and cat['description'].strip():
                st.caption(cat['description'])
                
            cat_chaps = chaps_df[chaps_df['category_id'] == cat['id']]
            
            for _, chap in cat_chaps.iterrows():
                with st.container(border=True):
                    st.subheader(f"📖 {chap['title']}")
                    if pd.notna(chap.get('description')) and chap['description'].strip():
                        st.write(f"*{chap['description']}*")
                        
                    chap_mods = mods_df[mods_df['chapter_id'] == chap['id']]
                    if chap_mods.empty:
                        st.caption("No modules in this chapter yet.")
                    else:
                        for _, mod in chap_mods.iterrows():
                            m_col1, m_col2 = st.columns([3, 1])
                            with m_col1:
                                is_done = mod['id'] in completed_ids
                                icon = "✅" if is_done else "⚠️"
                                st.write(f"**{icon} {mod['title']}**")
                                if pd.notna(mod.get('description')) and mod['description'].strip():
                                    st.caption(mod['description'])
                            with m_col2:
                                if st.button("Read Module", key=f"go_{mod['id']}", use_container_width=True):
                                    st.session_state["active_lms_module"] = mod['id']
                                    st.rerun()