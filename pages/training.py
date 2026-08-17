import streamlit as st
import pandas as pd
import sqlite3
import base64
from datetime import date
from streamlit_quill import st_quill
from db_ops import (
    get_lms_categories, add_lms_category, delete_lms_category,
    get_lms_chapters, add_lms_chapter, delete_lms_chapter,
    get_lms_modules, add_lms_module, delete_lms_module,
    get_lms_topics, add_lms_topic, delete_lms_topic,
    get_lms_subtopics, add_lms_subtopic, delete_lms_subtopic,
    get_user_progress, mark_progress
)

st.set_page_config(page_title="Enterprise Training & SOPs", layout="wide")

# ==========================================
# 🔒 ROLE-BASED ACCESS & MULTI-TENANT GATEKEEPER
# ==========================================
if not st.session_state.get("logged_in"):
    st.warning("⚠️ Access Restricted: Please log in.")
    st.stop()

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load an authorized project from the Control tab.")
    st.stop()

user_email = st.session_state.get("email", st.session_state.get("username", "Unknown"))
user_role = st.session_state.get("role", "viewer").lower()

# Define specific permissions based on the role hierarchy
is_admin_or_educator = user_role in ["admin", "educator", "manager"]
is_assistant = user_role in ["assistant", "educator assistant", "educator_assistant"]
can_build_curriculum = is_admin_or_educator or is_assistant

if "active_lms_focus" not in st.session_state: st.session_state["active_lms_focus"] = None 

# --- ENTERPRISE DATABASE EXPANSION (For Jobsite Tracking) ---
DB_FILE = "wickboldt_projects.db"
def init_compliance_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lms_training_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            course_name TEXT,
            worker_name TEXT,
            trade_company TEXT,
            completion_date TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_compliance_db()

# Fetch all data layers from existing db_ops
cats_df = get_lms_categories()
chaps_df = get_lms_chapters()
mods_df = get_lms_modules()
tops_df = get_lms_topics()
subs_df = get_lms_subtopics()

# Fetch Self-Paced Progress
done_mods = get_user_progress(user_email, "lms_module_progress", "module_id")
done_tops = get_user_progress(user_email, "lms_topic_progress", "topic_id")
done_subs = get_user_progress(user_email, "lms_subtopic_progress", "subtopic_id")

# ==========================================
# 📖 UNIVERSAL FOCUS MODE (READER) - PRESERVED 100%
# ==========================================
if st.session_state["active_lms_focus"] is not None:
    focus = st.session_state["active_lms_focus"]
    f_type, f_id = focus["type"], focus["id"]
    
    if f_type == "module":
        row = mods_df[mods_df['id'] == f_id].iloc[0]
        prog_table, prog_col, is_done = "lms_module_progress", "module_id", (f_id in done_mods)
        hierarchy = f"{row['category_title']} / {row['chapter_title']}"
    elif f_type == "topic":
        row = tops_df[tops_df['id'] == f_id].iloc[0]
        prog_table, prog_col, is_done = "lms_topic_progress", "topic_id", (f_id in done_tops)
        hierarchy = f"{row['category_title']} / {row['chapter_title']} / {row['module_title']}"
    else: 
        row = subs_df[subs_df['id'] == f_id].iloc[0]
        prog_table, prog_col, is_done = "lms_subtopic_progress", "subtopic_id", (f_id in done_subs)
        hierarchy = f"{row['category_title']} / {row['chapter_title']} / {row['module_title']} / {row['topic_title']}"
    
    if st.button("← Back to Training Library"):
        st.session_state["active_lms_focus"] = None
        st.rerun()
    
    st.divider()
    st.caption(hierarchy)
    st.title(row['title'])
    st.markdown(f"*{row['description']}*")
    st.divider()
    
    if pd.notna(row.get('video_url')) and row['video_url'].strip() != "":
        try: st.video(row['video_url']); st.divider()
        except: pass
            
    if pd.notna(row.get('content')) and row['content'].strip():
        st.markdown(row['content'], unsafe_allow_html=True)
        st.divider()
    
    if pd.notna(row.get('attached_file_name')) and row['attached_file_name']:
        if pd.notna(row.get('attached_file_desc')) and row['attached_file_desc'].strip():
            st.write(f"**Instructions:** {row['attached_file_desc']}")
        st.download_button(
            label=f"📄 Download Attached File: {row['attached_file_name']}",
            data=base64.b64decode(row['attached_file_data']),
            file_name=row['attached_file_name'],
            type="primary"
        )
        st.divider()
        
    if is_done:
        st.success("✅ You have completed this material.")
    else:
        if st.button("Acknowledge: I have read and understood this material", type="primary"):
            mark_progress(user_email, prog_table, prog_col, f_id)
            st.balloons(); st.session_state["active_lms_focus"] = None; st.rerun()
            
    st.stop() 

