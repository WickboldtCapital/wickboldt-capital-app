import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import date, timedelta

st.set_page_config(page_title="Subcontractor CRM & Bid Management", layout="wide")

# ==========================================
# 🔒 SECURITY & CONTEXT GUARDS
# ==========================================
active_project = st.session_state.get("active_project")
if not active_project:
    st.warning("⚠️ Access Restricted: Please load a project from the Control tab.")
    st.stop()

DB_FILE = "wickboldt_projects.db"

# --- DB HELPERS ---
def get_db_state():
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (active_project,)).fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
    except Exception:
        pass
    return {}

def save_state(updated_dict):
    current_state = get_db_state()
    current_state.update(updated_dict)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), active_project))
    conn.commit()
    conn.close()

db_state = get_db_state()
subs_list = db_state.get("subs_roster", [])
awarded_bids = db_state.get("awarded_bids", {})
rfp_logs = db_state.get("rfp_logs", [])
quote_vault = db_state.get("quote_vault", {})

# Fetch Engineered Targets for Bid Leveling Comparison
eng_data = db_state.get("engineering", {})
est_data = db_state.get("estimates", {})

def get_engineered_target(trade):
    """Maps the selected CRM trade to the calculated MEP/Engineering hard costs."""
    if trade == "Plumbing":
        return float(eng_data.get("plumbing_total_cost", 0.0))
    elif trade == "Electrical":
        return float(eng_data.get("elec_total_cost", 0.0))
    elif trade == "Framing":
        return float(eng_data.get("framing_total_cost", 0.0))
    elif trade == "HVAC":
        # Assumes HVAC module outputs this key
        return float(eng_data.get("hvac_total_cost", 0.0))
    elif trade == "Concrete & Foundation":
        return float(eng_data.get("foundation_total_cost", 0.0))
    elif trade in ["Painting", "Drywall & Insulation", "Flooring", "Finish Carpentry"]:
        # Pulls from Architecture Interior Finishes bucket
        return float(est_data.get("Interior Finishes & Drywall", 0.0))
    elif trade == "Roofing":
        return float(est_data.get("Exterior Shell Finishes", 0.0))
    return 0.0

st.header("🤝 Subcontractor CRM & Procurement")
st.markdown(f"**Active Development:** `{active_project}`")
st.markdown("Manage your trade roster, issue RFPs, compare bids against engineered baselines, and award contracts.")
st.divider()

trade_categories = [
    "Site Work & Excavation", "Concrete & Foundation", "Framing", 
    "Roofing", "Plumbing", "Electrical", "HVAC", 
    "Drywall & Insulation", "Painting", "Flooring", "Finish Carpentry"
]

# ==========================================
# ENTERPRISE WORKFLOW TABS
# ==========================================
tab_roster, tab_rfp, tab_bids, tab_awards = st.tabs([
    "1. 📇 Roster & Compliance", 
    "2. 📤 Issue Bid Requests (RFP)", 
    "3. ⚖️ Bid Leveling vs Engineered Targets", 
    "4. 🏆 Awarded Contracts"
])

