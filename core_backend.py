import sqlite3
import hashlib
import os
import shutil
import base64
import streamlit as st
from datetime import datetime

DB_FILE = "wickboldt_projects.db"
BACKUP_DIR = "backups"

def auto_backup_db():
    """Automatically backs up the database file."""
    if os.path.exists(DB_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(DB_FILE, os.path.join(BACKUP_DIR, f"wickboldt_projects_{timestamp}.db"))

def hash_password(password):
    """Encrypts passwords for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

@st.cache_data
def get_logo_html():
    """Fetches and encodes the corporate logo, wrapping it in a clean presentation badge."""
    logo_filename = "logo.svg" if os.path.exists("logo.svg") else "logo.png"
    if os.path.exists(logo_filename):
        with open(logo_filename, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        ext = "svg+xml" if logo_filename.endswith(".svg") else "png"
        
        # Wrapped in a rounded white badge with a subtle shadow so non-transparent logos look intentional
        return f'''
        <div style="background-color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
            <img src="data:image/{ext};base64,{encoded}" width="200">
        </div>
        '''
    
    # Fallback text if no image exists
    return '''
    <div style="background-color: #ffffff; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
        <h2 style="color: #002D62; margin-bottom: 0;">Wickboldt Capital</h2>
        <p style="color: #D4AF37; font-style: italic; font-weight: bold; margin-top: 5px;">Today's Foundation. Tomorrow's Legacy.</p>
    </div>
    '''

def init_db():
    """Initializes standard tables and creates the master admin account."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password_hash TEXT, role TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS projects (project_id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT UNIQUE)")
    for col in [("phase", "TEXT"), ("notes", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col[0]} {col[1]}")
        except sqlite3.OperationalError:
            pass
    cursor.execute("INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, ?)", 
                   ("steve.wickboldt.jr@gmail.com", hash_password("admin123"), "Admin"))
    conn.commit()
    conn.close()

def inject_custom_theme():
    """Injects custom CSS to enforce a Royal Blue sidebar, White text, and Gold Active Tab styling."""
    st.markdown("""
    <style>
    /* 1. Force the entire Sidebar Background to Royal Blue */
    [data-testid="stSidebar"] {
        background-color: #002D62 !important;
    }

    /* 2. Force the sidebar navigation links to crisp white */
    [data-testid="stSidebarNav"] span {
        color: #FFFFFF !important;
        font-size: 15px !important;
    }
    
    /* Force standard text (like "Logged in as") in the sidebar to white */
    [data-testid="stSidebar"] .stMarkdown p {
        color: #FFFFFF !important;
    }
    
    /* 3. Style the Active/Selected Tab with a Gold highlight */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: rgba(212, 175, 55, 0.15) !important;
        border-left: 4px solid #D4AF37 !important;
        border-radius: 0px 8px 8px 0px !important;
    }
    
    /* 4. Make the text of the Active Tab Gold */
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #D4AF37 !important; 
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)