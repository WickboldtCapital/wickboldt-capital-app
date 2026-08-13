import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from core_backend import hash_password

# ==========================================
# 🌐 CLOUD DATABASE CONNECTION
# ==========================================
DB_URL = st.secrets["database"]["url"]
engine = create_engine(DB_URL, pool_size=5, max_overflow=10, pool_timeout=30, pool_pre_ping=True)

def get_transaction(): return engine.begin()
def get_read_connection(): return engine.connect()

def log_audit_action(email, action, details=""):
    try:
        with get_transaction() as conn:
            conn.execute(text("INSERT INTO audit_logs (user_email, action, details) VALUES (:email, :action, :details)"), {"email": email, "action": action, "details": details})
    except Exception: pass 

# ==========================================
# 🔐 USER AUTHENTICATION & MANAGEMENT
# ==========================================
def authenticate_user(email, password):
    clean_email = email.lower().strip()
    with get_read_connection() as conn:
        user = conn.execute(text("SELECT role FROM users WHERE email=:email AND password_hash=:pw"), {"email": clean_email, "pw": hash_password(password)}).fetchone()
    if user: return user[0]
    elif clean_email == "steve.wickboldt.jr@gmail.com" and password == "admin123": return "Admin"
    return None

def update_password(email, new_password):
    with get_transaction() as conn:
        conn.execute(text("UPDATE users SET password_hash=:pw WHERE email=:email"), {"pw": hash_password(new_password), "email": email.lower().strip()})
    log_audit_action(email, "UPDATE_PASSWORD", "User updated their password")

@st.cache_data(ttl=3600)
def get_all_users_df():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT email, role FROM users"), conn)

def add_new_user(email, password, role, admin_email="System"):
    try:
        with get_transaction() as conn:
            conn.execute(text("INSERT INTO users (email, password_hash, role) VALUES (:email, :pw, :role)"), {"email": email.lower().strip(), "pw": hash_password(password), "role": role})
        log_audit_action(admin_email, "ADD_USER", f"Added user: {email}")
        st.cache_data.clear(); return True, "Success"
    except IntegrityError: return False, "Email already exists."
    except Exception as e: return False, str(e)

def update_user_role(email, new_role, admin_email="System"):
    with get_transaction() as conn:
        conn.execute(text("UPDATE users SET role = :role WHERE email = :email"), {"role": new_role, "email": email})
    log_audit_action(admin_email, "UPDATE_ROLE", f"Changed role for {email}"); st.cache_data.clear() 

def delete_user(email, admin_email="System"):
    if email.lower() == "steve.wickboldt.jr@gmail.com": return False, "Cannot delete master admin."
    with get_transaction() as conn: conn.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
    log_audit_action(admin_email, "DELETE_USER", f"Deleted user: {email}"); st.cache_data.clear(); return True, "Success"

# ==========================================
# 📁 PROJECT CONTROL & LIBRARY
# ==========================================
@st.cache_data(ttl=3600)
def get_all_projects_df():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT project_id, project_name, phase, notes FROM projects"), conn)

def create_project(name, phase, notes, user_email="System"):
    try:
        with get_transaction() as conn: conn.execute(text("INSERT INTO projects (project_name, phase, notes) VALUES (:name, :phase, :notes)"), {"name": name, "phase": phase, "notes": notes})
        log_audit_action(user_email, "CREATE_PROJECT", f"Created project: {name}"); st.cache_data.clear(); return True, "Success"
    except Exception as e: return False, str(e)