# ==========================================
# TAB 1: ROSTER & COMPLIANCE
# ==========================================
with tab_roster:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add Subcontractor")
        with st.form("add_sub_form", clear_on_submit=True):
            company_name = st.text_input("Company Name")
            trade = st.selectbox("Primary Trade", trade_categories)
            contact_name = st.text_input("Primary Contact")
            phone = st.text_input("Phone Number")
            email = st.text_input("Email Address")
            status = st.selectbox("Status", ["Active", "Probation", "Do Not Use"])
            
            if st.form_submit_button("💾 Save Subcontractor", type="primary"):
                if company_name and trade:
                    new_sub = {
                        "id": str(len(subs_list) + 1),
                        "Company": company_name,
                        "Trade": trade,
                        "Contact": contact_name,
                        "Phone": phone,
                        "Email": email,
                        "Status": status,
                        "GL_Expiry": str(date.today() + timedelta(days=180)),
                        "WC_Expiry": str(date.today() + timedelta(days=180))
                    }
                    subs_list.append(new_sub)
                    save_state({"subs_roster": subs_list})
                    st.success(f"{company_name} added to the master roster!")
                else:
                    st.error("Company Name and Trade are required.")

    with col2:
        st.subheader("Master Roster & Insurance Compliance")
        st.markdown("Track General Liability (GL) and Workers' Compensation (WC) expirations.")
        if subs_list:
            df_comp = pd.DataFrame(subs_list)
            df_comp['GL_Expiry'] = pd.to_datetime(df_comp['GL_Expiry'])
            df_comp['WC_Expiry'] = pd.to_datetime(df_comp['WC_Expiry'])
            
            today = pd.to_datetime(date.today())
            df_comp['GL_Status'] = df_comp['GL_Expiry'].apply(lambda x: "🔴 Expired" if x < today else ("🟡 Expiring Soon" if (x - today).days <= 30 else "🟢 Valid"))
            df_comp['WC_Status'] = df_comp['WC_Expiry'].apply(lambda x: "🔴 Expired" if x < today else ("🟡 Expiring Soon" if (x - today).days <= 30 else "🟢 Valid"))
            
            st.dataframe(
                df_comp[["Company", "Trade", "Contact", "GL_Status", "WC_Status"]], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Your subcontractor roster is currently empty.")

# ==========================================
# TAB 2: ISSUE BID REQUESTS (RFP)
# ==========================================
with tab_rfp:
    st.subheader("Generate Bid Request (RFP)")
    st.markdown("Draft a scope of work and log Bid Requests sent out to eligible subcontractors.")
    
    rfp_col1, rfp_col2 = st.columns([1, 2])
    
    with rfp_col1:
        rfp_trade = st.selectbox("Select Trade Phase", trade_categories, key="rfp_trade")
        eligible_rfp_subs = [sub["Company"] for sub in subs_list if sub["Trade"] == rfp_trade]
        
        target_subs = st.multiselect("Select Subcontractors to Invite", eligible_rfp_subs)
        due_date = st.date_input("Bid Deadline", value=date.today() + timedelta(days=14))
        
    with rfp_col2:
        scope_of_work = st.text_area("Detailed Scope of Work & Inclusions", value="Please provide a turnkey bid including all labor, materials, and equipment required per Wickboldt Capital standard plans and specifications.", height=150)
        
        if st.button("📤 Log & Issue Bid Request", type="primary"):
            if target_subs:
                rfp_logs.append({
                    "Date_Issued": str(date.today()),
                    "Trade": rfp_trade,
                    "Invited_Subs": ", ".join(target_subs),
                    "Due_Date": str(due_date),
                    "Scope": scope_of_work
                })
                save_state({"rfp_logs": rfp_logs})
                st.toast("✅ Bid Request Logged Successfully!")
                st.success(f"RFP generated for {len(target_subs)} subcontractor(s).")
            else:
                st.warning("Please select at least one subcontractor to invite.")

    st.divider()
    st.markdown("##### 📜 Active Bid Requests (RFPs)")
    if rfp_logs:
        st.dataframe(pd.DataFrame(rfp_logs), use_container_width=True, hide_index=True)
    else:
        st.info("No RFPs have been issued yet.")

# ==========================================
# TAB 3: BID LEVELING & QUOTES VAULT
# ==========================================
with tab_bids:
    st.subheader("Bid Leveling (Apples-to-Apples Comparison)")
    st.markdown("Compare incoming bids directly against your internally engineered targets to instantly spot overages.")
    
    target_trade = st.selectbox("Select Trade for Bid Leveling", trade_categories)
    eligible_subs = [sub["Company"] for sub in subs_list if sub["Trade"] == target_trade]
    
    # Live Integration: Fetch target from Engineering Modules
    target_budget = get_engineered_target(target_trade)
    
    st.info(f"**🎯 Engineered Target Budget ({target_trade}):** ${target_budget:,.2f}" if target_budget > 0 else f"**🎯 Engineered Target Budget ({target_trade}):** No engineered baseline found. Using open bid.")
    
    if len(eligible_subs) < 2:
        st.warning(f"You need at least 2 subcontractors under the '{target_trade}' trade to perform bid leveling.")
    else:
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("#### Bidder A")
            sub_a = st.selectbox("Select Subcontractor A", eligible_subs, key="sub_a")
            bid_a_amt = st.number_input("Base Bid Amount ($)", min_value=0.0, step=500.0, key="amt_a")
            
            # Real-Time Variance Calculation
            if target_budget > 0 and bid_a_amt > 0:
                var_a = target_budget - bid_a_amt
                if var_a >= 0:
                    st.success(f"**Variance:** Under budget by ${abs(var_a):,.2f}")
                else:
                    st.error(f"**Variance:** Over budget by ${abs(var_a):,.2f}")
            
            inc_a = st.checkbox("Includes Materials?", key="mat_a")
            pull_a = st.checkbox("Pulls Municipal Permits?", key="perm_a")
            exc_a = st.text_area("Noted Exclusions", key="exc_a")
            
            st.markdown("**Upload Official Quote**")
            file_a = st.file_uploader("Attach PDF/Image Quote", type=["pdf", "png", "jpg"], key="file_a")
            
        with colB:
            st.markdown("#### Bidder B")
            sub_b = st.selectbox("Select Subcontractor B", [s for s in eligible_subs if s != sub_a], key="sub_b")
            bid_b_amt = st.number_input("Base Bid Amount ($)", min_value=0.0, step=500.0, key="amt_b")
            
            # Real-Time Variance Calculation
            if target_budget > 0 and bid_b_amt > 0:
                var_b = target_budget - bid_b_amt
                if var_b >= 0:
                    st.success(f"**Variance:** Under budget by ${abs(var_b):,.2f}")
                else:
                    st.error(f"**Variance:** Over budget by ${abs(var_b):,.2f}")
                    
            inc_b = st.checkbox("Includes Materials?", key="mat_b")
            pull_b = st.checkbox("Pulls Municipal Permits?", key="perm_b")
            exc_b = st.text_area("Noted Exclusions", key="exc_b")
            
            st.markdown("**Upload Official Quote**")
            file_b = st.file_uploader("Attach PDF/Image Quote", type=["pdf", "png", "jpg"], key="file_b")

        st.divider()
        st.markdown("#### Award Contract")
        winning_sub = st.radio("Select Winning Bidder", [sub_a, sub_b], horizontal=True)
        award_amt = bid_a_amt if winning_sub == sub_a else bid_b_amt
        winning_file = file_a if winning_sub == sub_a else file_b
        
        if st.button("🏆 Award Contract & Save to Vault", type="primary"):
            if award_amt > 0:
                awarded_bids[target_trade] = {
                    "Company": winning_sub,
                    "Awarded_Amount": award_amt,
                    "Date_Awarded": str(date.today())
                }
                
                if winning_file is not None:
                    quote_vault[target_trade] = {
                        "Company": winning_sub,
                        "Filename": winning_file.name,
                        "Type": winning_file.type,
                        "Size_KB": round(winning_file.size / 1024, 2)
                    }
                
                save_state({"awarded_bids": awarded_bids, "quote_vault": quote_vault})
                st.balloons()
                st.success(f"Contract for {target_trade} successfully awarded to {winning_sub} for ${award_amt:,.2f}!")
            else:
                st.error("Cannot award a contract with a $0.00 base bid.")

# ==========================================
# TAB 4: AWARDED CONTRACTS
# ==========================================
with tab_awards:
    st.subheader("Awarded Subcontractor Contracts & Vault")
    st.markdown("Log of all locked-in trades and associated quote documents.")
    
    if awarded_bids:
        awards_list = []
        total_awarded = 0.0
        for trade, details in awarded_bids.items():
            vault_doc = quote_vault.get(trade, {}).get("Filename", "No Document Attached")
            awards_list.append({
                "Trade Phase": trade,
                "Awarded Subcontractor": details["Company"],
                "Contract Amount": details["Awarded_Amount"],
                "Date Awarded": details["Date_Awarded"],
                "Vault Document": vault_doc
            })
            total_awarded += details["Awarded_Amount"]
            
        st.dataframe(
            pd.DataFrame(awards_list), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Contract Amount": st.column_config.NumberColumn("Contract Amount ($)", format="$%.2f")
            }
        )
        st.divider()
        st.metric("Total Committed Contracts", f"${total_awarded:,.2f}")
        st.info("Awarded contracts represent committed hard costs. Ensure your AI-Ingested Actuals in the Proforma align with these totals once invoices are received.")
    else:
        st.info("No contracts have been awarded yet. Use the Bid Leveling tab to award your first trade.")