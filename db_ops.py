import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from core_backend import hash_password

# ==========================================
# 🌐 CLOUD DATABASE CONNECTION (SUPABASE)
# ==========================================

DB_URL = st.secrets["database"]["url"]

engine = create_engine(
    DB_URL,
    pool_size=5,          
    max_overflow=10,      
    pool_timeout=30,      
    pool_pre_ping=True    
)

def get_transaction():
    return engine.begin()

def get_read_connection():
    return engine.connect()

# ==========================================
# 🕵️ AUDIT LOGGING LEDGER
# ==========================================

def log_audit_action(email, action, details=""):
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO audit_logs (user_email, action, details) VALUES (:email, :action, :details)")
            conn.execute(query, {"email": email, "action": action, "details": details})
    except Exception:
        pass 

# ==========================================
# 🔐 USER AUTHENTICATION & MANAGEMENT
# ==========================================

def authenticate_user(email, password):
    clean_email = email.lower().strip()
    with get_read_connection() as conn:
        query = text("SELECT role FROM users WHERE email=:email AND password_hash=:pw")
        user = conn.execute(query, {"email": clean_email, "pw": hash_password(password)}).fetchone()
        
    if user:
        return user[0]
    elif clean_email == "steve.wickboldt.jr@gmail.com" and password == "admin123":
        return "Admin"
    return None

def update_password(email, new_password):
    clean_email = email.lower().strip()
    with get_transaction() as conn:
        query = text("UPDATE users SET password_hash=:pw WHERE email=:email")
        conn.execute(query, {"pw": hash_password(new_password), "email": clean_email})
    log_audit_action(email, "UPDATE_PASSWORD", "User updated their password")

@st.cache_data(ttl=3600)
def get_all_users_df():
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT email, role FROM users"), conn)

def add_new_user(email, password, role, admin_email="System"):
    clean_email = email.lower().strip()
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO users (email, password_hash, role) VALUES (:email, :pw, :role)")
            conn.execute(query, {"email": clean_email, "pw": hash_password(password), "role": role})
        log_audit_action(admin_email, "ADD_USER", f"Added new user: {clean_email} with role {role}")
        st.cache_data.clear() 
        return True, "Success"
    except IntegrityError:
        return False, "This email is already in the system."
    except Exception as e:
        return False, f"Database Error: {e}"

def update_user_role(email, new_role, admin_email="System"):
    with get_transaction() as conn:
        query = text("UPDATE users SET role = :role WHERE email = :email")
        conn.execute(query, {"role": new_role, "email": email})
    log_audit_action(admin_email, "UPDATE_ROLE", f"Changed role for {email} to {new_role}")
    st.cache_data.clear() 

def delete_user(email, admin_email="System"):
    if email.lower() == "steve.wickboldt.jr@gmail.com":
        return False, "Cannot delete the master administrator account."
    with get_transaction() as conn:
        query = text("DELETE FROM users WHERE email = :email")
        conn.execute(query, {"email": email})
    log_audit_action(admin_email, "DELETE_USER", f"Deleted user: {email}")
    st.cache_data.clear() 
    return True, "User deleted successfully."

# ==========================================
# 📁 PROJECT CONTROL
# ==========================================

@st.cache_data(ttl=3600)
def get_all_projects_df():
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT project_id, project_name, phase, notes FROM projects"), conn)

def create_project(name, phase, notes, user_email="System"):
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO projects (project_name, phase, notes) VALUES (:name, :phase, :notes)")
            conn.execute(query, {"name": name, "phase": phase, "notes": notes})
        log_audit_action(user_email, "CREATE_PROJECT", f"Created project: {name}")
        st.cache_data.clear() 
        return True, "Success"
    except IntegrityError:
        return False, "A project with this name already exists."
    except Exception as e:
        return False, f"Database Error: {e}"

# ==========================================
# 📚 MASTER COMPANY LIBRARY (GOVERNANCE)
# ==========================================

