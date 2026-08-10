import streamlit as st
import re
import io
import urllib.parse
from db_ops import get_library_state, save_library_state
# Imports the data blocks safely
from governance_data import SEED_TEXT_DB, FOLDER_STRUCTURE

# --- RICH TEXT EDITOR & PDF ENGINE ---
try:
    from streamlit_quill import st_quill
    HAS_QUILL = True
except ImportError:
    HAS_QUILL = False

try:
    from xhtml2pdf import pisa
    HAS_PDF_ENGINE = True
except ImportError:
    HAS_PDF_ENGINE = False

if not st.session_state.get("active_project"):
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# --- HEADER STYLING ---
st.markdown("### 🏢 Wickboldt Capital: Master Company Library")
st.markdown("Central repository containing company-wide governance procedures and master specifications.")

if st.session_state.get("role") == "Admin":
    st.success("🔓 **Administrator Mode:** You have full read/write access to modify the database.")
else:
    st.info("🔒 **Viewing Mode:** Read-only access. Admin login required to edit.")

st.write("")
col1, col2 = st.columns([2, 1])
search_query = col1.text_input("🔍 Search Master Library...").lower()
sort_method = col2.selectbox("Sort View By", ["Folder Structure", "Date Modified (Newest)", "Alphabetical (A-Z)"])
st.markdown("---")

# ==========================================
# 🔄 DATABASE AUTO-SYNC
# ==========================================
db_library = get_library_state()
needs_save = False

# If the DB is missing documents, force-add them!
for doc_key, doc_content in SEED_TEXT_DB.items():
    if doc_key not in db_library:
        db_library[doc_key] = doc_content
        needs_save = True

# Save the full documents back to the database if any were added
if needs_save:
    save_library_state(db_library)

# ==========================================
# 🛠️ ADMIN CONTROL PANEL
# ==========================================
if st.session_state.get("role") == "Admin":
    with st.expander("🛠️ Admin Document Editor"):
        doc_to_edit = st.selectbox("Select Document to Edit:", list(db_library.keys()))
        if HAS_QUILL:
            new_content = st_quill(value=db_library.get(doc_to_edit, ""), html=True, key=f"quill_{doc_to_edit}")
        else:
            new_content = st.text_area("Document Content:", value=db_library.get(doc_to_edit, ""), height=350)
            
        if st.button("💾 Save Changes to Master Database"):
            db_library[doc_to_edit] = new_content
            save_library_state(db_library)
            st.success(f"Successfully updated {doc_to_edit}!")
            st.rerun()
    st.markdown("---")

# ==========================================
# 🛠️ PDF GENERATOR 
# ==========================================
def generate_pro_pdf(title, date, content):
    if not HAS_PDF_ENGINE: return None
    html_template = f"""
    <html>
    <head>
        <style>
            @page {{ margin: 2cm; }}
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px; color: #333; line-height: 1.5; }}
            h2 {{ color: #002D62; border-bottom: 2px solid #D4AF37; padding-bottom: 5px; }}
            .meta {{ font-size: 10px; color: #666; margin-bottom: 25px; }}
        </style>
    </head>
    <body>
        <h2>WICKBOLDT CAPITAL - MASTER SPECIFICATION</h2>
        <div class="meta"><b>Document:</b> {title}<br><b>Date Published:</b> {date}</div>
        <div class="content">{content}</div>
    </body>
    </html>
    """
    result_bytes = io.BytesIO()
    if pisa.CreatePDF(html_template, dest=result_bytes).err: return None
    return result_bytes.getvalue()

# ==========================================
# 🖥️ DYNAMIC RENDER ENGINE (New Tab Link Edition)
# ==========================================
def render_document(doc_key):
    content = db_library.get(doc_key, f"Standard specification for {doc_key}.")
    
    # 1. Clean the HTML out of the text
    clean_text = re.sub(r'<[^>]+>', '', content)
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    
    # 2. Extract the TRUE title (first line in your data)
    if lines:
        full_title = lines[0]
        body_lines = [line for line in lines if not line.startswith('Addendum') and not line.startswith('WC-SOP')]
        snippet = body_lines[0] if body_lines else clean_text[:150]
    else:
        full_title = doc_key
        snippet = "No description available."
        
    if len(snippet) > 180: 
        snippet = snippet[:177] + "..."
        
    file_name = f"{re.sub(r'[^a-zA-Z0-9]+', '_', doc_key)}_Spec.pdf"
    
    # Hide if it doesn't match the search query
    if search_query and search_query not in full_title.lower() and search_query not in content.lower():
        return False
        
    # 3. Render the UI cards
    with st.expander(f"📄 {full_title}"):
        st.markdown(f"**Executive Snippet:**\n{snippet}")
        col_dl, col_view = st.columns([1, 1])
        
        # PDF Download Button
        if HAS_PDF_ENGINE:
            pdf_bytes = generate_pro_pdf(doc_key, "2026-08-09", content)
            if pdf_bytes:
                col_dl.download_button("📥 Download Native PDF", pdf_bytes, file_name=file_name, mime="application/pdf", key=f"dl_{doc_key}")
        else:
            col_dl.warning("⚠️ Run `pip install xhtml2pdf` to enable PDF downloads.")
            
        # Browser Viewer Link Button (Opens in New Tab)
        safe_key = urllib.parse.quote(doc_key)
        link_html = f'''
        <a href="/?view_doc={safe_key}" target="_blank" style="
            display: inline-block;
            padding: 7px 14px;
            background-color: #0047AB; 
            color: #FFFFFF !important;
            border: 1.5px solid #D4AF37;
            text-decoration: none !important;
            border-radius: 4px;
            font-family: sans-serif;
            font-size: 14px;
            font-weight: 600;
            text-align: center;
        ">
            📖 Read Full Document in New Tab ↗
        </a>
        '''
        col_view.markdown(link_html, unsafe_allow_html=True)
        
    return True

# Draw the Folder Structure
for top_folder, sub_folders in FOLDER_STRUCTURE.items():
    st.markdown(f"#### {top_folder}")
    for sub_name, doc_keys in sub_folders.items():
        if sub_name:
            st.markdown(f"**{sub_name}**")
        for key in doc_keys:
            render_document(key)
    st.markdown("---")