# ==========================================
# 📚 ENTERPRISE MULTI-TAB VIEW
# ==========================================
st.title("Enterprise Training & SOPs 📚")
st.markdown(f"**Active Workspace:** `{active_project}`")
st.divider()

if can_build_curriculum: 
    tab_library, tab_admin, tab_certify, tab_logs = st.tabs(["📚 Training Library", "⚙️ Curriculum Builder", "✍️ Jobsite Certifications", "📊 Compliance Reports"])
else: 
    tab_library, tab_certify, tab_logs = st.tabs(["📚 Training Library", "✍️ Jobsite Certifications", "📊 Compliance Reports"])

# ==========================================
# TAB 1: LIBRARY VIEW (THE FLEXIBLE TREE) - PRESERVED 100%
# ==========================================
def has_content(row):
    if pd.notna(row.get('content')) and row['content'].strip(): return True
    if pd.notna(row.get('video_url')) and row['video_url'].strip(): return True
    if pd.notna(row.get('attached_file_name')) and row['attached_file_name']: return True
    return False

with tab_library:
    if cats_df.empty: st.info("No curriculum has been published yet.")
    else:
        for _, cat in cats_df.iterrows():
            st.header(f"📂 {cat['title']}")
            if pd.notna(cat.get('description')) and cat['description'].strip(): st.caption(cat['description'])
                
            for _, chap in chaps_df[chaps_df['category_id'] == cat['id']].iterrows():
                with st.container(border=True):
                    st.subheader(f"📖 {chap['title']}")
                    if pd.notna(chap.get('description')) and chap['description'].strip(): st.write(f"*{chap['description']}*")
                        
                    for _, mod in mods_df[mods_df['chapter_id'] == chap['id']].iterrows():
                        m_has_content = has_content(mod)
                        m_icon = "✅" if mod['id'] in done_mods else "📦"
                        
                        with st.expander(f"{m_icon} {mod['title']}"):
                            if pd.notna(mod.get('description')) and mod['description'].strip(): st.caption(mod['description'])
                            
                            if m_has_content:
                                if st.button("📖 Read Module Material", key=f"rm_{mod['id']}", type="primary"):
                                    st.session_state["active_lms_focus"] = {"type": "module", "id": mod['id']}; st.rerun()
                                    
                            for _, top in tops_df[tops_df['module_id'] == mod['id']].iterrows():
                                t_has_content = has_content(top)
                                t_icon = "✅" if top['id'] in done_tops else "📑"
                                
                                t_col1, t_col2 = st.columns([3, 1])
                                with t_col1:
                                    st.markdown(f"**{t_icon} {top['title']}**")
                                    if pd.notna(top.get('description')) and top['description'].strip(): st.caption(top['description'])
                                with t_col2:
                                    if t_has_content:
                                        if st.button("Read Topic", key=f"rt_{top['id']}"):
                                            st.session_state["active_lms_focus"] = {"type": "topic", "id": top['id']}; st.rerun()
                                            
                                for _, sub in subs_df[subs_df['topic_id'] == top['id']].iterrows():
                                    s_col1, s_col2 = st.columns([4, 1])
                                    with s_col1:
                                        s_icon = "✅" if sub['id'] in done_subs else "📄"
                                        st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{s_icon} {sub['title']}")
                                        if pd.notna(sub.get('description')) and sub['description'].strip():
                                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;{sub['description']}")
                                    with s_col2:
                                        if st.button("Read", key=f"rs_{sub['id']}", use_container_width=True):
                                            st.session_state["active_lms_focus"] = {"type": "subtopic", "id": sub['id']}; st.rerun()
                                st.divider()