def init_library_db():
    with get_transaction() as conn:
        column_check = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='projects' AND column_name='project_data'")).fetchone()
        if not column_check:
            conn.execute(text("ALTER TABLE projects ADD COLUMN project_data TEXT"))
        row_check = conn.execute(text("SELECT 1 FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone()
        if not row_check:
            conn.execute(text("INSERT INTO projects (project_name, project_data) VALUES ('__MASTER_LIBRARY__', '{}')"))

@st.cache_data(ttl=3600)
def get_library_state():
    init_library_db() 
    with get_read_connection() as conn:
        query = text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")
        row = conn.execute(query).fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}

def save_library_state(data, user_email="System"):
    with get_transaction() as conn:
        query = text("UPDATE projects SET project_data=:data WHERE project_name='__MASTER_LIBRARY__'")
        conn.execute(query, {"data": json.dumps(data)})
    log_audit_action(user_email, "UPDATE_LIBRARY", "Modified the master company library")
    st.cache_data.clear()

# ==========================================
# ⏱️ SCHEDULING & MILESTONES
# ==========================================

def get_project_milestones(project_name):
    with get_read_connection() as conn:
        query = text("SELECT id, task_name, is_complete, completed_by, completed_at FROM milestones WHERE project_name=:name ORDER BY id ASC")
        return pd.read_sql(query, conn, params={"name": project_name})

def add_milestone(project_name, task_name):
    with get_transaction() as conn:
        query = text("INSERT INTO milestones (project_name, task_name) VALUES (:project_name, :task_name)")
        conn.execute(query, {"project_name": project_name, "task_name": task_name})
    st.cache_data.clear()

def complete_milestone(milestone_id, user_email):
    with get_transaction() as conn:
        query = text("UPDATE milestones SET is_complete = TRUE, completed_by = :email, completed_at = NOW() WHERE id = :id")
        conn.execute(query, {"email": user_email, "id": milestone_id})
    st.cache_data.clear()


# ==========================================
# 🎓 ENTERPRISE LMS (RELATIONAL)
# ==========================================

def get_lms_categories():
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT * FROM lms_categories ORDER BY sort_order ASC, title ASC"), conn)

def add_lms_category(title, description, sort_order):
    with get_transaction() as conn:
        conn.execute(text("INSERT INTO lms_categories (title, description, sort_order) VALUES (:t, :d, :s)"), {"t": title, "d": description, "s": sort_order})

def delete_lms_category(cat_id):
    with get_transaction() as conn:
        conn.execute(text("DELETE FROM lms_categories WHERE id=:id"), {"id": cat_id})

def get_lms_chapters():
    with get_read_connection() as conn:
        return pd.read_sql(text("""
            SELECT ch.*, c.title as category_title 
            FROM lms_chapters ch 
            JOIN lms_categories c ON ch.category_id = c.id 
            ORDER BY c.sort_order ASC, ch.sort_order ASC, ch.title ASC
        """), conn)

def add_lms_chapter(cat_id, title, description, sort_order):
    with get_transaction() as conn:
        conn.execute(text("INSERT INTO lms_chapters (category_id, title, description, sort_order) VALUES (:c, :t, :d, :s)"), {"c": cat_id, "t": title, "d": description, "s": sort_order})

def delete_lms_chapter(chap_id):
    with get_transaction() as conn:
        conn.execute(text("DELETE FROM lms_chapters WHERE id=:id"), {"id": chap_id})

def get_lms_modules():
    with get_read_connection() as conn:
        return pd.read_sql(text("""
            SELECT m.*, ch.title as chapter_title, c.id as category_id, c.title as category_title 
            FROM lms_modules m 
            JOIN lms_chapters ch ON m.chapter_id = ch.id 
            JOIN lms_categories c ON ch.category_id = c.id 
            ORDER BY c.sort_order ASC, ch.sort_order ASC, m.sort_order ASC, m.title ASC
        """), conn)

def add_lms_module(chap_id, title, desc, content, video, sort, fname, fdata, fdesc):
    with get_transaction() as conn:
        conn.execute(text("""
            INSERT INTO lms_modules (chapter_id, title, description, content, video_url, sort_order, attached_file_name, attached_file_data, attached_file_desc) 
            VALUES (:c, :t, :d, :cnt, :v, :s, :fn, :fd, :fdesc)
        """), {"c": chap_id, "t": title, "d": desc, "cnt": content, "v": video, "s": sort, "fn": fname, "fd": fdata, "fdesc": fdesc})

def delete_lms_module(mod_id):
    with get_transaction() as conn:
        conn.execute(text("DELETE FROM lms_modules WHERE id=:id"), {"id": mod_id})

def get_user_completed_modules(email):
    with get_read_connection() as conn:
        res = conn.execute(text("SELECT module_id FROM lms_user_progress WHERE user_email = :e"), {"e": email}).fetchall()
        return [r[0] for r in res]

def mark_module_completed(email, module_id):
    with get_transaction() as conn:
        conn.execute(text("INSERT INTO lms_user_progress (user_email, module_id) VALUES (:e, :m)"), {"e": email, "m": module_id})