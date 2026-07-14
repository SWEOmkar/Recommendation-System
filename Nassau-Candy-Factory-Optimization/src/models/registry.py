"""Model registry module for saving and loading serialized models and pipelines.

This module handles serialization of model objects, feature extractors, and
associated pipeline metadata using joblib.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
import joblib

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages serialization, versioning, and loading of machine learning artifacts."""

    def __init__(self, registry_dir: str = "models") -> None:
        """Initializes the model registry.

        Args:
            registry_dir (str): Path to serialize the model artifacts.
        """
        self.registry_dir = registry_dir
        os.makedirs(registry_dir, exist_ok=True)
        logger.info("Model registry initialized at: %s", registry_dir)

    def save_model(
        self,
        model: Any,
        feature_extractor: Any,
        metrics: Dict[str, float],
        model_name: str = "best_model",
    ) -> Tuple[str, str]:
        """Serializes the model, feature extractor, and metadata to disk.

        Args:
            model (Any): Trained estimator object.
            feature_extractor (Any): Fitted feature extractor transformer.
            metrics (Dict[str, float]): Validation performance metrics.
            model_name (str): Prefix name for the serialized files.

        Returns:
            Tuple[str, str]: Paths to the saved model and metadata files.
        """
        model_path = os.path.join(self.registry_dir, f"{model_name}.joblib")
        meta_path = os.path.join(self.registry_dir, f"{model_name}_metadata.json")

        logger.info("Serializing model artifacts to %s...", model_path)
        
        # Save model and feature extractor together in a tuple or dict
        artifacts = {
            "model": model,
            "feature_extractor": feature_extractor
        }
        joblib.dump(artifacts, model_path)

        # Save performance metadata
        metadata = {
            "model_type": type(model).__name__,
            "metrics": metrics,
            "serialized_at": str(datetime.now())
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        logger.info("Model artifacts and metadata saved successfully.")
        return model_path, meta_path

    def load_model(self, model_name: str = "best_model") -> Tuple[Any, Any]:
        """Loads serialized model and feature extractor from disk.

        Args:
            model_name (str): Name of the serialized model to load.

        Returns:
            Tuple[Any, Any]: Deserialized model estimator and feature extractor.

        Raises:
            FileNotFoundError: If the model artifacts are not found.
        """
        model_path = os.path.join(self.registry_dir, f"{model_name}.joblib")
        if not os.path.exists(model_path):
            logger.error("Serialized model file not found at: %s", model_path)
            raise FileNotFoundError("Required model artifacts were not found.")

        logger.info("Loading model artifacts from %s...", model_path)
        artifacts = joblib.load(model_path)
        return artifacts["model"], artifacts["feature_extractor"]
