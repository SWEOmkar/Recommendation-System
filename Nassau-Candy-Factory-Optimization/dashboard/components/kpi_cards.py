"""KPI Cards component matching the premium enterprise design system."""

import streamlit as st
import numpy as np


def generate_sparkline_svg(values, color="#FF6B00", width=90, height=28) -> str:
    """Generates an inline SVG sparkline path from a list of values."""
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"><line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" stroke="{color}" stroke-dasharray="2,2" stroke-width="1.5"/></svg>'
    
    # Filter non-null values
    clean_vals = [float(x) for x in values if x is not None and not np.isnan(x)]
    if len(clean_vals) < 2:
        return f'<svg width="{width}" height="{height}"><line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" stroke="{color}" stroke-dasharray="2,2" stroke-width="1.5"/></svg>'
        
    min_v, max_v = min(clean_vals), max(clean_vals)
    range_v = max_v - min_v if max_v != min_v else 1.0
    
    points = []
    dx = width / (len(clean_vals) - 1)
    for i, v in enumerate(clean_vals):
        x = i * dx
        y = height - ((v - min_v) / range_v * (height - 6) + 3)
        points.append(f"{x:.1f},{y:.1f}")
        
    points_str = " ".join(points)
    return f'<svg width="{width}" height="{height}" style="overflow: visible;"><polyline fill="none" stroke="{color}" stroke-width="2" points="{points_str}" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def render_kpi_card(
    title: str,
    value: str,
    trend_pct: float = None,
    trend_up_is_good: bool = True,
    comparison_text: str = "",
    sparkline_values: list = None,
    icon: str = "📈",
    tooltip: str = "",
    col_obj = None
) -> None:
    """Renders a custom enterprise-style KPI Card inside a Streamlit column object.

    Each card contains title, value, status icon, tooltip, trend indicators,
    and inline SVG sparklines.
    """
    trend_class = "neutral"
    trend_indicator = ""
    
    if trend_pct is not None:
        if trend_pct > 0:
            trend_class = "up" if trend_up_is_good else "down"
            trend_indicator = f"↑ {trend_pct:+.1f}%"
        elif trend_pct < 0:
            trend_class = "down" if trend_up_is_good else "up"
            trend_indicator = f"↓ {trend_pct:+.1f}%"
        else:
            trend_class = "neutral"
            trend_indicator = "• 0.0%"

    # Custom trend line colors
    spark_color = "#FF6B00"
    if trend_class == "up":
        spark_color = "#10b981"
    elif trend_class == "down":
        spark_color = "#ef4444"
        
    sparkline_svg = generate_sparkline_svg(sparkline_values, color=spark_color)

    # Flat HTML string to prevent markdown parser from mistaking layout indentation for a code block
    card_html = (
        f'<div class="kpi-card" title="{tooltip}">'
        f'<div class="kpi-card-header">'
        f'<span class="kpi-card-icon">{icon}</span>'
        f'<span class="kpi-card-label">{title}</span>'
        f'</div>'
        f'<div class="kpi-card-body">'
        f'<span class="kpi-card-value">{value}</span>'
        f'<div class="kpi-card-sparkline">{sparkline_svg}</div>'
        f'</div>'
        f'<div class="kpi-card-footer">'
    )
    if trend_pct is not None:
        card_html += f'<span class="kpi-card-trend {trend_class}">{trend_indicator}</span>'
    if comparison_text:
        card_html += f'<span class="kpi-card-compare">{comparison_text}</span>'
    card_html += '</div></div>'
    
    if col_obj:
        col_obj.html(card_html)
    else:
        st.html(card_html)
