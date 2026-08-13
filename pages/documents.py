import streamlit as st
from storage_ops import upload_document, list_documents, get_secure_url
from db_ops import log_audit_action

st.title("Secure Document Library 📁")
st.markdown("Upload and manage encrypted project files. All downloads use temporary, expiring URLs.")

# --- UPLOAD SECTION ---
with st.expander("⬆️ Upload New Document", expanded=True):
    uploaded_file = st.file_uploader("Select PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
    if st.button("Secure Upload"):
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            success, msg = upload_document(uploaded_file.name, file_bytes, uploaded_file.type)
            
            if success:
                # Log this action to our audit ledger
                log_audit_action(st.session_state.get("email"), "UPLOAD_DOCUMENT", f"Uploaded {uploaded_file.name}")
                st.success(f"**{uploaded_file.name}** securely vaulted!")
                st.rerun() # Refresh the page to show the new file
            else:
                st.error(msg)
        else:
            st.warning("Please select a file first.")

st.divider()

# --- VIEW & DOWNLOAD SECTION ---
st.subheader("Available Documents")
docs = list_documents()

if not docs:
    st.info("The secure vault is currently empty.")
else:
    for doc in docs:
        doc_name = doc['name']
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"📄 **{doc_name}**")
            
        with col2:
            if st.button("Generate Secure Link", key=doc_name):
                # Generates a link that self-destructs in 60 seconds
                secure_url = get_secure_url(doc_name, expires_in=60) 
                
                if secure_url:
                    st.markdown(f"[Click Here to Download/View]({secure_url}) *(Link expires in 60s)*")
                    log_audit_action(st.session_state.get("email"), "GENERATE_DOC_LINK", f"Accessed {doc_name}")
                else:
                    st.error("Failed to generate secure link.")