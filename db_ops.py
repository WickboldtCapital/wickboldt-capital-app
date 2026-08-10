import sqlite3
import json
import pandas as pd
from core_backend import DB_FILE, hash_password

def get_connection():
    """Opens a connection to the database. We use this inside 'with' blocks for safety."""
    return sqlite3.connect(DB_FILE)

# ==========================================
# 🔐 USER AUTHENTICATION & MANAGEMENT
# ==========================================

def authenticate_user(email, password):
    """Returns the user's role if credentials match, otherwise returns None."""
    clean_email = email.lower().strip()
    
    # The 'with' statement guarantees the connection is closed instantly when done
    with get_connection() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE email=? AND password_hash=?", 
            (clean_email, hash_password(password))
        ).fetchone()
        
    if user:
        return user[0]
    # Master Override
    elif clean_email == "steve.wickboldt.jr@gmail.com" and password == "admin123":
        return "Admin"
    return None

def update_password(email, new_password):
    """Updates a user's password securely."""
    clean_email = email.lower().strip()
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash=? WHERE email=?", 
            (hash_password(new_password), clean_email)
        )
        conn.commit()
def get_all_users_df():
    """Returns a pandas DataFrame of all registered users."""
    with get_connection() as conn:
        return pd.read_sql("SELECT email, role FROM users", conn)

def add_new_user(email, password, role):
    """Creates a new user securely."""
    clean_email = email.lower().strip()
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", 
                (clean_email, hash_password(password), role)
            )
            conn.commit()
        return True, "Success"
    except sqlite3.IntegrityError:
        return False, "This email is already in the system."
    except Exception as e:
        return False, f"Database Error: {e}"

def update_user_role(email, new_role):
    """Updates an existing user's role."""
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE email = ?", (new_role, email))
        conn.commit()

def delete_user(email):
    """Deletes a user, with hardcoded protection for the master admin."""
    if email.lower() == "steve.wickboldt.jr@gmail.com":
        return False, "Cannot delete the master administrator account."
        
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
    return True, "User deleted successfully."

# ==========================================
# 📁 PROJECT CONTROL
# ==========================================

def get_all_projects_df():
    """Returns a pandas DataFrame of all projects."""
    with get_connection() as conn:
        return pd.read_sql("SELECT project_id, project_name, phase, notes FROM projects", conn)

def create_project(name, phase, notes):
    """Safely creates a new project and handles duplicate names."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO projects (project_name, phase, notes) VALUES (?, ?, ?)", 
                (name, phase, notes)
            )
            conn.commit()
        return True, "Success"
    except sqlite3.IntegrityError:
        return False, "A project with this name already exists."
    except Exception as e:
        return False, f"Database Error: {e}"

# ==========================================
# 📚 MASTER COMPANY LIBRARY (GOVERNANCE)
# ==========================================

def init_library_db():
    """Ensures the projects table can hold JSON library data and creates the master record."""
    with get_connection() as conn:
        try:
            conn.execute("ALTER TABLE projects ADD COLUMN project_data TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
        conn.execute("INSERT OR IGNORE INTO projects (project_name, project_data) VALUES ('__MASTER_LIBRARY__', '{}')")
        conn.commit()

def get_library_state():
    """Fetches the Master Library JSON data."""
    init_library_db() # Ensure it's initialized before fetching
    with get_connection() as conn:
        row = conn.execute("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'").fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}

def save_library_state(data):
    """Saves updates to the Master Library JSON data."""
    with get_connection() as conn:
        conn.execute("UPDATE projects SET project_data=? WHERE project_name='__MASTER_LIBRARY__'", (json.dumps(data),))
        conn.commit()
