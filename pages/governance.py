import streamlit as st
import base64
from fpdf import FPDF
from db_ops import get_library_state, update_library_doc

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
st.markdown("Select a master template, add a new document, or generate a finalized PDF.")
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

# --- DOCUMENT SELECTOR (WITH CREATE NEW FEATURE) ---
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
tab_edit, tab_pdf = st.tabs(["📝 Text Editor", "📄 PDF Viewer & Export"])

with tab_edit:
    st.markdown(f"### Editing: {active_title if active_title else 'New Document'}")
    
    # Live text editor
    edited_text = st.text_area("Document Content", value=current_text, height=500, label_visibility="collapsed")
    
    col_save, _ = st.columns([1, 4])
    with col_save:
        if st.button("💾 Save to Database", type="primary", use_container_width=True):
            if active_title.strip() == "":
                st.error("⚠️ Please enter a document title before saving.")
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
        
        if st.button("🔄 Generate PDF Render", type="primary"):
            with st.spinner("Compiling PDF in memory..."):
                pdf = WickboldtPDF()
                pdf.add_page()
                
                # Title
                pdf.set_font("Arial", "B", 16)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, active_title, ln=True, align="C")
                pdf.ln(5)
                
                # Body Text
                pdf.set_font("Arial", "", 11)
                safe_text = edited_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, safe_text)
                
                # Generate directly into RAM (Zero-disk usage)
                pdf_bytes = pdf.output(dest="S").encode("latin-1")
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                
                st.download_button(
                    label="⬇️ Download Official PDF",
                    data=pdf_bytes,
                    file_name=f"{active_title.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
                st.markdown("#### Document Preview")
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)