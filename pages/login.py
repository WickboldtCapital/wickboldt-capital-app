import streamlit as st
import os
from db_ops import authenticate_user, update_password

ui_placeholder = st.empty()

with ui_placeholder.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Bulletproof image loader looking in the assets folder
        # We check common variations to avoid Linux case-sensitivity crashes
        logo_path = None
        if os.path.exists("assets/logo.png"):
            logo_path = "assets/logo.png"
        elif os.path.exists("assets/Logo.png"):
            logo_path = "assets/Logo.png"
        elif os.path.exists("assets/logo.svg"):
            logo_path = "assets/logo.svg"
            
        if logo_path:
            try:
                st.image(logo_path, use_container_width=True)
            except Exception:
                st.caption("(Corporate logo rendering error...)")
        else:
            st.markdown("<h2 style='text-align: center;'>🏗️ Wickboldt Capital</h2>", unsafe_allow_html=True)
            st.caption("(Corporate logo syncing to cloud...)")
            
        st.markdown("<h3 style='text-align: center;'>Proforma Development Portal</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
        if submit:
            role = authenticate_user(email, password)
            
            if role:
                # Store the role in Title Case (e.g., "Admin") for UI consistency
                clean_role = str(role).strip().capitalize()
                st.session_state.update({
                    "logged_in": True, 
                    "email": email.lower().strip(), 
                    "role": clean_role
                })
                ui_placeholder.empty()
                st.rerun()
            else:
                st.error("Invalid email or password.")
                    
        with st.expander("🔑 Account Recovery"):
            with st.form("self_reset_form"):
                reset_email = st.text_input("Confirm Account Email", value="steve.wickboldt.jr@gmail.com")
                new_reset_pw = st.text_input("New Password", type="password")
                if st.form_submit_button("Update Password Now"):
                    # One clean function call
                    update_password(reset_email, new_reset_pw)
                    st.success("Password updated successfully!")