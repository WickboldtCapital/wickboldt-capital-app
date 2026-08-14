import streamlit as st
from db_ops import get_all_users_df, add_new_user, update_user_role, update_password, delete_user

if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: You must be logged in as an Administrator to view this page.")
    st.stop()

st.markdown("### 🔐 User & Access Management")
st.markdown("Add, edit, or revoke access for team members and partners. Only Administrators can access this console.")
st.markdown("---")

users_df = get_all_users_df()

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### ➕ Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        new_email = st.text_input("User Email Address")
        new_password = st.text_input("Assign Initial Password", type="password")
        new_role = st.selectbox("Assign Role", ["Standard User", "Admin"])
        
        if st.form_submit_button("Create User"):
            if new_email and new_password:
                success, message = add_new_user(new_email, new_password, new_role)
                if success:
                    st.success(f"Added {new_email} as {new_role}.")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter an email address and a password.")

with col2:
    st.markdown("#### ⚙️ Modify or Delete User")
    if users_df is not None and not users_df.empty:
        safe_users = users_df[users_df['email'] != 'steve.wickboldt.jr@gmail.com']['email'].tolist()
        
        if safe_users:
            with st.form("modify_user_form"):
                selected_user = st.selectbox("Select User to Modify", safe_users)
                new_assigned_role = st.selectbox("Update Role", ["Standard User", "Admin"])
                new_reset_pw = st.text_input("Reset Password (Leave blank to keep current)", type="password")
                
                col_update, col_delete = st.columns(2)
                
                update_btn = col_update.form_submit_button("💾 Save Changes")
                delete_btn = col_delete.form_submit_button("🗑️ Delete User")
                
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
            st.info("No other users in the system to modify.")

st.markdown("---")
st.markdown("#### 📋 Active System Users")
if users_df is not None:
    st.dataframe(
        users_df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "email": "Email Address",
            "role": "System Role"
        }
    )