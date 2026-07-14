"""Factory Simulator page layout."""

import logging
import streamlit as st
import pandas as pd
import numpy as np
from dashboard.utils.helpers import get_simulator
from dashboard.components.custom_elements import render_page_header, render_section_header, render_risk_alert
from dashboard.utils.error_handler import SIMULATION_ERROR, MODEL_LOAD_ERROR

logger = logging.getLogger(__name__)


def render_simulator_page(df_clean) -> None:
    """Renders the what-if route simulator page with an executive decision card workflow."""
    
    render_page_header(
        title="What-If Route Simulator",
        subtitle="Evaluate manual facility reallocations, shipping modes, and region assignments using ML inference."
    )

    # 1. Product Selection
    unique_products = sorted(df_clean["Product Name"].unique()) if not df_clean.empty else []
    if not unique_products:
        st.warning("No products match active sidebar filters.")
        st.stop()
        
    st.markdown("""
    <style>
        .stSelectbox { margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

    # Static Catalog baseline to lookup current factory
    product_catalog = {
        "Wonka Bar - Nutty Crunch Surprise": ("Chocolate", "Lot's O' Nuts"),
        "Wonka Bar - Fudge Mallows": ("Chocolate", "Lot's O' Nuts"),
        "Wonka Bar -Scrumdiddlyumptious": ("Chocolate", "Lot's O' Nuts"),
        "Wonka Bar - Milk Chocolate": ("Chocolate", "Wicked Choccy's"),
        "Wonka Bar - Triple Dazzle Caramel": ("Chocolate", "Wicked Choccy's"),
        "Laffy Taffy": ("Sugar", "Sugar Shack"),
        "SweeTARTS": ("Sugar", "Sugar Shack"),
        "Nerds": ("Sugar", "Sugar Shack"),
        "Fun Dip": ("Sugar", "Sugar Shack"),
        "Fizzy Lifting Drinks": ("Other", "Sugar Shack"),
        "Everlasting Gobstopper": ("Sugar", "Secret Factory"),
        "Hair Toffee": ("Sugar", "The Other Factory"),
        "Lickable Wallpaper": ("Other", "Secret Factory"),
        "Wonka Gum": ("Other", "Secret Factory"),
        "Kazookles": ("Other", "The Other Factory"),
    }

    # Clean dropdown select UI
    selected_product = st.selectbox("Product SKU to Simulate", unique_products, index=0)
    
    df_prod = df_clean[df_clean["Product Name"] == selected_product]
    prod_division, current_factory = product_catalog.get(
        selected_product, 
        (df_prod["Division"].iloc[0] if not df_prod.empty else "Chocolate", "Lot's O' Nuts")
    )

    # Display baseline summary info
    avg_sales = float(df_prod["Sales"].mean()) if not df_prod.empty else 15.0
    avg_units = int(df_prod["Units"].mean()) if not df_prod.empty else 3
    baseline_lead = float(df_prod["lead_time_days"].mean()) if not df_prod.empty else 5.2

    # 2. Simulator Parameters Form
    st.markdown("### Simulated Route Configuration")
    try:
        simulator = get_simulator()
    except Exception:
        logger.exception("Failed to initialize simulator")
        st.error(MODEL_LOAD_ERROR)
        return
    
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    with col_sel1:
        target_factory = st.selectbox("Destination Factory Override", list(simulator.FACTORIES.keys()))
    with col_sel2:
        target_region = st.selectbox("Target Customer Region", list(simulator.REGION_CENTROIDS.keys()))
    with col_sel3:
        target_ship_mode = st.selectbox("Shipping Speed Tier", list(simulator.SHIPPING_RATES.keys()))

    # Run Button
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("Run Simulation Scenario", use_container_width=True):
        try:
            with st.spinner("Calculating simulated route metrics..."):
                sim_res = simulator.simulate_scenario(
                    product_name=selected_product,
                    division=prod_division,
                    target_factory=target_factory,
                    target_region=target_region,
                    target_ship_mode=target_ship_mode,
                    base_sales=avg_sales,
                    base_units=avg_units
                )
            
            # Baseline calculation for profit delta comparison
            base_lat, base_lon = simulator.FACTORIES.get(current_factory, (32.88, -111.76))
            reg_lat, reg_lon = simulator.REGION_CENTROIDS.get(target_region, (37.77, -122.41))
            
            baseline_dist = simulator._haversine_distance(base_lat, base_lon, reg_lat, reg_lon)
            rate = simulator.SHIPPING_RATES.get(target_ship_mode, 0.05)
            baseline_shipping = baseline_dist * avg_units * rate
            
            simulated_shipping = sim_res["simulated_shipping_cost"]
            freight_delta = baseline_shipping - simulated_shipping  # Positive means savings!
            
            # Simulated lead time
            sim_lead = sim_res["simulated_lead_time_days"]
            lead_diff = baseline_lead - sim_lead
            
            # 3. Present Executive Decision Card
            render_section_header("Simulation Output Analysis", "The simulated routing variables compared to current static facility allocations.")
            
            profit_color = "#10b981" if freight_delta >= 0 else "#ef4444"
            risk_color = "#10b981" if sim_res["transition_risk"] == "Low" else "#ef4444"
            
            # Formulate recommendation reasoning
            is_mismatch = simulator.FACTORY_SPECIALTIES.get(target_factory) != prod_division
            if is_mismatch:
                rec_insight = f"⚠️ Capability Mismatch: Reallocating this {prod_division} SKU to {target_factory} (which specializes in {simulator.FACTORY_SPECIALTIES.get(target_factory)}) requires line retrofitting and creates High CapEx risk."
            elif lead_diff > 0 and freight_delta > 0:
                rec_insight = f"✅ Highly Recommended: Reallocating from {current_factory} to {target_factory} speeds up transit by {lead_diff:.1f} days and saves approximately ${freight_delta:.2f} in outbound freight per order."
            elif lead_diff > 0:
                rec_insight = f"⚡ Speed Advantage: Faster fulfillment by {lead_diff:.1f} days, but with a freight cost increase of ${abs(freight_delta):.2f} per order."
            elif freight_delta > 0:
                rec_insight = f"💰 Cost Advantage: Saves ${freight_delta:.2f} in freight per order, but increases transit delay by {abs(lead_diff):.1f} days."
            else:
                rec_insight = f"❌ Not Recommended: Increases both fulfillment lead time by {abs(lead_diff):.1f} days and freight by ${abs(freight_delta):.2f} per order."

            # Flat HTML string to prevent markdown parser from mistaking layout indentation for a code block
            sim_card_html = (
                f'<div class="rec-card" style="border-left: 5px solid #FF6B00; background-color: #20232A;">'
                f'<div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #8A8A8A; letter-spacing: 0.05em; margin-bottom: 0.5rem;">'
                f'Executive Decision Card - Simulation Results'
                f'</div>'
                f'<div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">'
                f'<span>{selected_product}</span>'
                f'<span style="color: #8A8A8A; font-weight: 400;">current:</span>'
                f'<span style="color: #8A8A8A; font-weight: 600;">{current_factory}</span>'
                f'<span style="color: #FF6B00;">➔</span>'
                f'<span style="color: #FFFFFF; font-weight: 600;">simulated:</span>'
                f'<span style="color: #FF6B00; font-weight: 700;">{target_factory}</span>'
                f'</div>'
                f'<div class="rec-card-grid">'
                f'<div class="rec-card-stat">'
                f'<span class="rec-card-stat-label">Predicted Lead Time</span>'
                f'<span class="rec-card-stat-val" style="color: #E5A93C;">{sim_lead:.1f} Days</span>'
                f'</div>'
                f'<div class="rec-card-stat">'
                f'<span class="rec-card-stat-label">Freight Impact</span>'
                f'<span class="rec-card-stat-val" style="color: {profit_color};">{freight_delta:+.2f} per order</span>'
                f'</div>'
                f'<div class="rec-card-stat">'
                f'<span class="rec-card-stat-label">Transition Risk</span>'
                f'<span class="rec-card-stat-val" style="color: {risk_color};">{sim_res["transition_risk"]}</span>'
                f'</div>'
                f'<div class="rec-card-stat">'
                f'<span class="rec-card-stat-label">Model Confidence</span>'
                f'<span class="rec-card-stat-val" style="color: #38bdf8;">{sim_res["confidence_score"]:.1f}%</span>'
                f'</div>'
                f'</div>'
                f'<div class="rec-card-reason" style="margin-top: 1rem;">'
                f'{rec_insight}'
                f'</div>'
                f'</div>'
            )
            st.html(sim_card_html)
            
            # Capability warnings banner
            if is_mismatch:
                render_risk_alert(
                    title="Facility Capability Breached",
                    text=f"The selected factory {target_factory} does not possess the specialty tooling required for {prod_division} confections. Proceeding requires manual operational oversight.",
                    level="error"
                )
                
            st.info(f"Geographic transit distance to target {target_region} customer centroid: {sim_res['distance_miles']:,} miles.")

        except Exception:
            logger.exception("Simulation failed for product=%s factory=%s", selected_product, target_factory)
            st.error(SIMULATION_ERROR)
