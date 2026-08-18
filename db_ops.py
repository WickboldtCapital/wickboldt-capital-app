import os
import streamlit as st
import json
import pandas as pd
import uuid
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from core_backend import hash_password

# ==========================================
# 🌐 CLOUD DATABASE CONNECTION (CACHED)
# ==========================================
@st.cache_resource
def get_db_engine():
    DB_URL = os.environ.get("DATABASE_URL")
    if not DB_URL:
        DB_URL = st.secrets["database"]["url"]
    # Initializes the connection pool exactly once to prevent memory overload
    return create_engine(DB_URL, pool_size=5, max_overflow=10, pool_timeout=30, pool_pre_ping=True)

engine = get_db_engine()

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
# 📁 PROJECT CONTROL (MULTI-TENANT ISOLATION)
# ==========================================
def ensure_project_schema():
    """Safely ensures the user_email and portfolio_name columns exist."""
    try:
        with get_transaction() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN user_email VARCHAR(255)"))
    except Exception: pass
    try:
        with get_transaction() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN portfolio_name VARCHAR(255) DEFAULT 'Master Portfolio'"))
    except Exception: pass

@st.cache_data(ttl=60)
def get_user_projects_df(user_email, role):
    """Fetches projects belonging to the user, with portfolio mapping."""
    ensure_project_schema()
    with get_read_connection() as conn: 
        if role and role.lower() == "admin":
            return pd.read_sql(text("SELECT project_id, project_name, phase, notes, user_email, COALESCE(portfolio_name, 'Master Portfolio') as portfolio_name FROM projects"), conn)
        else:
            return pd.read_sql(text("SELECT project_id, project_name, phase, notes, user_email, COALESCE(portfolio_name, 'Master Portfolio') as portfolio_name FROM projects WHERE user_email = :email"), conn, params={"email": user_email})

@st.cache_data(ttl=60)
def get_all_projects_df():
    ensure_project_schema()
    with get_read_connection() as conn: 
        return pd.read_sql(text("SELECT project_id, project_name, phase, notes, user_email, COALESCE(portfolio_name, 'Master Portfolio') as portfolio_name FROM projects"), conn)

def create_project(name, phase, notes, user_email="System", portfolio="Master Portfolio"):
    ensure_project_schema()
    try:
        with get_transaction() as conn: 
            conn.execute(text("INSERT INTO projects (project_name, phase, notes, user_email, portfolio_name) VALUES (:name, :phase, :notes, :email, :port)"), 
                         {"name": name, "phase": phase, "notes": notes, "email": user_email, "port": portfolio})
        log_audit_action(user_email, "CREATE_PROJECT", f"Created project: {name} in {portfolio}")
        st.cache_data.clear()
        return True, "Success"
    except Exception as e: 
        return False, str(e)

def delete_project(project_name, user_email="System"):
    try:
        with get_transaction() as conn:
            conn.execute(text("DELETE FROM project_milestones WHERE project_name = :name"), {"name": project_name})
            conn.execute(text("DELETE FROM projects WHERE project_name = :name"), {"name": project_name})
        log_audit_action(user_email, "DELETE_PROJECT", f"Deleted project: {project_name}")
        st.cache_data.clear()
        return True, "Success"
    except Exception as e:
        return False, str(e)

# ==========================================
# 📚 STANDALONE MASTER LIBRARY
# ==========================================
def init_library_db():
    with get_transaction() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_documents (
                doc_title TEXT PRIMARY KEY,
                doc_content TEXT
            )
        """))
        try:
            old_row = conn.execute(text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone()
            if old_row and old_row[0]:
                old_dict = json.loads(old_row[0])
                for title, content in old_dict.items():
                    conn.execute(text("""
                        INSERT INTO company_documents (doc_title, doc_content) 
                        VALUES (:t, :c) 
                        ON CONFLICT (doc_title) DO NOTHING
                    """), {"t": title, "c": content})
                conn.execute(text("DELETE FROM projects WHERE project_name='__MASTER_LIBRARY__'"))
        except Exception:
            pass

@st.cache_data(ttl=3600)
def get_library_state():
    init_library_db() 
    with get_read_connection() as conn:
        rows = conn.execute(text("SELECT doc_title, doc_content FROM company_documents")).fetchall()
        return {row[0]: row[1] for row in rows}

def save_library_state(data, user_email="System"):
    with get_transaction() as conn: 
        for title, content in data.items():
            conn.execute(text("""
                INSERT INTO company_documents (doc_title, doc_content) 
                VALUES (:t, :c) 
                ON CONFLICT (doc_title) DO UPDATE SET doc_content = EXCLUDED.doc_content
            """), {"t": title, "c": content})
    log_audit_action(user_email, "UPDATE_LIBRARY", "Batch modified library templates")
    st.cache_data.clear()

def update_library_doc(doc_title, new_text, user_email="System"):
    with get_transaction() as conn:
        conn.execute(text("""
            INSERT INTO company_documents (doc_title, doc_content) 
            VALUES (:t, :c) 
            ON CONFLICT (doc_title) DO UPDATE SET doc_content = EXCLUDED.doc_content
        """), {"t": doc_title, "c": new_text})
    log_audit_action(user_email, "UPDATE_LIBRARY", f"Modified document: {doc_title}")
    st.cache_data.clear()

# ==========================================
# ⏱️ ENTERPRISE SCHEDULING & MILESTONES
# ==========================================
def init_milestones_table():
    with get_transaction() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_milestones (
                id TEXT PRIMARY KEY,
                project_name TEXT,
                phase_category TEXT,
                task_name TEXT,
                assigned_trade TEXT,
                start_date TEXT,
                due_date TEXT,
                is_complete INTEGER DEFAULT 0,
                completed_by TEXT,
                completed_at TEXT
            )
        """))

