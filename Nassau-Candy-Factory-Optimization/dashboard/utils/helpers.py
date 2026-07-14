"""Helper utilities for the Nassau Candy Streamlit Dashboard, optimized with caching."""

import os
import sys
import logging
import pandas as pd
import streamlit as st

from dashboard.utils.error_handler import (
    DATA_LOAD_ERROR,
    MODEL_LOAD_ERROR,
    RECOMMENDATION_ERROR,
    log_and_reraise,
)

logger = logging.getLogger(__name__)

# Resolve absolute path to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, os.path.join(project_root, "src"))

from optimization.recommender import NassauRecommender
from optimization.simulator import NassauSimulator


@st.cache_data
def load_clean_dataset() -> pd.DataFrame:
    """Loads the preprocessed clean dataset.

    Returns:
        pd.DataFrame: Cleaned data frame.

    Raises:
        RuntimeError: With a generic message if loading fails.
    """
    try:
        csv_path = os.path.join(project_root, "data", "processed", "clean_data.csv")
        if not os.path.exists(csv_path):
            from data.preprocessor import NassauPreprocessor
            raw_path = os.path.join(project_root, "data", "raw", "Nassau Candy Distributor.csv")
            preprocessor = NassauPreprocessor(date_shift_days=1270)
            df = preprocessor.run_pipeline(raw_path, csv_path)
        else:
            df = pd.read_csv(csv_path)

        df["Order Date"] = pd.to_datetime(df["Order Date"])
        return df
    except Exception as e:
        log_and_reraise(e, "Failed to load clean dataset", DATA_LOAD_ERROR)


@st.cache_resource
def get_recommender(weights) -> NassauRecommender:
    """Instantiates the multi-objective utility Recommender resource.

    Raises:
        RuntimeError: With a generic message if model loading fails.
    """
    try:
        models_path = os.path.join(project_root, "models")
        return NassauRecommender(model_dir=models_path, default_weights=weights)
    except Exception as e:
        log_and_reraise(e, "Failed to instantiate NassauRecommender", MODEL_LOAD_ERROR)


@st.cache_resource
def get_simulator() -> NassauSimulator:
    """Instantiates the What-If Route Simulator resource.

    Raises:
        RuntimeError: With a generic message if model loading fails.
    """
    try:
        models_path = os.path.join(project_root, "models")
        return NassauSimulator(model_dir=models_path)
    except Exception as e:
        log_and_reraise(e, "Failed to instantiate NassauSimulator", MODEL_LOAD_ERROR)


@st.cache_data
def get_cached_recommendations(weights) -> dict:
    """Runs recommendation engine simulations and caches the result by weights.

    Drastically speeds up page loading and slider adjustments.

    Raises:
        RuntimeError: With a generic message if recommendation generation fails.
    """
    try:
        recommender = get_recommender(weights)
        csv_path = os.path.join(project_root, "data", "processed", "clean_data.csv")
        return recommender.generate_recommendations(csv_path)
    except Exception as e:
        log_and_reraise(e, "Failed to generate cached recommendations", RECOMMENDATION_ERROR)
