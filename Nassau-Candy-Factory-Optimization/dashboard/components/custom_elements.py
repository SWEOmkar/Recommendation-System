"""Reusable premium enterprise layout components for the Nassau Candy Dashboard."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_page_header(title: str, subtitle: str) -> None:
    """Renders a standard enterprise page header with borders and metadata."""
    html = f'<div class="page-header-container"><h1 class="page-title">{title}</h1><div class="page-subtitle">{subtitle}</div></div>'
    st.html(html)


def render_section_header(title: str, subtitle: str = None) -> None:
    """Renders a section title with optional subtitle description."""
    sub_html = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ''
    html = f'<div class="section-header-container"><h2 class="section-title">{title}</h2>{sub_html}</div>'
    st.html(html)


def render_chart_container(title: str, fig: go.Figure) -> None:
    """Wraps a Plotly chart inside a styled dark-slate container."""
    st.html(f'<div class="chart-container"><div class="chart-title">{title}</div>')
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.html('</div>')


def render_risk_alert(title: str, text: str, level: str = "warning", icon: str = "🚨") -> None:
    """Renders a custom warning or risk notification block."""
    bg_colors = {
        "warning": "rgba(229, 169, 60, 0.05)",
        "error": "rgba(239, 68, 68, 0.05)",
        "success": "rgba(16, 185, 129, 0.05)"
    }
    border_colors = {
        "warning": "rgba(229, 169, 60, 0.2)",
        "error": "rgba(239, 68, 68, 0.2)",
        "success": "rgba(16, 185, 129, 0.2)"
    }
    
    bg = bg_colors.get(level, bg_colors["warning"])
    border = border_colors.get(level, border_colors["warning"])
    
    html = (
        f'<div class="stitch-alert" style="background: {bg}; border: 1px solid {border};">'
        f'<div class="stitch-alert-icon">{icon}</div>'
        f'<div class="stitch-alert-content">'
        f'<div class="stitch-alert-title">{title}</div>'
        f'<div class="stitch-alert-text">{text}</div>'
        f'</div>'
        f'</div>'
    )
    st.html(html)


def render_recommendation_card(
    sku: str,
    current_factory: str,
    recommended_factory: str,
    time_reduction_pct: float,
    freight_savings: float,
    profit_impact: float,
    confidence_score: float,
    priority: str,
    reason: str
) -> None:
    """Renders an executive decision card highlighting a single reallocation scenario."""
    priority_class = priority.lower()
    
    html = (
        f'<div class="rec-card">'
        f'<div class="rec-card-header">'
        f'<div class="rec-card-route">'
        f'<span class="rec-card-node" style="color: #8A8A8A;">{sku}</span>'
        f'<span class="rec-card-arrow">::</span>'
        f'<span class="rec-card-node">{current_factory}</span>'
        f'<span class="rec-card-arrow">➔</span>'
        f'<span class="rec-card-node" style="color: #FF6B00;">{recommended_factory}</span>'
        f'</div>'
        f'<span class="rec-card-priority {priority_class}">{priority} Priority</span>'
        f'</div>'
        f'<div class="rec-card-grid">'
        f'<div class="rec-card-stat">'
        f'<span class="rec-card-stat-label">Fulfillment Speed</span>'
        f'<span class="rec-card-stat-val" style="color: #10b981;">-{time_reduction_pct:.1f}% Lead Time</span>'
        f'</div>'
        f'<div class="rec-card-stat">'
        f'<span class="rec-card-stat-label">Freight Impact</span>'
        f'<span class="rec-card-stat-val" style="color: #10b981;">+${freight_savings:,.2f}</span>'
        f'</div>'
        f'<div class="rec-card-stat">'
        f'<span class="rec-card-stat-label">Confidence</span>'
        f'<span class="rec-card-stat-val" style="color: #38bdf8;">{confidence_score:.1f}%</span>'
        f'</div>'
        f'<div class="rec-card-stat">'
        f'<span class="rec-card-stat-label">Net Profit Impact</span>'
        f'<span class="rec-card-stat-val">${profit_impact:,.2f}</span>'
        f'</div>'
        f'</div>'
        f'<div class="rec-card-reason">'
        f'<b>Rationale:</b> {reason}'
        f'</div>'
        f'</div>'
    )
    st.html(html)
