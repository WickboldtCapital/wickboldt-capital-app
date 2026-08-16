from fpdf import FPDF

def generate_proforma_pdf(project_cost, required_equity, noi, yield_on_cost, cash_flows):
    """Generates a branded Wickboldt Capital PDF packet in memory."""
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Wickboldt Capital - Investment Proforma", ln=True, align="C")
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Build-to-Rent Portfolio Analysis", ln=True, align="C")
    pdf.ln(10)
    
    # --- EXECUTIVE SUMMARY ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.set_font("Arial", '', 11)
    
    pdf.cell(0, 8, f"Total Project Cost: ${project_cost:,.0f}", ln=True)
    pdf.cell(0, 8, f"Required Equity: ${required_equity:,.0f}", ln=True)
    pdf.cell(0, 8, f"Stabilized Annual NOI: ${noi:,.0f}", ln=True)
    pdf.cell(0, 8, f"Target Yield on Cost: {yield_on_cost:.2f}%", ln=True)
    pdf.ln(10)
    
    # --- 10-YEAR PROJECTION ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "10-Year Cash Flow Projection (NOI)", ln=True)
    pdf.set_font("Arial", '', 11)
    
    for i, cf in enumerate(cash_flows, 1):
        pdf.cell(0, 8, f"Year {i}: ${cf:,.0f}", ln=True)
        
    # Return the PDF file as a byte stream ready for download
    return bytes(pdf.output())
