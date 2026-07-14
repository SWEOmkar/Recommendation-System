"""Model training pipeline for Nassau Candy Distributor lead-time prediction.

This module loads the cleaned dataset, splits it into train/test sets, engineers
features, trains and tunes three models (Linear Regression, Random Forest,
and Gradient Boosting), performs cross-validation, evaluates model metrics,
extracts feature importance, calculates residuals, and serializes the best model.
"""

import os
import sys
import logging
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, cross_val_score, RandomizedSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from features.feature_engineering import NassauFeatureExtractor
from models.registry import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes standard regression metrics.

    Args:
        y_true (np.ndarray): Real target values.
        y_pred (np.ndarray): Predicted target values.

    Returns:
        Dict[str, float]: Metrics dictionary.
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {"RMSE": float(rmse), "MAE": float(mae), "R2": float(r2)}


def run_training_pipeline(data_path: str, model_dir: str = "models") -> None:
    """Executes the complete machine learning training pipeline.

    Args:
        data_path (str): Path to the processed clean CSV data.
        model_dir (str): Folder to save serialized models.
    """
    logger.info("Starting Nassau ML Pipeline...")

    # 1. Ingest Data
    if not os.path.exists(data_path):
        logger.error("Clean dataset not found at: %s", data_path)
        raise FileNotFoundError("Required clean dataset was not found.")
        
    df = pd.read_csv(data_path)
    logger.info("Loaded cleaned dataset of shape: %s", df.shape)

    # 2. Extract target and split
    target_col = "lead_time_days"
    if target_col not in df.columns:
        raise KeyError("Required target column is missing from the dataset.")

    # Drop columns that are dates or targets to avoid leakage
    drop_cols = ["Row ID", "Order ID", "Order Date", "Ship Date", "adjusted_ship_date", "raw_lead_time_days", target_col]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    y = df[target_col]

    # Re-insert Order Date temporarily in X because feature extractor requires it for monthly/weekday calculations
    X["Order Date"] = pd.to_datetime(df["Order Date"])

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=df["Division"]
    )
    logger.info("Data splits established. Train: %s, Test: %s", X_train_raw.shape, X_test_raw.shape)

    # 3. Feature Engineering
    extractor = NassauFeatureExtractor()
    X_train = extractor.fit_transform(X_train_raw, y_train)
    X_test = extractor.transform(X_test_raw)
    
    logger.info("Feature engineering complete. Selected features: %s", list(X_train.columns))

    # Save feature names for output reference
    feature_names = list(X_train.columns)

    # 4. Cross Validation & Base Training
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42)
    }

    cv_results = {}
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    logger.info("Running 5-Fold Cross-Validation on base models...")
    for name, model in models.items():
        # Evaluate using RMSE score
        scores = cross_val_score(model, X_train, y_train, cv=kf, scoring="neg_root_mean_squared_error", n_jobs=-1)
        mean_rmse = -scores.mean()
        cv_results[name] = mean_rmse
        logger.info("%s: Average CV-RMSE = %.4f", name, mean_rmse)

    # 5. Hyperparameter Tuning (Randomized Search)
    logger.info("Initiating hyperparameter tuning for ensemble models...")
    
    # Tuning Gradient Boosting
    gb_grid = {
        "n_estimators": [50, 100, 150],
        "learning_rate": [0.01, 0.05, 0.1],
        "max_depth": [3, 4, 6],
        "subsample": [0.8, 0.9, 1.0]
    }
    
    gb_search = RandomizedSearchCV(
        estimator=GradientBoostingRegressor(random_state=42),
        param_distributions=gb_grid,
        n_iter=5,
        cv=3,
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1
    )
    logger.info("Tuning Gradient Boosting Regressor...")
    gb_search.fit(X_train, y_train)
    best_gb = gb_search.best_estimator_
    logger.info("Best GB Hyperparameters: %s", gb_search.best_params_)

    # Tuning Random Forest
    rf_grid = {
        "n_estimators": [50, 100, 150],
        "max_depth": [5, 10, 15, None],
        "min_samples_split": [2, 5, 10]
    }
    rf_search = RandomizedSearchCV(
        estimator=RandomForestRegressor(random_state=42, n_jobs=-1),
        param_distributions=rf_grid,
        n_iter=5,
        cv=3,
        scoring="neg_root_mean_squared_error",
        random_state=42,
        n_jobs=-1
    )
    logger.info("Tuning Random Forest Regressor...")
    rf_search.fit(X_train, y_train)
    best_rf = rf_search.best_estimator_
    logger.info("Best RF Hyperparameters: %s", rf_search.best_params_)

    # Update models dictionary with tuned versions
    tuned_models = {
        "Linear Regression": models["Linear Regression"].fit(X_train, y_train),
        "Random Forest (Tuned)": best_rf,
        "Gradient Boosting (Tuned)": best_gb
    }

    # 6. Evaluation and Comparison
    logger.info("Comparing final models on test split...")
    comparison_metrics = {}
    best_score = float("inf")
    best_model_name = ""
    best_model_obj = None

    for name, model in tuned_models.items():
        if not hasattr(model, "predict"):
            model.fit(X_train, y_train)
            
        y_pred = model.predict(X_test)
        metrics = evaluate_model(y_test, y_pred)
        comparison_metrics[name] = metrics
        
        logger.info("%s Test Metrics: RMSE=%.4f | MAE=%.4f | R2=%.4f", 
                    name, metrics["RMSE"], metrics["MAE"], metrics["R2"])
        
        if metrics["RMSE"] < best_score:
            best_score = metrics["RMSE"]
            best_model_name = name
            best_model_obj = model

    logger.info("Best performing model selected: %s (RMSE = %.4f)", best_model_name, best_score)

    # 7. Feature Importance (Ensemble models only)
    if hasattr(best_model_obj, "feature_importances_"):
        logger.info("Extracting feature importances for %s...", best_model_name)
        importances = best_model_obj.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        print("\n=== FEATURE IMPORTANCE RANKING ===")
        for f in range(min(10, len(feature_names))):
            idx = indices[f]
            print(f"{f+1}. Feature: {feature_names[idx]:<25} | Importance: {importances[idx]:.4f}")
        print("==================================\n")
    else:
        logger.info("Selected model (%s) does not support feature importance extraction.", best_model_name)

    # 8. Residual Analysis
    y_test_pred = best_model_obj.predict(X_test)
    residuals = y_test - y_test_pred
    
    residual_stats = {
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "min_residual": float(np.min(residuals)),
        "max_residual": float(np.max(residuals))
    }
    logger.info("Residual summary: Mean error = %.4f | Std Dev = %.4f", 
                residual_stats["mean_residual"], residual_stats["std_residual"])

    # 9. Model Serialization
    registry = ModelRegistry(registry_dir=model_dir)
    best_metrics = comparison_metrics[best_model_name]
    model_path, meta_path = registry.save_model(
        model=best_model_obj,
        feature_extractor=extractor,
        metrics=best_metrics,
        model_name="best_model"
    )
    logger.info("ML pipeline complete. Registered model saved at: %s", model_path)


if __name__ == "__main__":
    processed_csv = "data/processed/clean_data.csv"
    run_training_pipeline(data_path=processed_csv, model_dir="models")