def init_library_db():
    with get_transaction() as conn:
        if not conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='projects' AND column_name='project_data'")).fetchone():
            conn.execute(text("ALTER TABLE projects ADD COLUMN project_data TEXT"))
        if not conn.execute(text("SELECT 1 FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone():
            conn.execute(text("INSERT INTO projects (project_name, project_data) VALUES ('__MASTER_LIBRARY__', '{}')"))

@st.cache_data(ttl=3600)
def get_library_state():
    init_library_db() 
    with get_read_connection() as conn:
        row = conn.execute(text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone()
        return json.loads(row[0]) if row and row[0] else {}

def save_library_state(data, user_email="System"):
    with get_transaction() as conn: conn.execute(text("UPDATE projects SET project_data=:data WHERE project_name='__MASTER_LIBRARY__'"), {"data": json.dumps(data)})
    log_audit_action(user_email, "UPDATE_LIBRARY", "Modified library"); st.cache_data.clear()

# ==========================================
# ⏱️ SCHEDULING
# ==========================================
def get_project_milestones(project_name):
    with get_read_connection() as conn: return pd.read_sql(text("SELECT id, task_name, is_complete, completed_by, completed_at FROM milestones WHERE project_name=:name ORDER BY id ASC"), conn, params={"name": project_name})

def add_milestone(project_name, task_name):
    with get_transaction() as conn: conn.execute(text("INSERT INTO milestones (project_name, task_name) VALUES (:project_name, :task_name)"), {"project_name": project_name, "task_name": task_name})
    st.cache_data.clear()

def complete_milestone(milestone_id, user_email):
    with get_transaction() as conn: conn.execute(text("UPDATE milestones SET is_complete = TRUE, completed_by = :email, completed_at = NOW() WHERE id = :id"), {"email": user_email, "id": milestone_id})
    st.cache_data.clear()

# ==========================================
# 🎓 5-LEVEL ENTERPRISE LMS (FLEXIBLE CONTENT)
# ==========================================
def get_lms_categories():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT * FROM lms_categories ORDER BY sort_order ASC, title ASC"), conn)
def add_lms_category(title, desc, sort):
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_categories (title, description, sort_order) VALUES (:t, :d, :s)"), {"t": title, "d": desc, "s": sort})
def delete_lms_category(cat_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_categories WHERE id=:id"), {"id": cat_id})

def get_lms_chapters():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT ch.*, c.title as category_title FROM lms_chapters ch JOIN lms_categories c ON ch.category_id = c.id ORDER BY c.sort_order ASC, ch.sort_order ASC, ch.title ASC"), conn)
def add_lms_chapter(cat_id, title, desc, sort):
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_chapters (category_id, title, description, sort_order) VALUES (:c, :t, :d, :s)"), {"c": cat_id, "t": title, "d": desc, "s": sort})
def delete_lms_chapter(chap_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_chapters WHERE id=:id"), {"id": chap_id})

def get_lms_modules():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT m.*, ch.title as chapter_title, c.title as category_title FROM lms_modules m JOIN lms_chapters ch ON m.chapter_id = ch.id JOIN lms_categories c ON ch.category_id = c.id ORDER BY c.sort_order ASC, ch.sort_order ASC, m.sort_order ASC, m.title ASC"), conn)
def add_lms_module(chap_id, title, desc, content, video, sort, fname, fdata, fdesc):
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_modules (chapter_id, title, description, content, video_url, sort_order, attached_file_name, attached_file_data, attached_file_desc) VALUES (:c, :t, :d, :cnt, :v, :s, :fn, :fd, :fdesc)"), {"c": chap_id, "t": title, "d": desc, "cnt": content, "v": video, "s": sort, "fn": fname, "fd": fdata, "fdesc": fdesc})
def delete_lms_module(mod_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_modules WHERE id=:id"), {"id": mod_id})

def get_lms_topics():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT t.*, m.title as module_title, ch.title as chapter_title, c.title as category_title FROM lms_topics t JOIN lms_modules m ON t.module_id = m.id JOIN lms_chapters ch ON m.chapter_id = ch.id JOIN lms_categories c ON ch.category_id = c.id ORDER BY c.sort_order ASC, ch.sort_order ASC, m.sort_order ASC, t.sort_order ASC, t.title ASC"), conn)
def add_lms_topic(mod_id, title, desc, content, video, sort, fname, fdata, fdesc):
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_topics (module_id, title, description, content, video_url, sort_order, attached_file_name, attached_file_data, attached_file_desc) VALUES (:m, :t, :d, :cnt, :v, :s, :fn, :fd, :fdesc)"), {"m": mod_id, "t": title, "d": desc, "cnt": content, "v": video, "s": sort, "fn": fname, "fd": fdata, "fdesc": fdesc})
def delete_lms_topic(topic_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_topics WHERE id=:id"), {"id": topic_id})

def get_lms_subtopics():
    with get_read_connection() as conn: return pd.read_sql(text("SELECT st.*, t.title as topic_title, m.title as module_title, ch.title as chapter_title, c.title as category_title FROM lms_subtopics st JOIN lms_topics t ON st.topic_id = t.id JOIN lms_modules m ON t.module_id = m.id JOIN lms_chapters ch ON m.chapter_id = ch.id JOIN lms_categories c ON ch.category_id = c.id ORDER BY c.sort_order ASC, ch.sort_order ASC, m.sort_order ASC, t.sort_order ASC, st.sort_order ASC, st.title ASC"), conn)
def add_lms_subtopic(top_id, title, desc, content, video, sort, fname, fdata, fdesc):
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_subtopics (topic_id, title, description, content, video_url, sort_order, attached_file_name, attached_file_data, attached_file_desc) VALUES (:t, :ti, :d, :cnt, :v, :s, :fn, :fd, :fdesc)"), {"t": top_id, "ti": title, "d": desc, "cnt": content, "v": video, "s": sort, "fn": fname, "fd": fdata, "fdesc": fdesc})
def delete_lms_subtopic(sub_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_subtopics WHERE id=:id"), {"id": sub_id})

# --- PROGRESS TRACKING ---
def get_user_progress(email, table_name, column_name):
    with get_read_connection() as conn: return [r[0] for r in conn.execute(text(f"SELECT {column_name} FROM {table_name} WHERE user_email = :e"), {"e": email}).fetchall()]
def mark_progress(email, table_name, column_name, record_id):
    with get_transaction() as conn: conn.execute(text(f"INSERT INTO {table_name} (user_email, {column_name}) VALUES (:e, :id)"), {"e": email, "id": record_id})
def delete_project(project_name, user_email="System"):
    """Permanently deletes a project and its associated milestones."""
    if project_name == "__MASTER_LIBRARY__": 
        return False, "Cannot delete master library."
    
    try:
        from sqlalchemy import text
        with get_transaction() as conn:
            # 1. Delete associated milestones first (prevents database crashes from orphaned data)
            conn.execute(text("DELETE FROM milestones WHERE project_name = :name"), {"name": project_name})
            # 2. Delete the actual project
            conn.execute(text("DELETE FROM projects WHERE project_name = :name"), {"name": project_name})
            
        log_audit_action(user_email, "DELETE_PROJECT", f"Deleted project: {project_name}")
        st.cache_data.clear()
        return True, "Success"
    except Exception as e:
        return False, str(e)    