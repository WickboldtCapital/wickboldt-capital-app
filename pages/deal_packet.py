import streamlit as st
import sqlite3
import json
import tempfile
import os
from weasyprint import HTML

st.set_page_config(page_title="Investment Deal Packet", layout="wide")

# --- SECURITY GUARD ---
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

# Fetch project state from database
DB_FILE = "wickboldt_projects.db"
def get_db_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
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

if st.button("🚀 Generate & Download PDF Deal Packet", type="primary", use_container_width=True):
    with st.spinner("Compiling WeasyPrint PDF layout..."):
        
        # HTML template matching your professional styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4 portrait;
                    margin: 15mm 15mm;
                    background-color: #fcfbf9;
                    @bottom-right {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 8pt;
                        color: #888;
                    }}
                    @bottom-left {{
                        content: "Wickboldt Capital | Confidential Investment Packet";
                        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        font-size: 8pt;
                        color: #888;
                    }}
                }}
                *, *::before, *::after {{ box-sizing: border-box; }}
                body {{
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    color: #2c3e50;
                    line-height: 1.5;
                    margin: 0;
                    padding: 0;
                    font-size: 10pt;
                }}
                .cover {{
                    height: 260mm;
                    display: block;
                    position: relative;
                    text-align: center;
                    padding-top: 50mm;
                }}
                .cover-badge {{
                    display: inline-block;
                    background-color: #1a365d;
                    color: #d4af37;
                    font-size: 9pt;
                    font-weight: bold;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    padding: 8px 16px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}
                .cover h1 {{
                    font-size: 26pt;
                    color: #1a365d;
                    margin: 0 0 10px 0;
                    font-weight: 700;
                }}
                .cover h2 {{
                    font-size: 14pt;
                    color: #4a5568;
                    margin: 0 0 30px 0;
                    font-weight: 400;
                }}
                .tagline {{
                    font-style: italic;
                    color: #d4af37;
                    font-size: 13pt;
                    margin-bottom: 50px;
                }}
                .cover-meta {{
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    max-width: 400px;
                    margin: 0 auto;
                    text-align: left;
                }}
                .cover-meta table {{ width: 100%; border-collapse: collapse; }}
                .cover-meta td {{ padding: 6px 0; font-size: 9.5pt; }}
                .cover-meta td.label {{ color: #718096; font-weight: 500; }}
                .cover-meta td.val {{ color: #1a365d; font-weight: 700; text-align: right; }}
                
                .page-break {{ page-break-before: always; }}
                
                h2.section-title {{
                    font-size: 15pt;
                    color: #1a365d;
                    border-bottom: 2px solid #d4af37;
                    padding-bottom: 6px;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}
                h3 {{ font-size: 11pt; color: #2b6cb0; margin-top: 15px; margin-bottom: 8px; }}
                
                .metrics-grid {{ display: table; width: 100%; margin-bottom: 20px; }}
                .metric-card {{
                    display: table-cell;
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-top: 4px solid #1a365d;
                    border-radius: 6px;
                    padding: 12px;
                    text-align: center;
                    width: 33.33%;
                }}
                .metric-val {{ font-size: 15pt; font-weight: bold; color: #1a365d; margin-bottom: 4px; }}
                .metric-lbl {{ font-size: 8pt; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; }}
                
                table.data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #ffffff; font-size: 9pt; }}
                table.data-table th {{ background-color: #1a365d; color: #ffffff; text-align: left; padding: 8px 10px; }}
                table.data-table td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; color: #2d3748; }}
                table.data-table tr:nth-child(even) {{ background-color: #f7fafc; }}
            </style>
        </head>
        <body>
            <div class="cover">
                <div class="cover-badge">Wickboldt Capital Portfolio</div>
                <h1>{packet_title}</h1>
                <h2>Build-to-Rent Asset Offering</h2>
                <div class="tagline">Today's Foundation. Tomorrow's Legacy.</div>
                
                <div class="cover-meta">
                    <table>
                        <tr><td class="label">Project Name:</td><td class="val">{active_project}</td></tr>
                        <tr><td class="label">Living Area:</td><td class="val">{sq_ft:,.0f} SqFt</td></tr>
                        <tr><td class="label">Target Appraisal:</td><td class="val">${appraisal_val:,.2f}</td></tr>
                        <tr><td class="label">Target Yield-on-Cost:</td><td class="val">{target_yoc}% YOC</td></tr>
                    </table>
                </div>
            </div>

            <div class="page-break"></div>
            
            <h2 class="section-title">1. Executive Summary & Proforma</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-val">${appraisal_val:,.0f}</div>
                    <div class="metric-lbl">Appraised Value</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">{target_yoc}%</div>
                    <div class="metric-lbl">Yield-on-Cost</div>
                </div>
                <div class="metric-card">
                    <div class="metric-val">${monthly_rent:,.0f}</div>
                    <div class="metric-lbl">Monthly Rent</div>
                </div>
            </div>

            <h3>Underwriting Baseline</h3>
            <table class="data-table">
                <tr><th>Parameter</th><th>Value</th></tr>
                <tr><td>Unit Size</td><td>{sq_ft:,.0f} SqFt</td></tr>
                <tr><td>Gross Rent Multiplier</td><td>10.0x Market Baseline</td></tr>
                <tr><td>Construction Debt Facility</td><td>75% LTV</td></tr>
            </table>
        </body>
        </html>
        """
        
        # Write to temp file and generate PDF bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            
        HTML(string=html_content).write_pdf(tmp_path)
        
        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
            
        os.unlink(tmp_path)
        
        st.success("✅ Deal Packet Generated Successfully!")
        st.download_button(
            label="📥 Download PDF Investment Packet",
            data=pdf_bytes,
            file_name=f"Wickboldt_Capital_{active_project}_Deal_Packet.pdf",
            mime="application/pdf",
            type="primary"
        )