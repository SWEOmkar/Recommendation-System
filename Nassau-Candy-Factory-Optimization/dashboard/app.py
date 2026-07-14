"""Main Streamlit entry point coordinating the multi-page logistics dashboard."""

import os
import sys
import logging
import streamlit as st

logger = logging.getLogger(__name__)

# Setup dynamic paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)
sys.path.append(os.path.join(project_root, "src"))

# Set page config
st.set_page_config(
    page_title="Nassau Candy Decision Intelligence Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and inject custom CSS style sheet
css_path = os.path.join(current_dir, "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Imports from modular architecture
from dashboard.components.sidebar import render_sidebar
from dashboard.utils.helpers import load_clean_dataset
from dashboard.utils.error_handler import safe_page_execution, DATA_LOAD_ERROR, PAGE_RENDER_ERROR
from dashboard.pages.executive import render_executive_page
from dashboard.pages.simulator import render_simulator_page
from dashboard.pages.recommendations import render_recommendations_page
from dashboard.pages.scenario import render_scenario_page
from dashboard.pages.risk import render_risk_page

# Load Clean Dataset
try:
    df_raw = load_clean_dataset()
except Exception:
    logger.exception("Critical failure loading dataset")
    st.error(DATA_LOAD_ERROR)
    st.stop()

# Render Sidebar Navigation and Filters
render_sidebar()

# Apply Filters from Session State
active_divs = st.session_state.filter_divs
active_regs = st.session_state.filter_regions

# Filter DataFrame
filtered_divs = [div for div, active in active_divs.items() if active]
filtered_regs = [reg for reg, active in active_regs.items() if active]

df_filtered = df_raw[
    (df_raw["Division"].isin(filtered_divs)) &
    (df_raw["Region"].isin(filtered_regs))
]

# Page Router
with safe_page_execution(st.session_state.page):
    if st.session_state.page == "Executive Dashboard":
        render_executive_page(df_filtered)

    elif st.session_state.page == "Factory Simulator":
        render_simulator_page(df_filtered)

    elif st.session_state.page == "Recommendation Dashboard":
        render_recommendations_page(df_filtered, active_divs)

    elif st.session_state.page == "Scenario Analysis":
        render_scenario_page(df_filtered)

    elif st.session_state.page == "Risk Dashboard":
        render_risk_page(df_filtered)
