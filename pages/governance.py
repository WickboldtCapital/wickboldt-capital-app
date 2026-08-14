import streamlit as st
import base64
import tempfile
from fpdf import FPDF
from db_ops import get_library_state

# --- SECURITY GUARD ---
if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: Administrator privileges required.")
    st.stop()

# ==========================================
# 📄 FPDF ENGINE CONFIGURATION
# ==========================================
class WickboldtPDF(FPDF):
    def header(self):
        # Professional header
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 51, 160) # Corporate Royal Blue
        self.cell(0, 10, "Wickboldt Capital", border=False, ln=True, align="R")
        self.set_font("Arial", "I", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "Enterprise Governance Library", border=False, ln=True, align="R")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        # Footer with custom tagline
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Today's Foundation. Tomorrow's Legacy.  |  Page " + str(self.page_no()), 0, 0, "C")

# ==========================================
# 🖥️ GOVERNANCE UI & EDITOR
# ==========================================
st.title("🏢 Master Company Library")
st.markdown("Select a master template or addendum below to edit the text or generate a finalized PDF document.")
st.divider()

library_data = get_library_state()

if not library_data:
    st.warning("⚠️ No documents currently found in the database.")
    st.stop()

# --- DOCUMENT SELECTOR ---
doc_title = st.selectbox("📂 Select Document", sorted(library_data.keys()))
current_text = library_data[doc_title]

st.markdown("---")

# --- DUAL WORKSPACE: EDITOR & VIEWER ---
tab_edit, tab_pdf = st.tabs(["📝 Text Editor", "📄 PDF Viewer & Export"])

with tab_edit:
    st.markdown(f"### Editing: {doc_title}")
    # Live text editor
    edited_text = st.text_area("Document Content", value=current_text, height=500, label_visibility="collapsed")
    
    col_save, _ = st.columns([1, 4])
    with col_save:
        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            try:
                from db_ops import update_library_doc
                update_library_doc(doc_title, edited_text)
                st.success("Saved successfully!")
            except ImportError:
                st.warning("Save successful in current session. (Requires 'update_library_doc' in db_ops to persist permanently).")

with tab_pdf:
    st.markdown(f"### PDF Preview: {doc_title}")
    
    if st.button("🔄 Generate PDF Render", type="primary"):
        with st.spinner("Compiling PDF..."):
            # Build the PDF using FPDF
            pdf = WickboldtPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, doc_title, ln=True, align="C")
            pdf.ln(5)
            
            # Body Text (Converting encoding safely)
            pdf.set_font("Arial", "", 11)
            safe_text = edited_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, safe_text)
            
            # Save to temporary file to display in iframe
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf.output(tmp_file.name)
                
                # Read file for Base64 injection into iframe
                with open(tmp_file.name, "rb") as f:
                    pdf_bytes = f.read()
                    
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Download Button
            st.download_button(
                label="⬇️ Download Official PDF",
                data=pdf_bytes,
                file_name=f"{doc_title.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            
            # Embedded PDF Viewer
            st.markdown("#### Document Preview")
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)