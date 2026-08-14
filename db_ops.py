import os
import streamlit as st
import json
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
from core_backend import hash_password

# ==========================================
# 🌐 CLOUD DATABASE CONNECTION
# ==========================================
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    DB_URL = st.secrets["database"]["url"]

engine = create_engine(DB_URL, pool_size=5, max_overflow=10, pool_timeout=30, pool_pre_ping=True)

def get_transaction(): return engine.begin()
def get_read_connection(): return engine.connect()

def log_audit_action(email, action, details=""):
    try:
        with get_transaction() as conn:
            conn.execute(text("INSERT INTO audit_logs (user_email, action, details) VALUES (:email, :action, :details)"), {"email": email, "action": action, "details": details})
    except Exception: pass 

# (The rest of your code like user auth and project control goes below this)