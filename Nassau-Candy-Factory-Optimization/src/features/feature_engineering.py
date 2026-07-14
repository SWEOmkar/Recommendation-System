"""Feature engineering module for Nassau Candy Distributor lead-time prediction.

This module provides the NassauFeatureExtractor class to construct modeling-ready
feature sets, applying cyclical temporal transformations, one-hot encoding,
interaction term creation, feature scaling, and correlation-based feature selection.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger(__name__)


class NassauFeatureExtractor(BaseEstimator, TransformerMixin):
    """Pipeline component for feature engineering.

    Fits on training data and transforms datasets to prevent data leakage during
    scaling, encoding, and selection.
    """

    def __init__(
        self,
        numerical_cols: List[str] = ["Sales", "Units", "Gross Profit", "Cost"],
        categorical_cols: List[str] = ["Ship Mode", "Division", "Region", "Product ID"],
        correlation_threshold: float = 0.95,
    ) -> None:
        """Initializes the feature extractor.

        Args:
            numerical_cols (List[str]): Numerical columns to scale.
            categorical_cols (List[str]): Categorical columns to encode.
            correlation_threshold (float): Correlation limit to drop collinear features.
        """
        self.numerical_cols = numerical_cols
        self.categorical_cols = categorical_cols
        self.correlation_threshold = correlation_threshold

        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.encoded_feature_names_: List[str] = []
        self.selected_features_: List[str] = []
        self.is_fitted = False

    def _add_cyclical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies sine and cosine transformations to monthly and weekday values.

        Args:
            df (pd.DataFrame): Dataframe containing 'Order Date'.

        Returns:
            pd.DataFrame: Dataframe with cyclical columns.
        """
        df_out = df.copy()

        # Monthly cyclicity
        month_vals = df_out["Order Date"].dt.month
        df_out["order_month_sin"] = np.sin(2 * np.pi * month_vals / 12.0)
        df_out["order_month_cos"] = np.cos(2 * np.pi * month_vals / 12.0)

        # Weekday cyclicity
        weekday_vals = df_out["Order Date"].dt.weekday
        df_out["order_weekday_sin"] = np.sin(2 * np.pi * weekday_vals / 7.0)
        df_out["order_weekday_cos"] = np.cos(2 * np.pi * weekday_vals / 7.0)

        logger.debug("Cyclical temporal features constructed.")
        return df_out

    def _create_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes interaction features.

        Includes:
        - profit_margin_pct
        - units_x_sales

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            pd.DataFrame: Dataframe with interaction terms.
        """
        df_out = df.copy()

        # Profit margin (%) - Proxy for shipping priority
        df_out["profit_margin_pct"] = (
            df_out["Gross Profit"] / df_out["Sales"].replace(0, 0.01)
        ) * 100

        # Units * Sales - Order density index
        df_out["units_x_sales"] = df_out["Units"] * df_out["Sales"]

        logger.debug("Interaction and ratio features constructed.")
        return df_out

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "NassauFeatureExtractor":
        """Fits the scaling, encoding, and feature selection parameters.

        Args:
            X (pd.DataFrame): Training features.
            y (Optional[pd.Series]): Target values.

        Returns:
            self: The fitted extractor instance.
        """
        logger.info("Fitting feature extractor pipeline...")

        # 1. Fit One-Hot Encoder
        self.encoder.fit(X[self.categorical_cols])
        # Retrieve encoded names
        self.encoded_feature_names_ = list(
            self.encoder.get_feature_names_out(self.categorical_cols)
        )

        # 2. Derive columns to fit scaler
        X_temp = self._add_cyclical_features(X)
        X_temp = self._create_interactions(X_temp)

        # Numeric columns include original numericals + cyclical + interactions
        scaler_cols = self.numerical_cols + [
            "order_month_sin",
            "order_month_cos",
            "order_weekday_sin",
            "order_weekday_cos",
            "profit_margin_pct",
            "units_x_sales",
        ]

        self.scaler.fit(X_temp[scaler_cols])

        # 3. Feature Selection: Build full unselected dataframe to evaluate correlation
        X_encoded_arr = self.encoder.transform(X[self.categorical_cols])
        X_encoded_df = pd.DataFrame(
            X_encoded_arr, columns=self.encoded_feature_names_, index=X.index
        )
        X_scaled_arr = self.scaler.transform(X_temp[scaler_cols])
        X_scaled_df = pd.DataFrame(X_scaled_arr, columns=scaler_cols, index=X.index)

        X_full = pd.concat([X_scaled_df, X_encoded_df], axis=1)

        # Find collinear columns to drop
        corr_matrix = X_full.corr().abs()
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )
        to_drop = [
            column
            for column in upper.columns
            if any(upper[column] > self.correlation_threshold)
        ]

        logger.info(
            "Feature Selection: Identified %d highly collinear columns for exclusion: %s",
            len(to_drop),
            to_drop,
        )

        self.selected_features_ = [col for col in X_full.columns if col not in to_drop]
        logger.info(
            "Selected %d features out of %d total columns.",
            len(self.selected_features_),
            X_full.shape[1],
        )

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw input features into modeling vectors.

        Args:
            X (pd.DataFrame): Raw dataframe input.

        Returns:
            pd.DataFrame: Cleaned, encoded, scaled, and selected features df.

        Raises:
            RuntimeError: If the transformer has not been fitted yet.
        """
        if not self.is_fitted:
            logger.error("Attempted transformation before fitting.")
            raise RuntimeError("Feature extraction pipeline has not been initialized.")

        # 1. Cyclical and interactions
        X_temp = self._add_cyclical_features(X)
        X_temp = self._create_interactions(X_temp)

        scaler_cols = self.numerical_cols + [
            "order_month_sin",
            "order_month_cos",
            "order_weekday_sin",
            "order_weekday_cos",
            "profit_margin_pct",
            "units_x_sales",
        ]

        # 2. Scale continuous values
        X_scaled_arr = self.scaler.transform(X_temp[scaler_cols])
        X_scaled_df = pd.DataFrame(X_scaled_arr, columns=scaler_cols, index=X.index)

        # 3. One-hot encode categorical values
        X_encoded_arr = self.encoder.transform(X[self.categorical_cols])
        X_encoded_df = pd.DataFrame(
            X_encoded_arr, columns=self.encoded_feature_names_, index=X.index
        )

        # 4. Merge and select final features
        X_full = pd.concat([X_scaled_df, X_encoded_df], axis=1)
        X_selected = X_full[self.selected_features_]

        logger.debug("Feature extraction and selection transform complete.")
        return X_selected
