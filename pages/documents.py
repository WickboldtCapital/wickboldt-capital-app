import streamlit as st
from storage_ops import upload_document, list_documents, get_secure_url

# --- SECURITY GUARD ---
if st.session_state.get("role") != "Admin":
    st.error("🚨 Access Denied: Administrator privileges required to access the Secure Vault.")
    st.stop()

# ==========================================
# 🖥️ SECURE DOCUMENT LIBRARY UI
# ==========================================
st.title("🔒 Secure Document Library")
st.markdown("Upload, view, and manage secure enterprise documents, engineering specs, and financial files. All files are encrypted at rest.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

# --- UPLOAD PANEL ---
with col1:
    st.markdown("### 📤 Upload File")
    st.info("Files uploaded here are pushed directly to the Supabase secure storage bucket.")
    uploaded_file = st.file_uploader("Select a document", label_visibility="collapsed")
    
    if uploaded_file is not None:
        if st.button("Encrypt & Upload", type="primary", use_container_width=True):
            with st.spinner("Uploading to secure vault..."):
                file_bytes = uploaded_file.getvalue()
                content_type = uploaded_file.type
                
                success, msg = upload_document(uploaded_file.name, file_bytes, content_type)
                if success:
                    st.success(f"✅ Successfully vaulted: {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error(msg)

# --- VAULT BROWSER PANEL ---
with col2:
    st.markdown("### 🗄️ Enterprise Vault")
    
    with st.spinner("Decrypting vault manifest..."):
        documents = list_documents()
        
    if documents:
        # Create a clean UI container for the file list
        for doc in documents:
            doc_name = doc.get('name', 'Unknown File')
            
            # Skip hidden Supabase system files
            if doc_name == ".emptyFolderPlaceholder":
                continue
                
            with st.container():
                c_name, c_action = st.columns([3, 1])
                
                with c_name:
                    st.markdown(f"📄 **{doc_name}**")
                    # Optional: Show file size if available from Supabase metadata
                    size_bytes = doc.get('metadata', {}).get('size', 0)
                    if size_bytes > 0:
                        st.caption(f"Size: {round(size_bytes / 1024, 1)} KB")
                        
                with c_action:
                    # Generate a unique key for each button so Streamlit doesn't get confused
                    if st.button("🔗 Generate Link", key=f"link_{doc_name}", use_container_width=True):
                        secure_url = get_secure_url(doc_name)
                        if secure_url:
                            st.success("Link active for 1 hour!")
                            st.markdown(f"**[Click here to securely view/download]({secure_url})**")
                        else:
                            st.error("Failed to generate link.")
            st.divider()
    else:
        st.info("The secure vault is currently empty. Upload a document to get started.")