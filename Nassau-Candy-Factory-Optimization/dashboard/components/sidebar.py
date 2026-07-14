"""Sidebar component for global filtering and navigation."""

import streamlit as st


def render_sidebar():
    """Renders the custom sidebar branding, navigation, and user profile."""
    
    # 1. Company Branding
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; padding-bottom: 1.5rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 1.5rem;">
        <div style="background-color: #FF6B00; border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-weight: 800; color: #FFFFFF; font-size: 1.3rem; margin-right: 10px;">
            N
        </div>
        <div>
            <div style="color: #FFFFFF; font-weight: 700; font-size: 1.1rem; line-height: 1.2;">Nassau Candy</div>
            <div style="color: #8A8A8A; font-weight: 600; font-size: 0.85rem;">Decision Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Navigation
    st.sidebar.markdown("<div class='sidebar-section-header'>Platform Navigation</div>", unsafe_allow_html=True)
    
    pages = {
        "Executive Dashboard": "📊 Executive Overview",
        "Factory Simulator": "⚙️ Factory Route Simulator",
        "Recommendation Dashboard": "🏆 Reallocation Matrix",
        "Scenario Analysis": "🎛️ Network Scenario Analysis",
        "Risk Dashboard": "🚨 Risk & Constraints Matrix"
    }

    if "page" not in st.session_state:
        st.session_state.page = "Executive Dashboard"

    # Dynamic styling to highlight the active menu button
    active_key = st.session_state.page.lower().replace(" ", "_")
    st.sidebar.markdown(f"""
    <style>
        div.element-container:has(button[key="nav_{active_key}"]) button {{
            background-color: #20232A !important;
            color: #FFFFFF !important;
            border-left: 4px solid #FF6B00 !important;
            font-weight: 700 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    for p_name, p_label in pages.items():
        key_name = f"nav_{p_name.lower().replace(' ', '_')}"
        if st.sidebar.button(p_label, key=key_name, use_container_width=True):
            st.session_state.page = p_name
            st.rerun()

    st.sidebar.markdown("---")

    # 3. Global Filters (Pills)
    st.sidebar.markdown("<div class='sidebar-section-header'>Product Division</div>", unsafe_allow_html=True)
    
    if "filter_divs" not in st.session_state:
        st.session_state.filter_divs = {"Chocolate": True, "Sugar": True, "Other": True}

    col_div1, col_div2, col_div3 = st.sidebar.columns(3)
    with col_div1:
        choc_active = st.session_state.filter_divs["Chocolate"]
        if st.button("Choc", key="pill_choc", type="primary" if choc_active else "secondary", use_container_width=True):
            st.session_state.filter_divs["Chocolate"] = not choc_active
            st.rerun()
    with col_div2:
        sugar_active = st.session_state.filter_divs["Sugar"]
        if st.button("Sugar", key="pill_sugar", type="primary" if sugar_active else "secondary", use_container_width=True):
            st.session_state.filter_divs["Sugar"] = not sugar_active
            st.rerun()
    with col_div3:
        other_active = st.session_state.filter_divs["Other"]
        if st.button("Other", key="pill_other", type="primary" if other_active else "secondary", use_container_width=True):
            st.session_state.filter_divs["Other"] = not other_active
            st.rerun()

    st.sidebar.markdown("<div class='sidebar-section-header'>Customer Regions</div>", unsafe_allow_html=True)

    if "filter_regions" not in st.session_state:
        st.session_state.filter_regions = {
            "Pacific": True,
            "Atlantic": True,
            "Interior": True,
            "Gulf": True
        }

    col_reg1, col_reg2 = st.sidebar.columns(2)
    with col_reg1:
        pac_active = st.session_state.filter_regions["Pacific"]
        if st.button("Pacific", key="pill_pac", type="primary" if pac_active else "secondary", use_container_width=True):
            st.session_state.filter_regions["Pacific"] = not pac_active
            st.rerun()
            
        int_active = st.session_state.filter_regions["Interior"]
        if st.button("Interior", key="pill_int", type="primary" if int_active else "secondary", use_container_width=True):
            st.session_state.filter_regions["Interior"] = not int_active
            st.rerun()
            
    with col_reg2:
        atl_active = st.session_state.filter_regions["Atlantic"]
        if st.button("Atlantic", key="pill_atl", type="primary" if atl_active else "secondary", use_container_width=True):
            st.session_state.filter_regions["Atlantic"] = not atl_active
            st.rerun()
            
        gulf_active = st.session_state.filter_regions["Gulf"]
        if st.button("Gulf", key="pill_gulf", type="primary" if gulf_active else "secondary", use_container_width=True):
            st.session_state.filter_regions["Gulf"] = not gulf_active
            st.rerun()

    # Reset Filters Button
    st.sidebar.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("🔄 Reset Global Filters", key="reset_filters", use_container_width=True):
        st.session_state.filter_divs = {"Chocolate": True, "Sugar": True, "Other": True}
        st.session_state.filter_regions = {"Pacific": True, "Atlantic": True, "Interior": True, "Gulf": True}
        st.rerun()

    st.sidebar.markdown("---")

    # 4. Enterprise Branding Footer & User Info Box
    st.sidebar.markdown("""
    <div class="sidebar-user-box">
        <div class="sidebar-avatar">N</div>
        <div class="sidebar-user-info">
            <span class="sidebar-username">Nassau Exec</span>
            <span class="sidebar-user-role">Operations Director</span>
        </div>
    </div>
    <div style="text-align: center; color: #8A8A8A; font-size: 0.75rem; margin-top: 1.5rem; letter-spacing: 0.05em;">
        SYSTEM STATUS: <span style="color: #10b981; font-weight: 700;">● ONLINE</span>
    </div>
    """, unsafe_allow_html=True)

    # Style button overrides
    st.sidebar.markdown("""
    <style>
        div[data-testid="stSidebar"] div.stButton > button {
            border-radius: 20px !important;
            background-color: #20232A !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #8A8A8A !important;
            font-size: 0.8rem !important;
            padding: 0.25rem 0.5rem !important;
            height: auto !important;
            transition: all 0.15s ease-in-out !important;
        }
        
        div[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #FF6B00 !important;
            border-color: #FF6B00 !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stSidebar"] div.stButton > button:hover {
            color: #FFFFFF !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(-1px);
        }
    </style>
    """, unsafe_allow_html=True)
