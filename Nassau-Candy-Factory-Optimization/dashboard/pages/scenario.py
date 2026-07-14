"""Scenario Analysis page layout."""

import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.utils.helpers import get_cached_recommendations, get_recommender
from dashboard.components.custom_elements import render_page_header, render_chart_container, render_section_header
from dashboard.utils.error_handler import RECOMMENDATION_ERROR

logger = logging.getLogger(__name__)


def render_scenario_page(df_clean) -> None:
    """Renders the scenario weights sliders, dynamic impact cards, and contribution bar chart."""
    
    render_page_header(
        title="Network Scenario Analysis",
        subtitle="Tune multi-objective scoring weights to run hypothetical network simulations and evaluate freight savings contribution."
    )

    # 1. Weights Sliders (Filtered Panel)
    st.markdown("""
    <div style="background-color: #20232A; border-radius: 12px; padding: 1.25rem 1.5rem; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
        <div style="color: #FFFFFF; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #FF6B00;">
            🛠️ Utility Function Tuning Panel
        </div>
    """, unsafe_allow_html=True)

    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        w_spd = st.slider("Fulfillment Speed (w_speed)", 0.0, 1.0, 0.4, 0.05, key="scen_w_spd")
    with col_w2:
        w_prf = st.slider("Freight Savings (w_profit)", 0.0, 1.0, 0.4, 0.05, key="scen_w_prf")
    with col_w3:
        w_rsk = st.slider("Transition Risk Tolerance (w_risk)", 0.0, 1.0, 0.2, 0.05, key="scen_w_rsk")
        
    st.markdown("</div>", unsafe_allow_html=True)

    # Get recommender with adjusted weights
    try:
        recommender = get_recommender(weights=(w_spd, w_prf, w_rsk))
        with st.spinner("Running network reallocations..."):
            recs = get_cached_recommendations(weights=(w_spd, w_prf, w_rsk))
    except Exception:
        logger.exception("Failed to generate scenario recommendations")
        st.error(RECOMMENDATION_ERROR)
        return

    # Isolate top recommendation for each SKU
    primary_recs = []
    for sku, options in recs.items():
        best_opt = options[0]
        primary_recs.append({
            "SKU": sku,
            "Target Factory": best_opt["target_factory"],
            "Savings": best_opt["profit_impact_savings"],
            "Time Improvement (%)": best_opt["lead_time_pct_reduction"]
        })
        
    prim_df = pd.DataFrame(primary_recs)

    # Calculate metrics
    total_savings = prim_df["Savings"].sum()
    avg_network_time_impr = prim_df["Time Improvement (%)"].mean()

    # 2. Display Metrics Row inside custom CSS styled cards
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown(f"""
        <div class="kpi-card" style="height: 110px; display: flex; flex-direction: column; justify-content: center; cursor: default;">
            <div class="kpi-card-header">
                <span class="kpi-card-icon">💰</span>
                <span class="kpi-card-label">Simulated Annual Freight Savings</span>
            </div>
            <div style="font-size: 2rem; font-weight: 800; color: #10b981; margin-top: 0.25rem;">
                ${total_savings:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_m2:
        st.markdown(f"""
        <div class="kpi-card" style="height: 110px; display: flex; flex-direction: column; justify-content: center; cursor: default;">
            <div class="kpi-card-header">
                <span class="kpi-card-icon">⚡</span>
                <span class="kpi-card-label">Average Transit Time Improvement</span>
            </div>
            <div style="font-size: 2rem; font-weight: 800; color: #E5A93C; margin-top: 0.25rem;">
                {avg_network_time_impr:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Bar Chart Plot wrapped inside ChartContainer
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    render_section_header("Savings Contribution Matrix", "Visualizing simulated outbound freight savings contribution mapped to target factory assignments.")
    
    fig_bar = px.bar(
        prim_df.sort_values(by="Savings", ascending=False),
        x="SKU",
        y="Savings",
        color="Target Factory",
        labels={"Savings": "Estimated Annual Savings ($)"},
        template="plotly_dark",
        color_discrete_sequence=["#FF6B00", "#E5A93C", "#5C54A4", "#49A09D", "#C84B31"]
    )
    
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=10, b=40),
        xaxis=dict(showgrid=False, tickfont=dict(color="#8A8A8A", size=9), title=None),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#8A8A8A", size=10), tickformat="$,.0f"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#8A8A8A", size=10)
        )
    )
    
    render_chart_container("Estimated Freight Savings Contribution by Product SKU", fig_bar)
