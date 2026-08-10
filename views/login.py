import streamlit as st
from core_backend import get_logo_html
# We import our clean functions instead of writing SQL here
from db_ops import authenticate_user, update_password

ui_placeholder = st.empty()

with ui_placeholder.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(get_logo_html(), unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Proforma Development Portal</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
        if submit:
            # Look how clean this is now!
            role = authenticate_user(email, password)
            
            if role:
                st.session_state.update({"logged_in": True, "email": email.lower().strip(), "role": role})
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