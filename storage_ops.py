import os
import streamlit as st
from supabase import create_client, Client

# Initialize the Supabase Client Safely
@st.cache_resource
def get_supabase_client():
    # 1. Try to get keys from Railway Environment Variables first
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # 2. Fallback to local secrets.toml if running on your PC
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except Exception:
            pass # Fail cleanly if no keys are found
            
    # 3. Connect if keys exist, otherwise return None
    if url and key:
        return create_client(url, key)
    
    return None

supabase = get_supabase_client()
BUCKET_NAME = "project_documents"

def upload_document(file_name, file_bytes, content_type):
    """Uploads a file directly to the secure bucket."""
    if supabase is None:
        return False, "System Error: Supabase credentials are missing or invalid."
        
    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            file=file_bytes,
            path=file_name,
            file_options={"content-type": content_type}
        )
        return True, "Upload successful."
    except Exception as e:
        return False, f"Upload Error: {e}"

def get_secure_url(file_name, expires_in=3600):
    """Generates a temporary, self-destructing URL (default 1 hour)."""
    if supabase is None:
        return None
        
    try:
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(file_name, expires_in)
        return response.get("signedURL")
    except Exception:
        return None

def list_documents():
    """Returns a list of all files currently in the secure bucket."""
    if supabase is None:
        return []
        
    try:
        files = supabase.storage.from_(BUCKET_NAME).list()
        # Filter out hidden system files
        return [f for f in files if f['name'] != '.emptyFolderPlaceholder']
    except Exception:
        return []