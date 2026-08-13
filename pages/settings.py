import streamlit as st
import sqlite3
import json

# --- SECURITY GUARD (ADMIN ONLY) ---
if st.session_state.get("role") != "Admin":
    st.error("⚠️ Access Restricted: Only Administrators can view and edit Global Master Settings.")
    st.stop()

# ==========================================
# 💾 GLOBAL SETTINGS DB ENGINE
# ==========================================
DB_FILE = "wickboldt_projects.db"
GLOBAL_KEY = "__GLOBAL_DEFAULTS__"

def init_global_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN project_data TEXT")
    except sqlite3.OperationalError:
        pass
    # Ensure the hidden global row exists
    conn.execute("INSERT OR IGNORE INTO projects (project_name, project_data) VALUES (?, ?)", (GLOBAL_KEY, "{}"))
    conn.commit()
    conn.close()

init_global_db()

def get_global_state():
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (GLOBAL_KEY,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else {}

db_state = get_global_state()

def auto_save_global(key):
    val = st.session_state[key]
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT project_data FROM projects WHERE project_name=?", (GLOBAL_KEY,)).fetchone()
    current_state = json.loads(row[0]) if row and row[0] else {}
    current_state[key] = val
    conn.execute("UPDATE projects SET project_data=? WHERE project_name=?", (json.dumps(current_state), GLOBAL_KEY))
    conn.commit()
    conn.close()

def bound(val, minimum, maximum):
    if minimum is not None: val = max(val, minimum)
    if maximum is not None: val = min(val, maximum)
    return val

def auto_num(label, key, default, container=st, step=None, min_value=None, max_value=None):
    saved_val = bound(float(db_state.get(key, default)), min_value, max_value)
    return container.number_input(label, value=saved_val, step=step, min_value=min_value, max_value=max_value, key=key, on_change=auto_save_global, args=(key,))

def auto_slider(label, key, min_value, max_value, default, container=st, step=None):
    saved_val = bound(float(db_state.get(key, default)), min_value, max_value)
    return container.slider(label, min_value=float(min_value), max_value=float(max_value), value=saved_val, step=step, key=key, on_change=auto_save_global, args=(key,))

# --- HEADER ---
st.header("⚙️ Master Global Settings")
st.markdown("Values set here become the standard default for all **new** projects created by users across the portal. Existing saved projects will retain their custom overrides.")
st.markdown("---")

st.subheader("🏦 Capital Stack & Debt Defaults")

c_col, r_col = st.columns(2)

with c_col:
    st.markdown("#### Construction Loan Standards")
    auto_num("Default Const. Target Rent ($)", "Construction_rent", 4500.0, step=100.0)
    auto_slider("Default Const. Vacancy (%)", "Construction_vac", 1.0, 15.0, 5.0, step=1.0)
    auto_slider("Default Const. Equity Position (%)", "const_eq_pct", 5.0, 40.0, 25.0, step=5.0)
    auto_slider("Default Underwriting Rate (%)", "const_uw_rate", 0.0, 15.0, 7.50, step=0.25)
    auto_num("Default Const. DSCR Target", "const_tgt_dscr", 1.20, step=0.05)
    auto_slider("Default Actual Const. Rate (%)", "const_act_rate", 0.0, 15.0, 6.25, step=0.25)

with r_col:
    st.markdown("#### Permanent Refinance Standards")
    auto_num("Default Refi Target Rent ($)", "Refinance_rent", 5100.0, step=100.0)
    auto_slider("Default Refi Vacancy (%)", "Refinance_vac", 1.0, 15.0, 5.0, step=1.0)
    auto_slider("Default Refi Equity Position (%)", "refi_eq_pct", 5.0, 40.0, 35.0, step=5.0)
    auto_slider("Default Base Refi Rate (%)", "refi_base_rate", 0.0, 10.0, 6.25, step=0.125)
    auto_slider("Default Points", "refi_points", 0.0, 4.0, 3.0, step=0.25)
    auto_num("Default Refi DSCR Target", "refi_tgt_dscr", 1.20, step=0.05)