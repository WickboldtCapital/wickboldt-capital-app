# ==========================================
# 📁 PROJECT CONTROL 
# ==========================================
@st.cache_data(ttl=3600)
def get_all_projects_df():
    with get_read_connection() as conn: 
        # Clean query - no more filtering out fake projects needed!
        return pd.read_sql(text("SELECT project_id, project_name, phase, notes FROM projects"), conn)

def create_project(name, phase, notes, user_email="System"):
    try:
        with get_transaction() as conn: 
            conn.execute(text("INSERT INTO projects (project_name, phase, notes) VALUES (:name, :phase, :notes)"), {"name": name, "phase": phase, "notes": notes})
        log_audit_action(user_email, "CREATE_PROJECT", f"Created project: {name}")
        st.cache_data.clear()
        return True, "Success"
    except Exception as e: 
        return False, str(e)


# ==========================================
# 📚 STANDALONE MASTER LIBRARY
# ==========================================
def init_library_db():
    with get_transaction() as conn:
        # 1. Create a true, standalone table for enterprise documents
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_documents (
                doc_title TEXT PRIMARY KEY,
                doc_content TEXT
            )
        """))
        
        # 2. Seamlessly migrate old data from the projects table if it exists
        try:
            old_row = conn.execute(text("SELECT project_data FROM projects WHERE project_name='__MASTER_LIBRARY__'")).fetchone()
            if old_row and old_row[0]:
                old_dict = json.loads(old_row[0])
                for title, content in old_dict.items():
                    conn.execute(text("""
                        INSERT INTO company_documents (doc_title, doc_content) 
                        VALUES (:t, :c) 
                        ON CONFLICT (doc_title) DO NOTHING
                    """), {"t": title, "c": content})
                
                # 3. Destroy the duct-tape row permanently
                conn.execute(text("DELETE FROM projects WHERE project_name='__MASTER_LIBRARY__'"))
        except Exception:
            pass

@st.cache_data(ttl=3600)
def get_library_state():
    init_library_db() 
    with get_read_connection() as conn:
        rows = conn.execute(text("SELECT doc_title, doc_content FROM company_documents")).fetchall()
        return {row[0]: row[1] for row in rows}

def save_library_state(data, user_email="System"):
    with get_transaction() as conn: 
        for title, content in data.items():
            conn.execute(text("""
                INSERT INTO company_documents (doc_title, doc_content) 
                VALUES (:t, :c) 
                ON CONFLICT (doc_title) DO UPDATE SET doc_content = EXCLUDED.doc_content
            """), {"t": title, "c": content})
    log_audit_action(user_email, "UPDATE_LIBRARY", "Batch modified library templates")
    st.cache_data.clear()

def update_library_doc(doc_title, new_text, user_email="System"):
    with get_transaction() as conn:
        conn.execute(text("""
            INSERT INTO company_documents (doc_title, doc_content) 
            VALUES (:t, :c) 
            ON CONFLICT (doc_title) DO UPDATE SET doc_content = EXCLUDED.doc_content
        """), {"t": doc_title, "c": new_text})
    log_audit_action(user_email, "UPDATE_LIBRARY", f"Modified document: {doc_title}")
    st.cache_data.clear()