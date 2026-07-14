"""Inference pipeline module for lead-time predictions.

This module exposes the NassauPredictor class, which loads the best model and
extractor from the registry to serve runtime single-point or batch predictions.
"""

import os
import sys
import logging
from typing import Dict, Any, Union, List
import pandas as pd
import numpy as np

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.registry import ModelRegistry

logger = logging.getLogger(__name__)


class NassauPredictor:
    """Loads model artifacts and runs lead time inference on arbitrary data schemas."""

    def __init__(self, model_dir: str = "models", model_name: str = "best_model") -> None:
        """Initializes the predictor.

        Args:
            model_dir (str): Registry path containing models.
            model_name (str): Name of the serialized model folder.
        """
        registry = ModelRegistry(registry_dir=model_dir)
        try:
            self.model, self.extractor = registry.load_model(model_name=model_name)
            logger.info("Predictor successfully loaded model '%s'", model_name)
        except Exception as e:
            logger.error("Failed to initialize predictor: %s", str(e))
            raise RuntimeError("Prediction model failed to initialize.") from None

    def predict_dataframe(self, df: pd.DataFrame) -> np.ndarray:
        """Runs batch lead-time prediction for a pre-formatted dataframe.

        Args:
            df (pd.DataFrame): Dataframe matching the raw dataset schema.

        Returns:
            np.ndarray: Predicted lead times in days.
        """
        df_input = df.copy()
        
        # Ensure Order Date is datetime format for the extractor
        if "Order Date" in df_input.columns:
            df_input["Order Date"] = pd.to_datetime(df_input["Order Date"])

        logger.debug("Extracting features for batch inference...")
        X_features = self.extractor.transform(df_input)
        
        logger.debug("Executing model inference...")
        predictions = self.model.predict(X_features)
        
        # Clip negative outputs (lead time must be at least 1 day)
        return np.clip(predictions, a_min=1.0, a_max=None)

    def predict_single(self, transaction: Dict[str, Any]) -> float:
        """Runs single-point lead-time prediction.

        Args:
            transaction (Dict[str, Any]): Dictionary containing transaction features
                (Order Date, Ship Mode, Division, Region, Product ID, Sales, Units, Cost, Gross Profit).

        Returns:
            float: Predicted lead time in days.
        """
        df_single = pd.DataFrame([transaction])
        pred_arr = self.predict_dataframe(df_single)
        return float(pred_arr[0])
