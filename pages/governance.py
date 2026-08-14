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
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 51, 160) # Corporate Royal Blue
        self.cell(0, 10, "Wickboldt Capital", border=False, ln=True, align="R")
        self.set_font("Arial", "I", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "Enterprise Governance Library", border=False, ln=True, align="R")
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
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

# Try to pull from the database first
library_data = get_library_state()

# --- THE FAILSAFE: RESTORE MASTER DOCUMENTS IF DB IS WIPED ---
if not library_data:
    st.toast("Database returned empty. Restoring Wickboldt Master Templates from secure backup...")
    library_data = {
        "Master Subcontractor Agreement": "WICKBOLDT CAPITAL, LLC\nMaster Subcontractor Agreement\n\nThis agreement outlines the standard terms, insurance requirements, and quality expectations for all subcontractors operating on Wickboldt Capital projects. All contractors must provide proof of liability insurance prior to commencing work.",
        "HVAC Engineering & Installation Addendum": "HVAC SYSTEM INSTALLATION ADDENDUM\n\nAll HVAC installations must comply with ACCA Manual J, S, and D specifications. Thermostat offset calculations and Brushless Direct Current ceiling fan airflow dynamics must be factored into the final engineering report prior to permit submittal.",
        "FEMA 50% Rule & Elevation Addendum": "ELEVATION & FOUNDATION ADDENDUM\n\nFor structure relocations and renovations, final elevation specifications must be strictly certified to 21.12 feet to comply with floodplain management and FEMA guidelines. Elevation Certificates must be provided upon foundation completion.",
        "Standard Draw Schedule": "CONSTRUCTION DRAW SCHEDULE\n\nPhase 1: Foundation, Site Layout & Underground Utilities (20%)\nPhase 2: Framing, ICF Assembly, & Dry-In (30%)\nPhase 3: MEP Rough-In (20%)\nPhase 4: Finishes, Trim & Paint (20%)\nPhase 5: Final Punchlist & Certificate of Occupancy (10%)"
    }

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
                st.success("Saved successfully to the database!")
            except Exception as e:
                st.warning(f"Could not save to database: {e}")

with tab_pdf:
    st.markdown(f"### PDF Preview: {doc_title}")
    
    if st.button("🔄 Generate PDF Render", type="primary"):
        with st.spinner("Compiling PDF..."):
            pdf = WickboldtPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, doc_title, ln=True, align="C")
            pdf.ln(5)
            
            # Body Text
            pdf.set_font("Arial", "", 11)
            safe_text = edited_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, safe_text)
            
            # Save and display
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf.output(tmp_file.name)
                with open(tmp_file.name, "rb") as f:
                    pdf_bytes = f.read()
                    
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            
            st.download_button(
                label="⬇️ Download Official PDF",
                data=pdf_bytes,
                file_name=f"{doc_title.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            
            st.markdown("#### Document Preview")
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)