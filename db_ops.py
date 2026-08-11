import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from core_backend import hash_password

# ==========================================
# 🌐 CLOUD DATABASE CONNECTION (SUPABASE)
# ==========================================

# Grabs the secure connection string from .streamlit/secrets.toml
DB_URL = st.secrets["database"]["url"]

# Create the master engine with Enterprise Connection Pooling
engine = create_engine(
    DB_URL,
    pool_size=5,          # Keep 5 core connections open and ready
    max_overflow=10,      # Allow up to 10 extra temporary connections during traffic spikes
    pool_timeout=30,      # Wait 30 seconds before failing if the pool is full
    pool_pre_ping=True    # Quietly test the connection before using it to prevent "dropped connection" errors
)

def get_transaction():
    """Opens a connection that auto-commits on success and rolls back on failure."""
    return engine.begin()

def get_read_connection():
    """Opens a basic connection (best for Pandas DataFrames)."""
    return engine.connect()

# ==========================================
# 🕵️ AUDIT LOGGING LEDGER
# ==========================================

def log_audit_action(email, action, details=""):
    """Silently writes an action to the hidden audit ledger."""
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO audit_logs (user_email, action, details) VALUES (:email, :action, :details)")
            conn.execute(query, {"email": email, "action": action, "details": details})
    except Exception:
        pass # We fail silently here so a logging glitch never crashes the main app


# ==========================================
# 🔐 USER AUTHENTICATION & MANAGEMENT
# ==========================================

def authenticate_user(email, password):
    """Returns the user's role if credentials match, otherwise returns None."""
    clean_email = email.lower().strip()
    
    with get_read_connection() as conn:
        query = text("SELECT role FROM users WHERE email=:email AND password_hash=:pw")
        user = conn.execute(query, {"email": clean_email, "pw": hash_password(password)}).fetchone()
        
    if user:
        return user[0]
    # Master Override
    elif clean_email == "steve.wickboldt.jr@gmail.com" and password == "admin123":
        return "Admin"
    return None

def update_password(email, new_password):
    """Updates a user's password securely."""
    clean_email = email.lower().strip()
    with get_transaction() as conn:
        query = text("UPDATE users SET password_hash=:pw WHERE email=:email")
        conn.execute(query, {"pw": hash_password(new_password), "email": clean_email})
    
    log_audit_action(email, "UPDATE_PASSWORD", "User updated their password")

@st.cache_data(ttl=3600)
def get_all_users_df():
    """Returns a pandas DataFrame of all registered users. CACHED for performance."""
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT email, role FROM users"), conn)

def add_new_user(email, password, role, admin_email="System"):
    """Creates a new user securely."""
    clean_email = email.lower().strip()
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO users (email, password_hash, role) VALUES (:email, :pw, :role)")
            conn.execute(query, {"email": clean_email, "pw": hash_password(password), "role": role})
        
        log_audit_action(admin_email, "ADD_USER", f"Added new user: {clean_email} with role {role}")
        st.cache_data.clear() # Clear cache to refresh the user list
        return True, "Success"
    except IntegrityError:
        return False, "This email is already in the system."
    except Exception as e:
        return False, f"Database Error: {e}"

def update_user_role(email, new_role, admin_email="System"):
    """Updates an existing user's role."""
    with get_transaction() as conn:
        query = text("UPDATE users SET role = :role WHERE email = :email")
        conn.execute(query, {"role": new_role, "email": email})
    
    log_audit_action(admin_email, "UPDATE_ROLE", f"Changed role for {email} to {new_role}")
    st.cache_data.clear() # Clear cache to show updated roles

def delete_user(email, admin_email="System"):
    """Deletes a user, with hardcoded protection for the master admin."""
    if email.lower() == "steve.wickboldt.jr@gmail.com":
        return False, "Cannot delete the master administrator account."
        
    with get_transaction() as conn:
        query = text("DELETE FROM users WHERE email = :email")
        conn.execute(query, {"email": email})
        
    log_audit_action(admin_email, "DELETE_USER", f"Deleted user: {email}")
    st.cache_data.clear() # Clear cache to remove user from lists
    return True, "User deleted successfully."


