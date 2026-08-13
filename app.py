# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state: 
    st.session_state["logged_in"] = False
if "active_project" not in st.session_state:
    st.session_state["active_project"] = None
if "nav_mode" not in st.session_state:
    st.session_state["nav_mode"] = "home"
if "role" not in st.session_state:
    st.session_state["role"] = "Admin"  # Forces Admin role by default
if "email" not in st.session_state:
    st.session_state["email"] = "steve.wickboldt.jr@gmail.com"