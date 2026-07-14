"""What-If Simulation Engine for Nassau Candy.

This module provides the NassauSimulator class, which evaluates specific manual
operational changes (Factory, Customer Region, and Ship Mode) for any transaction or product
and predicts shipping lead times, gross profits, transition risks, and model confidence scores.
"""

import os
import sys
import logging
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.predict import NassauPredictor

logger = logging.getLogger(__name__)


class NassauSimulator:
    """Simulates manual operational reallocations and returns multi-dimensional metrics."""

    FACTORIES = {
        "Lot's O' Nuts": (32.881893, -111.768036),
        "Wicked Choccy's": (32.076176, -81.088371),
        "Sugar Shack": (48.11914, -96.18115),
        "Secret Factory": (41.446333, -90.565487),
        "The Other Factory": (35.1175, -89.971107),
    }

    FACTORY_SPECIALTIES = {
        "Lot's O' Nuts": "Chocolate",
        "Wicked Choccy's": "Chocolate",
        "Sugar Shack": "Sugar",
        "Secret Factory": "Other",
        "The Other Factory": "Other",
    }

    # Region centroids for customer distance calculations
    REGION_CENTROIDS = {
        "Pacific": (37.7749, -122.4194),
        "Atlantic": (40.7128, -74.0060),
        "Interior": (41.8781, -87.6298),
        "Gulf": (29.7604, -95.3698),
    }

    # Outbound freight cost rates ($ per mile per unit)
    SHIPPING_RATES = {
        "Same Day": 0.20,
        "First Class": 0.15,
        "Second Class": 0.10,
        "Standard Class": 0.05,
    }

    def __init__(self, model_dir: str = "models") -> None:
        """Initializes the simulation engine.

        Args:
            model_dir (str): Registry path containing models.
        """
        self.predictor = NassauPredictor(model_dir=model_dir)

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
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        )
        c = 2 * np.arcsin(np.sqrt(a))
        return float(c * 3956)

    def _calculate_prediction_confidence(self, X_transformed: pd.DataFrame) -> float:
        """Computes prediction confidence based on Random Forest tree variance.

        If the model is an ensemble of trees (Random Forest), we measure the
        variance of predictions across all individual trees. High variance
        indicates low confidence.

        Args:
            X_transformed (pd.DataFrame): Transformed feature row.

        Returns:
            float: Confidence score between 0.0 and 100.0.
        """
        model_obj = self.predictor.model
        
        # If the serialized model is a Random Forest Regressor
        if hasattr(model_obj, "estimators_"):
            # Gather predictions from every individual tree
            predictions = np.array([tree.predict(X_transformed) for tree in model_obj.estimators_])
            # Calculate variance of predictions
            prediction_variance = float(np.var(predictions, axis=0)[0])
            
            # Convert variance to a exponential confidence score between 0 and 100
            # Higher variance -> lower confidence. Scale factor lambda = 0.05
            confidence = 100.0 * np.exp(-0.05 * prediction_variance)
            return float(np.clip(confidence, a_min=10.0, a_max=99.9))
        
        # Fallback for standard regressors (e.g. Linear Regression)
        return 75.0

    def simulate_scenario(
        self,
        product_name: str,
        division: str,
        target_factory: str,
        target_region: str,
        target_ship_mode: str,
        base_sales: float = 15.0,
        base_units: int = 4,
    ) -> Dict[str, Any]:
        """Simulates a custom 'what-if' logistics configuration.

        Args:
            product_name (str): Product SKU name.
            division (str): Product division (Chocolate, Sugar, Other).
            target_factory (str): Hypothetical manufacturing facility.
            target_region (str): Customer region (Pacific, Atlantic, Interior, Gulf).
            target_ship_mode (str): Shipping speed tier.
            base_sales (float): Total sales revenue of order.
            base_units (int): Number of units ordered.

        Returns:
            Dict[str, Any]: Simulation metrics (lead time, profit, risk, confidence).
        """
        logger.info(
            "Simulating: Product=%s | Factory=%s | Region=%s | ShipMode=%s",
            product_name,
            target_factory,
            target_region,
            target_ship_mode,
        )

        # 1. Coordinate distance recalculation
        f_lat, f_lon = self.FACTORIES[target_factory]
        r_lat, r_lon = self.REGION_CENTROIDS.get(target_region, (39.8283, -98.5795))
        distance = self._haversine_distance(f_lat, f_lon, r_lat, r_lon)

        # 2. Estimate outbound shipping costs and profit
        # Cost-to-serve is modeled as (distance * units * rate)
        rate = self.SHIPPING_RATES.get(target_ship_mode, 0.05)
        shipping_cost = distance * base_units * rate
        # Gross profit = Sales - manufacturing cost (base) - shipping cost
        # Let's assume manufacturing cost is roughly 40% of sales
        manufacturing_cost = base_sales * 0.40
        simulated_profit = base_sales - manufacturing_cost - shipping_cost

        # 3. Formulate transaction dataframe for model feature extraction
        sim_row = {
            "Product Name": product_name,
            "Division": division,
            "Region": target_region,
            "Ship Mode": target_ship_mode,
            "Product ID": "PROD-MOCK",  # Placeholder ID matching standard schema
            "Sales": base_sales,
            "Units": base_units,
            "Cost": manufacturing_cost,
            "Gross Profit": base_sales - manufacturing_cost,  # Base profit before shipping deduction
            "Order Date": pd.Timestamp.now(),  # Set to current date
            "distance_miles": distance,
        }
        df_sim = pd.DataFrame([sim_row])

        # 4. Predict Lead Time & compute Confidence Score
        X_trans = self.predictor.extractor.transform(df_sim)
        pred_lead_time = float(self.predictor.model.predict(X_trans)[0])
        pred_lead_time = max(1.0, pred_lead_time)  # Clip at lower bound

        confidence_score = self._calculate_prediction_confidence(X_trans)

        # 5. Determine capability mismatch risk
        specialty = self.FACTORY_SPECIALTIES[target_factory]
        risk_level = "Low" if specialty == division else "High"

        return {
            "simulated_lead_time_days": round(pred_lead_time, 2),
            "simulated_shipping_cost": round(shipping_cost, 2),
            "simulated_profit": round(simulated_profit, 2),
            "distance_miles": round(distance, 2),
            "transition_risk": risk_level,
            "confidence_score": round(confidence_score, 1),
        }


if __name__ == "__main__":
    simulator = NassauSimulator(model_dir="models")
    try:
        res = simulator.simulate_scenario(
            product_name="Wonka Bar - Milk Chocolate",
            division="Chocolate",
            target_factory="Sugar Shack",
            target_region="Pacific",
            target_ship_mode="First Class"
        )
        print("\n=== WHAT-IF SIMULATION RESULTS ===")
        for k, v in res.items():
            print(f"{k:<30}: {v}")
        print("==================================\n")
    except Exception:
        logger.exception("Error compiling simulation engine script")
