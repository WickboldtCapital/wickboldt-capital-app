import io
import json
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

def get_workspace_services():
    """Authenticates the Service Account and returns Drive and Docs service objects."""
    # Define the scopes required to read and write to Drive and Docs
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    
    # Safely load the raw JSON string from Streamlit secrets or Railway Env Vars
    creds_dict = json.loads(st.secrets["GCP_JSON"])
    
    creds = Credentials.from_service_account_info(
        creds_dict, 
        scopes=SCOPES
    )
    
    # Build the service objects for Drive and Docs
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    
    return drive_service, docs_service

def read_google_doc(document_id):
    """Fetches and reads the text of a Google Doc using its ID."""
    try:
        _, docs_service = get_workspace_services()
        doc = docs_service.documents().get(documentId=document_id).execute()
        
        text_content = ""
        for element in doc.get('body').get('content'):
            if 'paragraph' in element:
                for p_element in element.get('paragraph').get('elements'):
                    if 'textRun' in p_element:
                        text_content += p_element.get('textRun').get('content')
                        
        return text_content
    except Exception as e:
        return f"Error reading document: {e}"

def upload_pdf_to_drive(file_bytes, filename, folder_id):
    """Uploads a generated PDF byte stream directly to the specified Google Drive folder."""
    try:
        drive_service, _ = get_workspace_services()
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf', resumable=True)
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return True, file.get('id')
    except Exception as e:
        return False, str(e)

def list_drive_contents(folder_id):
    """Fetches all files and subfolders inside a specific Google Drive folder."""
    try:
        drive_service, _ = get_workspace_services()
        
        # Query for items inside the target folder that are not in the trash
        query = f"'{folder_id}' in parents and trashed = false"
        
        # Order by folder first, then alphabetical name
        results = drive_service.files().list(
            q=query, 
            fields="files(id, name, mimeType)", 
            orderBy="folder, name"
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        return [{"name": f"Error loading folder: {str(e)}", "mimeType": "error"}]
    