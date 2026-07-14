"""Recommendation engine module for Nassau Candy factory-product reallocation.

This module evaluates alternate factory assignments for each product SKU,
predicts lead times using the trained ML model, calculates profit and
operational differences, computes a multi-objective utility score, and
ranks the best allocations.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.predict import NassauPredictor

logger = logging.getLogger(__name__)


class NassauRecommender:
    """Evaluates and ranks factory reassignments using multi-objective optimization."""

    # Factory coordinates mapping
    FACTORIES = {
        "Lot's O' Nuts": (32.881893, -111.768036),
        "Wicked Choccy's": (32.076176, -81.088371),
        "Sugar Shack": (48.11914, -96.18115),
        "Secret Factory": (41.446333, -90.565487),
        "The Other Factory": (35.1175, -89.971107),
    }

    # Factory specialties to determine transition risk
    FACTORY_SPECIALTIES = {
        "Lot's O' Nuts": "Chocolate",
        "Wicked Choccy's": "Chocolate",
        "Sugar Shack": "Sugar",
        "Secret Factory": "Other",
        "The Other Factory": "Other",
    }

    # Shipping rates ($ per mile per unit)
    SHIPPING_RATES = {
        "Same Day": 0.20,
        "First Class": 0.15,
        "Second Class": 0.10,
        "Standard Class": 0.05,
    }

    def __init__(
        self,
        model_dir: str = "models",
        default_weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
    ) -> None:
        """Initializes the recommender engine.

        Args:
            model_dir (str): Registry path containing models.
            default_weights (Tuple[float, float, float]): (w_speed, w_profit, w_risk)
        """
        self.predictor = NassauPredictor(model_dir=model_dir)
        self.w_speed, self.w_profit, self.w_risk = default_weights
        
        # Approximate coordinate centroids of regions for distance calculations
        # (Since customer exact lat/long isn't in dataset, we map Region names to centroids)
        self.region_centroids = {
            "Pacific": (37.7749, -122.4194),  # San Francisco cent.
            "Atlantic": (40.7128, -74.0060),  # New York cent.
            "Interior": (41.8781, -87.6298),  # Chicago cent.
            "Gulf": (29.7604, -95.3698),      # Houston cent.
        }

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculates distance in miles between coordinate points.

        Args:
            lat1, lon1: Coordinates of point 1.
            lat2, lon2: Coordinates of point 2.

        Returns:
            float: Distance in miles.
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        )
        c = 2 * np.arcsin(np.sqrt(a))
        r = 3956  # Radius of earth in miles
        return float(c * r)

    def _estimate_shipping_cost(
        self, distance: float, units: int, ship_mode: str
    ) -> float:
        """Estimates outbound shipping freight costs.

        Args:
            distance (float): Shipping distance in miles.
            units (int): Number of items ordered.
            ship_mode (str): Shipping speed tier.

        Returns:
            float: Sizing of shipping cost in dollars.
        """
        rate = self.SHIPPING_RATES.get(ship_mode, 0.05)
        return distance * units * rate

    def evaluate_reassignment(
        self,
        df_product: pd.DataFrame,
        current_factory: str,
        target_factory: str,
        division: str,
    ) -> Dict[str, Any]:
        """Simulates product reallocation to a target factory and measures performance.

        Args:
            df_product (pd.DataFrame): Transactions for a specific product.
            current_factory (str): The currently assigned manufacturing facility.
            target_factory (str): The hypothetical destination facility.
            division (str): Product division (Chocolate, Sugar, Other).

        Returns:
            Dict[str, Any]: Metrics dictionary detailing improvements and risks.
        """
        df_sim = df_product.copy()

        # Target Coordinates
        t_lat, t_lon = self.FACTORIES[target_factory]

        # Calculate distances to customer regions for all rows
        distances = []
        for _, row in df_sim.iterrows():
            region = row["Region"]
            r_lat, r_lon = self.region_centroids.get(region, (39.8283, -98.5795))  # US geographic center fallback
            dist = self._haversine_distance(t_lat, t_lon, r_lat, r_lon)
            distances.append(dist)
        
        df_sim["distance_miles"] = distances

        # Predict new lead times using the model
        # We need to construct input features for prediction
        # To avoid data leak or missing cols, we add required fields
        # Note: the predictor expects raw cols, we pass df_sim
        predicted_lead_times = self.predictor.predict_dataframe(df_sim)
        mean_pred_lead_time = float(np.mean(predicted_lead_times))

        # Calculate current average lead time
        current_mean_lead_time = float(df_product["lead_time_days"].mean())
        lead_time_delta = current_mean_lead_time - mean_pred_lead_time
        lead_time_pct_reduction = (lead_time_delta / current_mean_lead_time) * 100

        # Calculate profit margin impact based on distance and units
        # Compute shipping costs
        current_distances = []
        c_lat, c_lon = self.FACTORIES[current_factory]
        for _, row in df_sim.iterrows():
            region = row["Region"]
            r_lat, r_lon = self.region_centroids.get(region, (39.8283, -98.5795))
            current_distances.append(self._haversine_distance(c_lat, c_lon, r_lat, r_lon))
            
        current_shipping = sum(
            self._estimate_shipping_cost(d, u, s)
            for d, u, s in zip(current_distances, df_product["Units"], df_product["Ship Mode"])
        )
        simulated_shipping = sum(
            self._estimate_shipping_cost(d, u, s)
            for d, u, s in zip(distances, df_product["Units"], df_product["Ship Mode"])
        )

        shipping_savings = current_shipping - simulated_shipping
        # Profit impact represents increase in gross profit from freight savings
        profit_delta = shipping_savings

        # Calculate Transition Risk Penalty
        # Transition risk is high if moving division out of factory specialty
        specialty = self.FACTORY_SPECIALTIES[target_factory]
        if specialty == division:
            transition_risk = 0.0  # High capability match
        else:
            transition_risk = 1.0  # Requires retrofitting line (high risk)

        # Normalize metrics for scoring
        # Lead time reduction: scaled between 0 and 1 (cap at 100% reduction)
        score_speed = max(0.0, min(1.0, lead_time_pct_reduction / 100.0))
        # Profit delta: scaled relative to total order sales (A margin saving of 5% of sales is excellent)
        total_sales = df_product["Sales"].sum()
        score_profit = max(0.0, min(1.0, profit_delta / (total_sales + 0.1)))
        
        # Calculate utility score
        utility_score = (
            (self.w_speed * score_speed)
            + (self.w_profit * score_profit)
            - (self.w_risk * transition_risk)
        )

        return {
            "target_factory": target_factory,
            "predicted_lead_time_days": mean_pred_lead_time,
            "lead_time_reduction_days": lead_time_delta,
            "lead_time_pct_reduction": lead_time_pct_reduction,
            "profit_impact_savings": profit_delta,
            "transition_risk_level": "High" if transition_risk > 0 else "Low",
            "utility_score": utility_score,
        }

    def generate_recommendations(self, data_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Runs reallocation scenario simulations and ranks factories for all products.

        Args:
            data_path (str): Path to clean dataset CSV.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Top-3 ranked recommendations grouped by SKU.
        """
        df = pd.read_csv(data_path)
        
        # Extract mapping of product to division and factory from document context
        # (This acts as Nassau's static catalog baseline)
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

        all_recommendations = {}

        for product_name, (division, current_factory) in product_catalog.items():
            df_prod = df[df["Product Name"] == product_name]
            if len(df_prod) == 0:
                logger.warning("No sales transactions found in dataset for SKU: %s", product_name)
                continue

            logger.info("Evaluating reallocations for SKU: %s (%d records)...", product_name, len(df_prod))
            product_recs = []

            # Evaluate against all alternative factories
            for target_factory in self.FACTORIES.keys():
                if target_factory == current_factory:
                    continue  # Skip evaluating current allocation
                
                try:
                    eval_metrics = self.evaluate_reassignment(
                        df_product=df_prod,
                        current_factory=current_factory,
                        target_factory=target_factory,
                        division=division,
                    )
                    product_recs.append(eval_metrics)
                except Exception as e:
                    logger.error(
                        "Failed to evaluate reassignment for %s to %s: %s",
                        product_name,
                        target_factory,
                        str(e),
                    )

            # Sort by utility score descending
            product_recs.sort(key=lambda x: x["utility_score"], reverse=True)
            # Take Top-3
            all_recommendations[product_name] = product_recs[:3]

        return all_recommendations


if __name__ == "__main__":
    processed_csv = "data/processed/clean_data.csv"
    recommender = NassauRecommender(model_dir="models")
    try:
        recs = recommender.generate_recommendations(data_path=processed_csv)
        print("\n=== TOP-3 REALLOCATION RECOMMENDATIONS (SAMPLE) ===")
        sample_sku = "Wonka Bar - Milk Chocolate"
        if sample_sku in recs:
            print(f"\nSKU: {sample_sku}")
            for rank, rec in enumerate(recs[sample_sku]):
                print(
                    f"  Rank {rank+1}: Facility: {rec['target_factory']:<20} | Score: {rec['utility_score']:.4f} | Lead Time Days: {rec['predicted_lead_time_days']:.2f} | Savings: ${rec['profit_impact_savings']:.2f} | Risk: {rec['transition_risk_level']}"
                )
        print("==================================================\n")
    except Exception:
        logger.exception("Error compiling recommender engine script")