# ==========================================
# TAB 2: CURRICULUM BUILDER (ADMIN) - PRESERVED 100%
# ==========================================
if can_build_curriculum:
    with tab_admin:
        if is_admin_or_educator:
            st.info("You have full Architecture Access. Construct your curriculum sequentially.")
        else:
            st.info("🔒 **Assistant Access Restricted:** You may only add and manage content at the Topic and Sub-Topic levels within existing Modules.")
        
        # --- LEVEL 1: CATEGORIES ---
        if is_admin_or_educator:
            with st.expander("1. Manage Categories", expanded=cats_df.empty):
                with st.form("f_cat", clear_on_submit=True):
                    c_title = st.text_input("Category Title")
                    c_desc = st.text_input("Description")
                    c_sort = st.number_input("Sort Order", value=0)
                    if st.form_submit_button("Create Category", type="primary"):
                        add_lms_category(c_title, c_desc, c_sort); st.rerun()
                for _, r in cats_df.iterrows():
                    if st.button(f"🗑️ Delete Category: {r['title']}", key=f"dcat_{r['id']}"): delete_lms_category(r['id']); st.rerun()

        # --- LEVEL 2: CHAPTERS ---
        if is_admin_or_educator:
            if not cats_df.empty:
                with st.expander("2. Manage Chapters", expanded=chaps_df.empty):
                    with st.form("f_chap", clear_on_submit=True):
                        cat_opts = dict(zip(cats_df['title'], cats_df['id']))
                        sel_cat = st.selectbox("Belongs to Category", list(cat_opts.keys()))
                        ch_title = st.text_input("Chapter Title")
                        ch_desc = st.text_input("Description")
                        ch_sort = st.number_input("Sort Order", value=0)
                        if st.form_submit_button("Create Chapter", type="primary"):
                            add_lms_chapter(cat_opts[sel_cat], ch_title, ch_desc, ch_sort); st.rerun()
                    for _, r in chaps_df.iterrows():
                        if st.button(f"🗑️ Delete Chapter: {r['title']}", key=f"dchap_{r['id']}"): delete_lms_chapter(r['id']); st.rerun()
            else:
                st.info("🔒 **Step 2 Locked:** Create at least one Category above to unlock Chapters.")

        # --- LEVEL 3: MODULES ---
        if is_admin_or_educator:
            if not chaps_df.empty:
                with st.expander("3. Manage Modules (Add Content Here if Desired)", expanded=mods_df.empty):
                    with st.form("f_mod", clear_on_submit=True):
                        ch_opts = {f"{row['category_title']} -> {row['title']}": row['id'] for _, row in chaps_df.iterrows()}
                        sel_chap = st.selectbox("Belongs to Chapter", list(ch_opts.keys()))
                        m_title = st.text_input("Module Title")
                        m_desc = st.text_input("Description")
                        m_sort = st.number_input("Sort Order", value=0)
                        m_vid = st.text_input("Video URL (Optional)")
                        st.write("**Rich Content (Leave blank if just a folder)**")
                        m_content = st_quill(placeholder="Content...", html=True, key="q_mod")
                        st.write("**File Attachment**")
                        m_file = st.file_uploader("Attach PDF or Document", key="f_mod_up")
                        m_fdesc = st.text_input("File Instructions")
                        if st.form_submit_button("Publish Module", type="primary"):
                            fn, fd = None, None
                            if m_file: fn, fd = m_file.name, base64.b64encode(m_file.read()).decode('utf-8')
                            add_lms_module(ch_opts[sel_chap], m_title, m_desc, m_content, m_vid, m_sort, fn, fd, m_fdesc); st.rerun()
                    for _, r in mods_df.iterrows():
                        if st.button(f"🗑️ Delete Module: {r['title']}", key=f"dmod_{r['id']}"): delete_lms_module(r['id']); st.rerun()
            elif not cats_df.empty:
                st.info("🔒 **Step 3 Locked:** Create at least one Chapter above to unlock Modules.")

        # --- LEVEL 4: TOPICS ---
        if not mods_df.empty:
            with st.expander("4. Manage Topics (Add Content Here if Desired)", expanded=tops_df.empty):
                with st.form("f_top", clear_on_submit=True):
                    mod_opts = {f"{row['chapter_title']} -> {row['title']}": row['id'] for _, row in mods_df.iterrows()}
                    sel_mod = st.selectbox("Belongs to Module", list(mod_opts.keys()))
                    t_title = st.text_input("Topic Title")
                    t_desc = st.text_input("Description")
                    t_sort = st.number_input("Sort Order", value=0)
                    t_vid = st.text_input("Video URL (Optional)")
                    st.write("**Rich Content (Leave blank if just a folder)**")
                    t_content = st_quill(placeholder="Content...", html=True, key="q_top")
                    st.write("**File Attachment**")
                    t_file = st.file_uploader("Attach PDF or Document", key="f_top_up")
                    t_fdesc = st.text_input("File Instructions")
                    if st.form_submit_button("Publish Topic", type="primary"):
                        fn, fd = None, None
                        if t_file: fn, fd = t_file.name, base64.b64encode(t_file.read()).decode('utf-8')
                        add_lms_topic(mod_opts[sel_mod], t_title, t_desc, t_content, t_vid, t_sort, fn, fd, t_fdesc); st.rerun()
                for _, r in tops_df.iterrows():
                    if st.button(f"🗑️ Delete Topic: {r['title']}", key=f"dtop_{r['id']}"): delete_lms_topic(r['id']); st.rerun()
        elif is_admin_or_educator and not chaps_df.empty:
            st.info("🔒 **Step 4 Locked:** Create at least one Module above to unlock Topics.")

        # --- LEVEL 5: SUB-TOPICS ---
        if not tops_df.empty:
            with st.expander("5. Manage Sub-Topics (Deepest Level)"):
                with st.form("f_sub", clear_on_submit=True):
                    top_opts = {f"{row['module_title']} -> {row['title']}": row['id'] for _, row in tops_df.iterrows()}
                    sel_top = st.selectbox("Belongs to Topic", list(top_opts.keys()))
                    s_title = st.text_input("Sub-Topic Title")
                    s_desc = st.text_input("Description")
                    s_sort = st.number_input("Sort Order", value=0)
                    s_vid = st.text_input("Video URL (Optional)")
                    st.write("**Rich Content Editor**")
                    s_content = st_quill(placeholder="Content...", html=True, key="q_sub")
                    st.write("**File Attachment**")
                    s_file = st.file_uploader("Attach PDF or Document", key="f_sub_up")
                    s_fdesc = st.text_input("File Instructions")
                    if st.form_submit_button("Publish Sub-Topic", type="primary"):
                        fn, fd = None, None
                        if s_file: fn, fd = s_file.name, base64.b64encode(s_file.read()).decode('utf-8')
                        add_lms_subtopic(top_opts[sel_top], s_title, s_desc, s_content, s_vid, s_sort, fn, fd, s_fdesc); st.rerun()
                for _, r in subs_df.iterrows():
                    if st.button(f"🗑️ Delete Sub-Topic: {r['title']}", key=f"dsub_{r['id']}"): delete_lms_subtopic(r['id']); st.rerun()
        elif not mods_df.empty:
            st.info("🔒 **Step 5 Locked:** Create at least one Topic above to unlock Sub-Topics.")

