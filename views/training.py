import streamlit as st
from db_ops import get_all_training_modules, add_training_module, get_user_completed_modules, mark_module_completed

st.title("Enterprise Training & SOPs 📚")
st.markdown("Review required safety guidelines, operating procedures, and project manuals.")

user_email = st.session_state.get("email", "Unknown")
user_role = st.session_state.get("role", "viewer").lower()

# --- ADMIN SECTION: CREATE NEW CONTENT ---
if user_role == "admin":
    with st.expander("⚙️ Admin: Publish New Training Module"):
        with st.form("new_training_form", clear_on_submit=True):
            t_title = st.text_input("Module Title")
            t_category = st.selectbox("Category", ["Safety", "Standard Operating Procedure (SOP)", "Onboarding", "Technical Guide"])
            t_content = st.text_area("Content (Markdown supported)", height=200)
            
            if st.form_submit_button("Publish Module", type="primary"):
                if t_title and t_content:
                    add_training_module(t_title, t_category, t_content, user_email)
                    st.success("Training module published successfully!")
                    st.rerun()
                else:
                    st.error("Title and Content are required.")

st.divider()

# --- USER SECTION: READ & SIGN OFF ---
modules_df = get_all_training_modules()
completed_ids = get_user_completed_modules(user_email)

if modules_df.empty:
    st.info("No training modules have been published yet.")
else:
    # Group by category for clean display
    categories = modules_df['category'].unique()
    
    for cat in categories:
        st.subheader(f"📂 {cat}")
        cat_modules = modules_df[modules_df['category'] == cat]
        
        for _, row in cat_modules.iterrows():
            is_done = row['id'] in completed_ids
            status_icon = "✅" if is_done else "⚠️"
            
            with st.expander(f"{status_icon} {row['title']}"):
                st.markdown(row['content'])
                st.divider()
                
                if is_done:
                    st.success(f"You have completed this module.")
                else:
                    if st.button("Mark as Read & Understood", key=f"read_{row['id']}"):
                        mark_module_completed(user_email, row['id'], row['title'])
                        st.balloons()
                        st.rerun()