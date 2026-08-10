import streamlit as st
import sqlite3
from datetime import datetime

# Explicitly set page config with your SVG logo favicon
st.set_page_config(
    page_title="Wickboldt Capital - Master Development Portal",
    page_icon="assets/logo.svg",
    layout="wide"
)

DB_FILE = "wickboldt_projects.db"

# Initialize public inquiry table if not exists
def init_public_crm():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS public_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            inquiry_type TEXT,
            message TEXT,
            date_logged TEXT
        )
    """)
    conn.commit()
    conn.close()

init_public_crm()

# --- INITIALIZE PUBLIC NAVIGATION STATE ---
if "public_subpage" not in st.session_state:
    st.session_state["public_subpage"] = "Home"

# ==========================================
# 🌐 PROFESSIONAL WEBSITE HEADER BAR
# ==========================================
header_col1, header_col2, header_col3 = st.columns([2, 5, 2])

with header_col1:
    st.markdown("### 🏗️ **Wickboldt Capital**")
    st.markdown("<p style='font-size: 0.8rem; color: #C5A059; margin-top: -15px;'><i>Today's Foundation. Tomorrow's Legacy.</i></p>", unsafe_allow_html=True)

with header_col2:
    # Top navigation bar links using small inline radio selection
    nav_selection = st.radio(
        "Navigation",
        ["Home", "Portfolio & Master Plan", "Architecture & Quality", "About Us", "Contact"],
        horizontal=True,
        label_visibility="collapsed",
        key="public_nav_radio"
    )
    if nav_selection != st.session_state["public_subpage"]:
        st.session_state["public_subpage"] = nav_selection
        st.rerun()

with header_col3:
    if st.button("🔒 Stakeholder Sign In", use_container_width=True, type="primary"):
        st.session_state["nav_mode"] = "login"
        st.rerun()

st.markdown("---")

# ==========================================
# 🏠 SUB-PAGE 1: HOME (LANDING HERO)
# ==========================================
if st.session_state["public_subpage"] == "Home":
    # Hero Section
    st.markdown(
        "<div style='background-color: #0B3C5D; padding: 40px; border-radius: 10px; text-align: center; color: white;'>"
        "<h1 style='color: white; margin-bottom: 5px;'>Premier Build-to-Rent Residential Development</h1>"
        "<p style='font-size: 1.2rem; color: #C5A059;'>Master Planned Communities in Hammond, Louisiana</p>"
        "</div>",
        unsafe_allow_html=True
    )
    st.write("")

    # Key Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Master Plan", "24 Lots")
    m2.metric("Asset Class", "Build-to-Rent (BTR)")
    m3.metric("Location", "Hammond, LA")
    m4.metric("University Proximity", "< 1 Mile to SLU")

    st.markdown("---")

    # Image Placeholder Section 1
    col_img1, col_text1 = st.columns([1, 1])
    with col_img1:
        st.markdown(
            "<div style='border: 2px dashed #C5A059; padding: 60px; text-align: center; border-radius: 8px; background-color: #f9f9f9;'>"
            "📷 <b>[ Placeholder: Front Exterior Architectural Rendering ]</b><br>"
            "<span style='font-size: 0.85rem; color: gray;'>Narrow-footprint 2-story 3BR/2.5BA single-family home with single-car garage</span>"
            "</div>",
            unsafe_allow_html=True
        )
    with col_text1:
        st.markdown("### Institutional-Grade Residential Portfolios")
        st.markdown(
            "Wickboldt Capital specializes in acquiring strategically positioned parcels and developing high-efficiency, "
            "narrow-footprint single-family rental homes. Designed specifically to capture dual-demographic demand from university "
            "faculty/students and local regional workforce personnel along the I-12 and I-55 logistics corridor."
        )
        if st.button("Explore Master Plan →", key="btn_to_master"):
            st.session_state["public_subpage"] = "Portfolio & Master Plan"
            st.rerun()

    st.markdown("---")

    # Image Placeholder Section 2
    col_text2, col_img2 = st.columns([1, 1])
    with col_text2:
        st.markdown("### Superior Construction & Long-Term Value")
        st.markdown(
            "Every Wickboldt Capital development is built to uncompromising standards. Utilizing 2x6 framing, closed-cell "
            "spray foam insulation, and rigorous Manual J/S/D/T HVAC engineering, our properties slash tenant utility burdens "
            "by up to 50% while guaranteeing extreme structural durability and minimal ongoing maintenance overhead."
        )
        if st.button("View Engineering Specs →", key="btn_to_arch"):
            st.session_state["public_subpage"] = "Architecture & Quality"
            st.rerun()
    with col_img2:
        st.markdown(
            "<div style='border: 2px dashed #0B3C5D; padding: 60px; text-align: center; border-radius: 8px; background-color: #f9f9f9;'>"
            "📷 <b>[ Placeholder: Interior Finish & Kitchen Rendering ]</b><br>"
            "<span style='font-size: 0.85rem; color: gray;'>Quartz countertops, 20 mil LVP flooring, commercial-grade fixtures</span>"
            "</div>",
            unsafe_allow_html=True
        )

# ==========================================
# 🗺️ SUB-PAGE 2: PORTFOLIO & MASTER PLAN
# ==========================================
elif st.session_state["public_subpage"] == "Portfolio & Master Plan":
    st.subheader("Rogers Moore Parkway Master Development")
    st.markdown("Located in Hammond, Louisiana — a booming micro-urban hub in Tangipahoa Parish.")
    
    st.markdown(
        "<div style='border: 2px dashed #0B3C5D; padding: 80px; text-align: center; border-radius: 8px; background-color: #f9f9f9; margin-bottom: 20px;'>"
        "🗺️ <b>[ Placeholder: Interactive Master Site Map - Rogers Moore Parkway ]</b><br>"
        "<span style='font-size: 0.85rem; color: gray;'>Phase 1 (10 Lots fronting Rogers Moore & Center Ave) & Phase 2 (14 Expansion Lots)</span>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("#### Master Phasing Structure")
    master_data = {
        "Phase": ["Phase One", "Phase One", "Phase Two"],
        "Lot Count": ["3 Lots", "7 Lots", "14 Lots"],
        "Designation": ["Tracts C1–3 (Active Loan Tranche)", "Remaining Phase One Frontage", "Phase Two Interior Expansion"],
        "Location / Alignment": ["Fronting Rogers Moore Pkwy & Center Ave", "Fronting Rogers Moore Pkwy & Center Ave", "Interior Master Development Corridor"],
        "Status": ["Underwriting / Active", "Scheduled Rollout", "Planning & Entitlement"]
    }
    st.table(pd.DataFrame(master_data))

# ==========================================
# 🏗️ SUB-PAGE 3: ARCHITECTURE & QUALITY
# ==========================================
elif st.session_state["public_subpage"] == "Architecture & Quality":
    st.subheader("Architectural Integrity & Technical Engineering")
    st.markdown("Engineered for maximum thermal efficiency, low operational overhead, and long-term asset resilience.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🧱 Structural Envelope")
        st.markdown("* **Foundation:** Elevated stem wall system (30-inch stem wall with integrated foam brick ledge).")
        st.markdown("* **Framing:** Robust 2x6 wood-frame construction with 9-foot ceilings.")
        st.markdown("* **Insulation:** Fully encapsulated closed-cell spray foam roof insulation and open-cell wall foam.")
        st.markdown("* **Footprint:** Optimized 1,150 sq ft two-story narrow footprint (3BR / 2.5BA / Single-car garage).")
    
    with col_b:
        st.markdown("#### ⚡ Mechanical & Interior Finishes")
        st.markdown("* **HVAC:** 1.5-ton ducted mini-split engineered strictly to Manual J, S, D, and T standards.")
        st.markdown("* **Air Circulation:** Integrated BLDC ceiling fans for enhanced physiological cooling.")
        st.markdown("* **Fixtures:** Solid brass ceramic-disc cartridge plumbing fixtures (Moen/Delta).")
        st.markdown("* **Surfaces:** Premium quartz countertops and commercial-grade 20 mil LVP flooring.")

# ==========================================
# 🏢 SUB-PAGE 4: ABOUT US
# ==========================================
elif st.session_state["public_subpage"] == "About Us":
    st.subheader("About Wickboldt Capital")
    st.markdown("Manufacturing institutional-grade equity from the ground up through disciplined real estate development.")
    
    st.markdown(
        "**Wickboldt Capital** is led by **Stephen J. Wickboldt, Jr.**, a licensed general contractor in the State of Louisiana "
        "with 30 years of comprehensive construction experience, including 22 years in offshore oil and gas engineering projects "
        "and 3 years in residential construction.\n\n"
        "Our development philosophy is rooted in foundational discipline: identifying undervalued parcels, securing municipal "
        "entitlements, and executing high-efficiency build-to-rent asset creation. By combining rigorous engineering standards with "
        "a long-term 'build, rent, and hold' strategy, Wickboldt Capital mitigates speculative market risks while delivering "
        "superior, tax-shielded cash flow streams across market cycles."
    )
    
    st.markdown("> *Today's Foundation. Tomorrow's Legacy.*")

# ==========================================
# 📞 SUB-PAGE 5: CONTACT & INQUIRIES
# ==========================================
elif st.session_state["public_subpage"] == "Contact":
    st.subheader("Inquiries & Stakeholder Contact")
    st.markdown("Interested in partnership, investor relations, or leasing availability at Rogers Moore Parkway? Get in touch below.")
    
    with st.form("public_contact_form"):
        c1, c2 = st.columns(2)
        p_name = c1.text_input("Full Name")
        p_email = c1.text_input("Email Address")
        p_phone = c2.text_input("Phone Number")
        p_type = c2.selectbox("Inquiry Type", ["Private Investor / Lender", "Prospective Tenant", "General Inquiry", "Broker / Partner"])
        p_message = st.text_area("Your Message")
        
        p_submitted = st.form_submit_button("Submit Inquiry")
        if p_submitted:
            if p_name and p_email:
                conn = sqlite3.connect(DB_FILE)
                conn.execute(
                    "INSERT INTO public_inquiries (name, email, phone, inquiry_type, message, date_logged) VALUES (?, ?, ?, ?, ?, ?)",
                    (p_name, p_email, p_phone, p_type, p_message, datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                conn.close()
                st.success("✅ Thank you! Your inquiry has been received by the Wickboldt Capital team.")
            else:
                st.warning("⚠️ Please provide at least your name and email address.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.85rem;'>© 2026 Wickboldt Capital. All Rights Reserved. Licensed General Contractor — State of Louisiana.</p>", unsafe_allow_html=True)