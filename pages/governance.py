import streamlit as st
import base64
from fpdf import FPDF
from streamlit_quill import st_quill
from db_ops import get_library_state, update_library_doc
from drive_ops import read_google_doc, upload_pdf_to_drive

# --- SECURITY GUARD ---
if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: Administrator privileges required.")
    st.stop()

# ==========================================
# 📄 FPDF2 ENGINE CONFIGURATION
# ==========================================
class WickboldtPDF(FPDF):
    def header(self):
        # fpdf2 uses helvetica as the default modern font
        self.set_font("helvetica", "B", 14)
        self.set_text_color(0, 51, 160) # Corporate Royal Blue
        self.cell(w=0, h=10, text="Wickboldt Capital", border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_font("helvetica", "I", 10)
        self.set_text_color(128, 128, 128)
        self.cell(w=0, h=5, text="Enterprise Governance Library", border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(w=0, h=10, text="Today's Foundation. Tomorrow's Legacy.  |  Page " + str(self.page_no()), align="C")

# ==========================================
# 🖥️ GOVERNANCE UI & EDITOR
# ==========================================
st.title("🏢 Master Company Library & Workspace Sync")
st.markdown("Manage enterprise documentation, sync with Google Workspace, and generate certified PDFs.")
st.divider()

# --- GOOGLE DRIVE SYNC PANEL ---
with st.expander("☁️ Google Workspace Sync Settings", expanded=False):
    st.markdown("Sync your app directly with your live Google Workspace documents.")
    # The default ID is set to your Deployment Brief
    default_doc_id = "1k5P4Lxo82lvVQ080lsGpkc6gMEs4v8vl9gOJN_ElRn0"
    target_doc_id = st.text_input("Google Doc ID", value=default_doc_id)
    target_folder_id = st.text_input("Google Drive Folder ID (for PDF backups)", placeholder="Paste folder ID here...")
    
    if st.button("📥 Pull Latest from Google Doc"):
        with st.spinner("Fetching live content from Google Workspace..."):
            fetched_text = read_google_doc(target_doc_id)
            if fetched_text and not fetched_text.startswith("Error"):
                update_library_doc("Enterprise Deployment & Architecture Brief", fetched_text, "Google Workspace Sync")
                st.success("✅ Successfully pulled and updated brief from Google Drive!")
                st.rerun()
            else:
                st.error(fetched_text)

# Fetch from database
library_data = get_library_state()

# --- THE FAILSAFE ---
if not library_data:
    st.toast("Database returned empty. Restoring Wickboldt Master Templates from secure backup...")
    library_data = {
        "Master Subcontractor Agreement": "<h3>WICKBOLDT CAPITAL, LLC</h3><p><b>Master Subcontractor Agreement</b></p><p>This agreement outlines the standard terms, insurance requirements, and quality expectations for all subcontractors operating on Wickboldt Capital projects.</p>"
    }

# --- DOCUMENT SELECTOR ---
doc_titles = sorted(list(library_data.keys()))
options = ["-- Create New Document --"] + doc_titles

col1, col2 = st.columns([3, 1])
with col1:
    selected_doc = st.selectbox("📂 Select Document", options)

# --- EDITOR LOGIC ---
if selected_doc == "-- Create New Document --":
    active_title = st.text_input("New Document Title", placeholder="e.g., Strategic Deployment Thesis")
    current_text = ""
else:
    active_title = selected_doc
    current_text = library_data.get(selected_doc, "")

st.markdown("---")

# --- DUAL WORKSPACE: EDITOR & VIEWER ---
tab_edit, tab_pdf = st.tabs(["📝 Enterprise Rich Text Editor", "📄 PDF Viewer & Export"])

with tab_edit:
    st.markdown(f"### Editing: {active_title if active_title else 'New Document'}")
    
    # 🌟 ENTERPRISE RICH TEXT EDITOR
    edited_text = st_quill(
        value=current_text,
        placeholder="Draft your enterprise document here...",
        html=True,
        key="quill_editor"
    )
    
    col_save, _ = st.columns([1, 4])
    with col_save:
        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            if active_title.strip() == "":
                st.error("⚠️ Please enter a document title before saving.")
            elif not edited_text:
                st.error("⚠️ Document cannot be empty.")
            else:
                try:
                    user_email = st.session_state.get("user_email", "System")
                    update_library_doc(active_title, edited_text, user_email)
                    st.success(f"✅ Saved '{active_title}' successfully!")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Could not save to database: {e}")

with tab_pdf:
    if active_title == "" or active_title == "-- Create New Document --":
        st.info("💡 Save your new document first before generating a PDF.")
    else:
        st.markdown(f"### PDF Preview: {active_title}")
        
        if st.button("🔄 Generate Rich PDF Render", type="primary"):
            with st.spinner("Compiling PDF with rich formatting..."):
                pdf = WickboldtPDF()
                pdf.add_page()
                
                # Title
                pdf.set_font("helvetica", "B", 16)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(w=0, h=10, text=active_title, new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(5)
                
                # Render the HTML Native directly into the PDF!
                pdf.set_font("helvetica", "", 11)
                pdf.write_html(edited_text)
                
                # Generate directly into RAM using fpdf2's modern output style
                pdf_bytes = bytes(pdf.output())
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                
                st.download_button(
                    label="⬇️ Download Official PDF",
                    data=pdf_bytes,
                    file_name=f"{active_title.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
                # Push to Drive option if folder ID is provided
                if target_folder_id:
                    if st.button("☁️ Push PDF to Google Drive Folder"):
                        success, res = upload_pdf_to_drive(pdf_bytes, f"{active_title}.pdf", target_folder_id)
                        if success:
                            st.success(f"✅ Successfully uploaded to Google Drive! File ID: {res}")
                        else:
                            st.error(f"❌ Upload failed: {res}")
                
                st.markdown("#### Document Preview")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)