# ==========================================
# TAB 3: JOBSITE CERTIFICATIONS (NEW ENTERPRISE FEATURE)
# ==========================================
with tab_certify:
    st.subheader("Log Subcontractor & Field Training")
    st.markdown(f"Register a completed module specifically for the **{active_project}** jobsite.")
    
    colA, colB = st.columns(2, gap="large")
    
    with colA:
        with st.form("certify_form", clear_on_submit=True):
            worker_name = st.text_input("Worker Full Name")
            trade_company = st.text_input("Subcontractor / Company Name")
            
            # Dynamically pull the Modules your Curriculum Builder created
            available_courses = mods_df['title'].tolist() if not mods_df.empty else ["No modules published yet"]
            selected_course = st.selectbox("Completed Module / Course", available_courses)
            
            date_completed = st.date_input("Date of Completion", value=date.today())
            st.markdown("**Competency Verification**")
            attestation = st.checkbox("I verify this worker has reviewed the material and understands the requirements.")
            
            if st.form_submit_button("💾 Issue Jobsite Certification", type="primary"):
                if worker_name and trade_company and attestation and not mods_df.empty:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("""
                        INSERT INTO lms_training_logs (project_name, course_name, worker_name, trade_company, completion_date, status) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (active_project, selected_course, worker_name, trade_company, str(date_completed), "Certified 🟢"))
                    conn.commit()
                    conn.close()
                    st.success(f"Certification successfully logged for {worker_name}.")
                    st.rerun()
                elif not attestation:
                    st.error("You must check the attestation box to issue a certification.")
                else:
                    st.warning("Worker Name and Company are required.")

    with colB:
        st.info("""
        **Enterprise Compliance Rule:**
        Field laborers and subcontractors who do not have app login credentials can have their certifications logged manually here by a Superintendent or Manager. 
        These logs are tied strictly to this project's active workspace.
        """)

# ==========================================
# TAB 4: COMPLIANCE REPORTING (MULTI-TENANT ISOLATED)
# ==========================================
with tab_logs:
    st.subheader("Jobsite Certification Ledger")
    
    conn = sqlite3.connect(DB_FILE)
    if is_admin_or_educator:
        st.caption("Admin View: Displaying training records across the entire portfolio. Use filters below to narrow down.")
        logs_df = pd.read_sql_query("SELECT project_name, worker_name, trade_company, course_name, completion_date, status FROM lms_training_logs ORDER BY completion_date DESC", conn)
    else:
        st.caption(f"Standard View: Displaying training records strictly isolated to **{active_project}**.")
        logs_df = pd.read_sql_query("SELECT project_name, worker_name, trade_company, course_name, completion_date, status FROM lms_training_logs WHERE project_name=? ORDER BY completion_date DESC", conn, params=(active_project,))
    conn.close()
    
    if not logs_df.empty:
        if is_admin_or_educator:
            filter_proj = st.selectbox("Filter by Project:", ["All Projects"] + logs_df['project_name'].unique().tolist())
            if filter_proj != "All Projects":
                logs_df = logs_df[logs_df['project_name'] == filter_proj]
                
        st.dataframe(
            logs_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "project_name": "Project Name",
                "worker_name": "Certified Worker",
                "trade_company": "Subcontractor / Trade",
                "course_name": "Training Module",
                "completion_date": "Date Completed",
                "status": "Status"
            }
        )
        st.divider()
        st.metric("Total Active Certifications", len(logs_df))
    else:
        st.info(f"No external training logs found for {active_project}.")
        