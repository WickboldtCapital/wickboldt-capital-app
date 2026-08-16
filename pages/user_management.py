import streamlit as st
import sqlite3
import pandas as pd
from db_ops import get_all_users_df, add_new_user, update_user_role, update_password, delete_user

st.set_page_config(page_title="User Management", layout="wide")

# ==========================================
# 🔒 STRICT ADMIN-ONLY SECURITY GUARD
# ==========================================
if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: You must be logged in as an Administrator to view this page.")
    st.stop()

st.title("🔐 User Access & Security Management")
st.markdown("Add, edit, or revoke access for team members and partners. Monitor enterprise audit logs.")
st.divider()

users_df = get_all_users_df()
enterprise_roles = ["Viewer", "Standard User", "Investor", "Manager", "Admin"]

# ==========================================
# 👥 USER CREATION & MODIFICATION
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("➕ Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        new_email = st.text_input("User Email Address")
        new_password = st.text_input("Assign Initial Password", type="password")
        new_role = st.selectbox("Assign Role", enterprise_roles)
        
        st.caption("Roles define what modules and data this user can interact with.")
        if st.form_submit_button("Create User", type="primary", use_container_width=True):
            if new_email and new_password:
                success, message = add_new_user(new_email.lower().strip(), new_password, new_role)
                if success:
                    st.success(f"Added {new_email} as {new_role}.")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter an email address and a password.")

with col2:
    st.subheader("⚙️ Modify or Delete User")
    if users_df is not None and not users_df.empty:
        # Protect the master admin account from being modified or deleted
        safe_users = users_df[users_df['email'] != 'steve.wickboldt.jr@gmail.com']['email'].tolist()
        
        if safe_users:
            with st.form("modify_user_form"):
                selected_user = st.selectbox("Select User to Modify", safe_users)
                new_assigned_role = st.selectbox("Update Role", enterprise_roles)
                new_reset_pw = st.text_input("Reset Password (Leave blank to keep current)", type="password")
                
                col_update, col_delete = st.columns(2)
                
                update_btn = col_update.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                delete_btn = col_delete.form_submit_button("🗑️ Delete User", use_container_width=True)
                
                if update_btn:
                    update_user_role(selected_user, new_assigned_role)
                    if new_reset_pw:
                        update_password(selected_user, new_reset_pw)
                        st.success(f"Updated role to {new_assigned_role} and reset password for {selected_user}.")
                    else:
                        st.success(f"Updated {selected_user} to {new_assigned_role}.")
                    st.rerun()
                    
                if delete_btn:
                    success, message = delete_user(selected_user)
                    if success:
                        st.success(f"Revoked access for {selected_user}.")
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("No other standard users in the system to modify.")

st.divider()

# ==========================================
# 📋 DIRECTORY & AUDIT LOGS
# ==========================================
col3, col4 = st.columns([1, 1.5])

with col3:
    st.subheader("📋 Active System Users")
    if users_df is not None and not users_df.empty:
        st.dataframe(
            users_df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "email": "Email Address",
                "role": "System Role"
            }
        )

with col4:
    st.subheader("🛡️ Security Audit Log")
    st.caption("Monitor recent logins, logouts, and system actions.")
    
    # Direct DB call to fetch logs dynamically without needing to alter db_ops.py
    def get_audit_logs_local():
        try:
            conn = sqlite3.connect("wickboldt_projects.db")
            df = pd.read_sql_query("SELECT user_email, action, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 100", conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame(columns=["user_email", "action", "details", "timestamp"])

    logs_df = get_audit_logs_local()
    if not logs_df.empty:
        st.dataframe(
            logs_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "user_email": "Target User",
                "action": "Action Type",
                "details": "Details",
                "timestamp": "Timestamp (UTC)"
            }
        )
    else:
        st.info("No audit logs recorded yet. System will populate this automatically.")