def get_project_milestones(project_name: str):
    """Fetches all milestones for the active project from Supabase/PostgreSQL."""
    init_milestones_table()
    with get_read_connection() as conn:
        return pd.read_sql_query(
            text("SELECT * FROM project_milestones WHERE project_name=:p_name"), 
            conn, 
            params={"p_name": project_name}
        )

def add_enterprise_milestone(project_name, phase_category, task_name, assigned_trade, start_date, due_date):
    init_milestones_table()
    with get_transaction() as conn:
        conn.execute(text("""
            INSERT INTO project_milestones 
            (id, project_name, phase_category, task_name, assigned_trade, start_date, due_date, is_complete) 
            VALUES (:id, :p_name, :phase, :task, :trade, :start, :due, 0)
        """), {
            "id": str(uuid.uuid4()),
            "p_name": project_name,
            "phase": phase_category,
            "task": task_name,
            "trade": assigned_trade,
            "start": str(start_date),
            "due": str(due_date)
        })

def complete_enterprise_milestone(milestone_id, user_email):
    with get_transaction() as conn:
        conn.execute(text("""
            UPDATE project_milestones 
            SET is_complete=1, completed_by=:email, completed_at=:c_at 
            WHERE id=:id
        """), {
            "email": user_email,
            "c_at": str(date.today()),
            "id": milestone_id
        })

def delete_enterprise_milestone(milestone_id):
    with get_transaction() as conn:
        conn.execute(text("DELETE FROM project_milestones WHERE id=:id"), {"id": milestone_id})

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
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_chapters (category_id, title, description, sort_order) VALUES (:c, :t, :d, :sort)"), {"c": cat_id, "t": title, "d": desc, "sort": sort})
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
    with get_transaction() as conn: conn.execute(text("INSERT INTO lms_subtopics (topic_id, title, description, content, video_url, sort_order, attached_file_name, attached_file_data, attached_file_desc) VALUES (:t, :ti, :d, :cnt, :v, :s, :fn, :fd, :fdesc)"), {"t": top_id, "ti": title, "d": desc, "cnt": content, "v": video, "s": sort, "fn": fname, "fd": "fdesc"})
def delete_lms_subtopic(sub_id):
    with get_transaction() as conn: conn.execute(text("DELETE FROM lms_subtopics WHERE id=:id"), {"id": sub_id})

# --- PROGRESS TRACKING ---
def get_user_progress(email, table_name, column_name):
    with get_read_connection() as conn: return [r[0] for r in conn.execute(text(f"SELECT {column_name} FROM {table_name} WHERE user_email = :e"), {"e": email}).fetchall()]
def mark_progress(email, table_name, column_name, record_id):
    with get_transaction() as conn: conn.execute(text(f"INSERT INTO {table_name} (user_email, {column_name}) VALUES (:e, :id)"), {"e": email, "id": record_id})

# ==========================================
# 💰 PROFORMA & BUDGET INGESTION ENGINE
# ==========================================
def add_budget_line_item(project_name, category, vendor_name, description, qty, unit_cost, total_cost):
    """Inserts an AI-extracted bid line item into the Supabase database."""
    try:
        with get_transaction() as conn:
            # Ensure the budget table exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_budgets (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR(255),
                    category VARCHAR(100),
                    vendor_name VARCHAR(255),
                    description TEXT,
                    qty NUMERIC,
                    unit_cost NUMERIC,
                    total_cost NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert the parsed line item
            conn.execute(text("""
                INSERT INTO project_budgets (project_name, category, vendor_name, description, qty, unit_cost, total_cost)
                VALUES (:project_name, :category, :vendor_name, :description, :qty, :unit_cost, :total_cost)
            """), {
                "project_name": project_name,
                "category": category,
                "vendor_name": vendor_name,
                "description": description,
                "qty": float(qty),
                "unit_cost": float(unit_cost),
                "total_cost": float(total_cost)
            })
        return True, "Line item successfully saved to budget."
    except Exception as e:
        return False, f"Database error: {str(e)}"

def get_project_budget(project_name):
    """Retrieves all active budget line items for a specific project."""
    try:
        # Safety catch: Ensure the table exists so it doesn't crash on new projects
        with get_transaction() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_budgets (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR(255),
                    category VARCHAR(100),
                    vendor_name VARCHAR(255),
                    description TEXT,
                    qty NUMERIC,
                    unit_cost NUMERIC,
                    total_cost NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
        with get_read_connection() as conn:
            sql = text("SELECT * FROM project_budgets WHERE project_name = :p_name ORDER BY created_at DESC")
            result = conn.execute(sql, {"p_name": project_name}).fetchall()
            
            if result:
                return pd.DataFrame(result)
            else:
                return pd.DataFrame()
    except Exception as e:
        # Silently pass instead of throwing a red error box in the UI
        return pd.DataFrame()