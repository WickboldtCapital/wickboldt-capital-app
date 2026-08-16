import streamlit as st
import sqlite3
import json
from fpdf import FPDF

st.set_page_config(page_title="Investment Deal Packet", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# Fetch project state from database
DB_FILE = "wickboldt_projects.db"
def get_db_state():
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return {}
    except Exception:
        return {}

db_state = get_db_state()

st.header("📄 Automated Deal Packet & Pitch Deck Generator")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Generate a publication-ready, branded Wickboldt Capital investment pitch deck incorporating live underwriting and estimation data.")
st.divider()

# --- INPUT OVERRIDES FOR PACKET ---
col1, col2 = st.columns(2)
with col1:
    packet_title = st.text_input("Packet / Project Title", value=f"{active_project} Investment Offering")
    target_yoc = st.number_input("Target Yield-on-Cost (%)", value=9.45, step=0.05)
    monthly_rent = st.number_input("Projected Monthly Rent ($)", value=4500.0, step=100.0)
with col2:
    appraisal_val = st.number_input("Target Appraisal / Value ($)", value=200000.0, step=5000.0)
    sq_ft = db_state.get("est_sq_ft", 1150.0)
    st.info(f"📊 **Linked Living Area:** {sq_ft:,.0f} SqFt (pulled from Estimation module)")

st.divider()

# --- NEW FEATURE: CAPITAL STACK CALCULATOR ---
st.subheader("🏦 Capital Stack Requirements")
st.markdown("Dynamically calculate the required equity and debt facility based on the target appraisal.")
ltv_pct = st.slider("Target Loan-to-Value (LTV) %", min_value=50, max_value=90, value=75, step=1)

loan_amount = appraisal_val * (ltv_pct / 100.0)
required_equity = appraisal_val - loan_amount

c1, c2 = st.columns(2)
c1.metric("Projected Debt Facility (Loan)", f"${loan_amount:,.2f}")
c2.metric("Required Cash / Equity", f"${required_equity:,.2f}")
st.divider()

# --- SAFE PURE-PYTHON PDF GENERATOR (FPDF2) ---
class DealPacketPDF(FPDF):
    def header(self):
        # Header with Wickboldt Brand Colors
        self.set_font("helvetica", "B", 16)
        self.set_text_color(26, 54, 93) # Navy blue
        self.cell(0, 10, "WICKBOLDT CAPITAL", border=False, ln=1, align="C")
        self.set_font("helvetica", "I", 10)
        self.set_text_color(212, 175, 55) # Gold
        self.cell(0, 5, "Today's Foundation. Tomorrow's Legacy.", border=False, ln=1, align="C")
        self.ln(10)

    def footer(self):
        # Footer
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(136, 136, 136)
        self.cell(0, 10, f"Confidential Investment Packet | Page {self.page_no()}", align="C")

def compile_pdf():
    pdf = DealPacketPDF()
    pdf.add_page()
    
    # --- COVER PAGE ---
    pdf.set_y(60)
    pdf.set_font("helvetica", "B", 24)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 15, packet_title, ln=1, align="C")
    
    pdf.set_font("helvetica", "", 16)
    pdf.set_text_color(74, 85, 104)
    pdf.cell(0, 10, "Build-to-Rent Asset Offering", ln=1, align="C")
    pdf.ln(30)
    
    # Meta Details Box
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Project Details:", ln=1, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Project Name: {active_project}", ln=1, align="C")
    pdf.cell(0, 8, f"Living Area: {sq_ft:,.0f} SqFt", ln=1, align="C")
    pdf.cell(0, 8, f"Target Appraisal: ${appraisal_val:,.2f}", ln=1, align="C")
    pdf.cell(0, 8, f"Target Yield-on-Cost: {target_yoc}%", ln=1, align="C")
    
    pdf.add_page()
    
    # --- SECTION 1: EXECUTIVE SUMMARY ---
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 10, "1. Executive Summary & Proforma", ln=1)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(212, 175, 55) # Gold line
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Metrics Grid
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(95, 10, f"Appraised Value: ${appraisal_val:,.0f}", border=1, align="C")
    pdf.cell(95, 10, f"Yield-on-Cost: {target_yoc}%", border=1, ln=1, align="C")
    pdf.cell(95, 10, f"Monthly Rent: ${monthly_rent:,.0f}", border=1, align="C")
    pdf.cell(95, 10, f"Gross Rent Multiplier: 10.0x", border=1, ln=1, align="C")
    pdf.ln(10)
    
    # --- SECTION 2: CAPITAL STACK (NEW FEATURE) ---
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 10, "2. Capital Stack & Funding Request", ln=1)
    pdf.set_draw_color(212, 175, 55)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0,0,0)
    
    # Stack breakdown
    pdf.cell(100, 10, f"Target Loan-to-Value (LTV):", border=0)
    pdf.cell(90, 10, f"{ltv_pct}%", border=0, ln=1, align="R")
    
    pdf.cell(100, 10, f"Projected Debt Facility:", border=0)
    pdf.cell(90, 10, f"${loan_amount:,.2f}", border=0, ln=1, align="R")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(100, 10, f"Required Equity / Cash:", border=0)
    pdf.cell(90, 10, f"${required_equity:,.2f}", border=0, ln=1, align="R")
    
    return bytes(pdf.output())

# --- ACTION BUTTON ---
if st.button("🚀 Generate & Download PDF Deal Packet", type="primary", use_container_width=True):
    with st.spinner("Compiling pure-Python FPDF Layout..."):
        pdf_bytes = compile_pdf()
        
        st.success("✅ Deal Packet Generated Successfully!")
        st.download_button(
            label="📥 Download PDF Investment Packet",
            data=pdf_bytes,
            file_name=f"Wickboldt_Capital_{active_project.replace(' ', '_')}_Deal_Packet.pdf",
            mime="application/pdf",
            type="primary"
        )
        