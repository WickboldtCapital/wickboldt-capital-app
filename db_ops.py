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

# Create the master engine that manages all database connections
engine = create_engine(DB_URL)

def get_transaction():
    """Opens a connection that auto-commits on success and rolls back on failure."""
    return engine.begin()

def get_read_connection():
    """Opens a basic connection (best for Pandas DataFrames)."""
    return engine.connect()

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

def get_all_users_df():
    """Returns a pandas DataFrame of all registered users."""
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT email, role FROM users"), conn)

def add_new_user(email, password, role):
    """Creates a new user securely."""
    clean_email = email.lower().strip()
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO users (email, password_hash, role) VALUES (:email, :pw, :role)")
            conn.execute(query, {"email": clean_email, "pw": hash_password(password), "role": role})
        return True, "Success"
    except IntegrityError:
        return False, "This email is already in the system."
    except Exception as e:
        return False, f"Database Error: {e}"

def update_user_role(email, new_role):
    """Updates an existing user's role."""
    with get_transaction() as conn:
        query = text("UPDATE users SET role = :role WHERE email = :email")
        conn.execute(query, {"role": new_role, "email": email})

def delete_user(email):
    """Deletes a user, with hardcoded protection for the master admin."""
    if email.lower() == "steve.wickboldt.jr@gmail.com":
        return False, "Cannot delete the master administrator account."
        
    with get_transaction() as conn:
        query = text("DELETE FROM users WHERE email = :email")
        conn.execute(query, {"email": email})
    return True, "User deleted successfully."

# ==========================================
# 📁 PROJECT CONTROL
# ==========================================

def get_all_projects_df():
    """Returns a pandas DataFrame of all projects."""
    with get_read_connection() as conn:
        return pd.read_sql(text("SELECT project_id, project_name, phase, notes FROM projects"), conn)

def create_project(name, phase, notes):
    """Safely creates a new project and handles duplicate names."""
    try:
        with get_transaction() as conn:
            query = text("INSERT INTO projects (project_name, phase, notes) VALUES (:name, :phase, :notes)")
            conn.execute(query, {"name": name, "phase": phase, "notes": notes})
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

def get_library_state():
    """Fetches the Master Library JSON data."""
    init_library_db() 
    with get_read_connection() as conn:
        query = text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")
        row = conn.execute(query).fetchone()
        
        if row and row[0]:
            return json.loads(row[0])
        return {}

def save_library_state(data):
    """Saves updates to the Master Library JSON data."""
    with get_transaction() as conn:
        query = text("UPDATE projects SET project_data=:data WHERE project_name='__MASTER_LIBRARY__'")
        conn.execute(query, {"data": json.dumps(data)})