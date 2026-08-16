import streamlit as st
import pandas as pd
from ai_ops import parse_contractor_bid
from db_ops import add_budget_line_item

st.title("🤖 AI Bid Ingestion & Parsing")
st.markdown("Upload contractor bids, supplier invoices, or quotes. The Gemini AI engine will parse the document, extract line items, and ingest them directly into the active project budget.")

active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ No active project selected. Please select a project from the sidebar to ingest bids.")
    st.stop()

st.success(f"Ingesting bids for project: **{active_project}**")
st.divider()

uploaded_file = st.file_uploader("Upload Contractor Bid or Invoice (PDF or Text)", type=["pdf", "csv", "txt"])

if uploaded_file:
    st.info(f"File uploaded: `{uploaded_file.name}`. Click below to parse.")
    
    if st.button("Parse Document with Gemini AI", type="primary"):
        with st.spinner("Analyzing document structure and extracting line items..."):
            file_bytes = uploaded_file.read()
            parsed_data = parse_contractor_bid(file_bytes, uploaded_file.name)
            st.session_state["parsed_bid"] = parsed_data

# Display Parsed Results
if "parsed_bid" in st.session_state:
    st.divider()
    st.subheader("📊 Extracted Bid Data")
    
    bid = st.session_state["parsed_bid"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendor Name", bid.get("vendor_name", "Unknown"))
    col2.metric("Category", bid.get("category", "General"))
    col3.metric("Total Amount", f"${bid.get('total_amount', 0):,.2f}")
    
    st.caption(f"**AI Notes:** {bid.get('notes', 'No notes provided.')}")
    
    # Display line items
    line_items = bid.get("line_items", [])
    if line_items:
        df = pd.DataFrame(line_items)
        st.dataframe(df, use_container_width=True)
        
        # Ingestion Hook
        st.divider()
        st.subheader("💾 Ingest to Project Budget")
        st.markdown("Review the line items above. If accurate, click below to commit these costs directly into the active project proforma.")
        
        if st.button("Commit Bid to Project Database", type="primary", use_container_width=True):
            success_count = 0
            with st.spinner("Writing line items to Supabase..."):
                for item in line_items:
                    success, msg = add_budget_line_item(
                        project_name=active_project,
                        category=bid.get("category", "General"),
                        vendor_name=bid.get("vendor_name", "Unknown"),
                        description=item.get("description", "Unknown Item"),
                        qty=item.get("qty", 1),
                        unit_cost=item.get("unit_cost", 0.0),
                        total_cost=item.get("total", 0.0)
                    )
                    if success:
                        success_count += 1
                        
            if success_count == len(line_items):
                st.success(f"✅ Successfully ingested {success_count} line items into the {active_project} budget!")
                # Clear session state so they can upload a new one
                del st.session_state["parsed_bid"]
                st.rerun()
            else:
                st.warning(f"⚠️ Partially successful. {success_count} of {len(line_items)} items saved.")
    else:
        st.warning("No line items could be extracted from this document.")