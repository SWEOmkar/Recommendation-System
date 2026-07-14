"""Risk Dashboard page layout."""

import logging
import streamlit as st
import pandas as pd
from dashboard.utils.helpers import get_cached_recommendations, get_recommender
from dashboard.components.custom_elements import render_page_header, render_section_header, render_risk_alert
from dashboard.utils.error_handler import RECOMMENDATION_ERROR

logger = logging.getLogger(__name__)


def render_risk_page(df_clean) -> None:
    """Renders facility mismatch alerts and capacity constraints tables."""
    
    render_page_header(
        title="Risk & Constraints Matrix",
        subtitle="Evaluate operational risks, retrofitting requirements, and production capacity constraints."
    )

    try:
        recommender = get_recommender(weights=(0.4, 0.4, 0.2))
        with st.spinner("Analyzing operational risk parameters..."):
            recs = get_cached_recommendations(weights=(0.4, 0.4, 0.2))
    except Exception:
        logger.exception("Failed to generate risk analysis")
        st.error(RECOMMENDATION_ERROR)
        return

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        mismatches = []
        for sku, options in recs.items():
            best_opt = options[0]
            if best_opt["transition_risk_level"] == "High":
                mismatches.append({
                    "Product SKU": sku,
                    "Target Factory": best_opt["target_factory"],
                    "Factory Specialty": recommender.FACTORY_SPECIALTIES[best_opt["target_factory"]]
                })

        mismatch_table_html = ""
        if mismatches:
            mismatch_table_html += """
            <table class="saas-table">
                <thead>
                    <tr>
                        <th>Product SKU</th>
                        <th>Target Factory</th>
                        <th>Factory Specialty</th>
                    </tr>
                </thead>
                <tbody>
            """
            for item in mismatches:
                mismatch_table_html += f"""
                    <tr>
                        <td>{item['Product SKU']}</td>
                        <td>{item['Target Factory']}</td>
                        <td>{item['Factory Specialty']}</td>
                    </tr>
                """
            mismatch_table_html += "</tbody></table>"
        else:
            mismatch_table_html = '<div style="color: #10b981; font-weight: 600; font-size: 0.85rem; padding: 0.5rem 0;">No capability mismatches detected in primary allocations.</div>'

        container_r1_html = f"""
        <div class="chart-container" style="height: 380px; overflow-y: auto;">
            <div class="chart-title" style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; margin-bottom: 0.75rem;">
                ⚠️ Facility Mismatch Alerts
            </div>
            {mismatch_table_html}
        </div>
        """
        st.html(container_r1_html)

        if mismatches:
            render_risk_alert(
                title="Line Retrofitting Required",
                text="The primary reallocation targets above involve High CapEx retrofitting because the destination factory does not specialize in the product's confections class.",
                level="error",
                icon="🚨"
            )

    with col_r2:
        # Group and sum allocated units
        factory_vol = {}
        for sku, options in recs.items():
            best_fac = options[0]["target_factory"]
            prod_units = df_clean[df_clean["Product Name"] == sku]["Units"].sum() if not df_clean.empty else 0
            factory_vol[best_fac] = factory_vol.get(best_fac, 0) + prod_units
            
        capacities = {
            "Lot's O' Nuts": 15000,
            "Wicked Choccy's": 12000,
            "Sugar Shack": 8000,
            "Secret Factory": 6000,
            "The Other Factory": 5000
        }
        
        cap_rows = []
        for fac, units in factory_vol.items():
            cap = capacities.get(fac, 10000)
            util = (units / cap) * 100
            cap_rows.append({
                "Factory": fac,
                "Allocated Volume": units,
                "Max Capacity": cap,
                "Utilization (%)": round(util, 1),
                "Status": "⚠️ OVERLOAD" if util > 100 else "✅ SAFE"
            })

        capacity_table_html = ""
        if cap_rows:
            capacity_table_html += """
            <table class="saas-table">
                <thead>
                    <tr>
                        <th>Factory</th>
                        <th>Allocated Volume</th>
                        <th>Max Capacity</th>
                        <th>Utilization</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
            """
            for item in cap_rows:
                status_class = "badge-safe" if item['Status'] == "✅ SAFE" else "badge-overload"
                status_text = "SAFE" if item['Status'] == "✅ SAFE" else "OVERLOAD"
                capacity_table_html += f"""
                    <tr>
                        <td>{item['Factory']}</td>
                        <td>{item['Allocated Volume']:,}</td>
                        <td>{item['Max Capacity']:,}</td>
                        <td>{item['Utilization (%)']:.1f}%</td>
                        <td><span class="{status_class}">{status_text}</span></td>
                    </tr>
                """
            capacity_table_html += "</tbody></table>"
        else:
            capacity_table_html = '<div style="color: #8A8A8A; font-size: 0.85rem; padding: 0.5rem 0;">No allocated volume data available.</div>'

        container_r2_html = f"""
        <div class="chart-container" style="height: 380px; overflow-y: auto;">
            <div class="chart-title" style="border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.5rem; margin-bottom: 0.75rem;">
                🏭 Factory Capacity Utilization
            </div>
            {capacity_table_html}
        </div>
        """
        st.html(container_r2_html)

        if cap_rows:
            overloads = [x["Factory"] for x in cap_rows if x["Utilization (%)"] > 100]
            if overloads:
                render_risk_alert(
                    title="Capacity Breached",
                    text=f"The following factories are currently overloaded under the recommended scenario: {', '.join(overloads)}. Consider adjusting scenario weights.",
                    level="warning",
                    icon="⚠️"
                )