# ==========================================
# 📁 PROJECT CONTROL
# ==========================================

@st.cache_data(ttl=3600)
def get_all_projects_df():
    """Returns a pandas DataFrame of all projects. CACHED for performance."""
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT project_id, project_name, phase, notes FROM projects"), conn)

def create_project(name, phase, notes, user_email="System"):
    """Safely creates a new project and handles duplicate names."""
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO projects (project_name, phase, notes) VALUES (:name, :phase, :notes)")
            conn.execute(query, {"name": name, "phase": phase, "notes": notes})
        
        log_audit_action(user_email, "CREATE_PROJECT", f"Created project: {name} in {phase}")
        st.cache_data.clear() # Clear cache to show the new project instantly
        return True, "Success"
    except IntegrityError:
        return False, "A project with this name already exists."
    except Exception as e:
        return False, f"Database Error: {e}"


# ==========================================
# 📚 MASTER COMPANY LIBRARY (GOVERNANCE)
# ==========================================

def init_library_db():
    """Ensures the projects table can hold JSON library data and creates the master record."""
    with get_transaction() as conn:
        # Check if the column exists by asking Postgres directly
        column_check = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='projects' AND column_name='project_data'
        """)).fetchone()
        
        # If column does not exist, create it
        if not column_check:
            conn.execute(text("ALTER TABLE projects ADD COLUMN project_data TEXT"))
            
        # Check if master library row exists
        row_check = conn.execute(text("SELECT 1 FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone()
        
        # If it doesn't exist, insert it
        if not row_check:
            conn.execute(text("INSERT INTO projects (project_name, project_data) VALUES ('__MASTER_LIBRARY__', '{}')"))

@st.cache_data(ttl=3600)
def get_library_state():
    """Fetches the Master Library JSON data. CACHED for performance."""
    init_library_db() 
    with get_read_connection() as conn:
        query = text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")
        row = conn.execute(query).fetchone()
        
        if row and row[0]:
            return json.loads(row[0])
        return {}

def save_library_state(data, user_email="System"):
    """Saves updates to the Master Library JSON data."""
    with get_transaction() as conn:
        query = text("UPDATE projects SET project_data=:data WHERE project_name='__MASTER_LIBRARY__'")
        conn.execute(query, {"data": json.dumps(data)})
        
    log_audit_action(user_email, "UPDATE_LIBRARY", "Modified the master company library")
    st.cache_data.clear() # Clear cache so the UI reflects the updated library

# ==========================================
# ⏱️ SCHEDULING & MILESTONES
# ==========================================

def get_project_milestones(project_name):
    """Fetches all milestones for the active project."""
    with get_read_connection() as conn:
        query = text("SELECT id, task_name, is_complete, completed_by, completed_at FROM milestones WHERE project_name=:name ORDER BY id ASC")
        return pd.read_sql(query, conn, params={"name": project_name})

def add_milestone(project_name, task_name):
    """Adds a new pending milestone to a project."""
    with get_transaction() as conn:
        query = text("INSERT INTO milestones (project_name, task_name) VALUES (:project_name, :task_name)")
        conn.execute(query, {"project_name": project_name, "task_name": task_name})
    st.cache_data.clear()

def complete_milestone(milestone_id, user_email):
    """Marks a milestone as complete and logs who did it."""
    with get_transaction() as conn:
        query = text("""
            UPDATE milestones 
            SET is_complete = TRUE, completed_by = :email, completed_at = NOW() 
            WHERE id = :id
        """)
        conn.execute(query, {"email": user_email, "id": milestone_id})
    
    log_audit_action(user_email, "MILESTONE_COMPLETED", f"Completed milestone ID {milestone_id}")
    st.cache_data.clear()