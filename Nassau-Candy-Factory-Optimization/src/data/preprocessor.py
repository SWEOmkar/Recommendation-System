"""Data preprocessor module for cleaning and validating Nassau Candy Distributor data.

This module implements a production-grade cleaning pipeline including missing
value handling, duplicate removal, date conversion, datatype optimization,
outlier detection, validation, and exporting cleaned datasets.
"""

import os
import logging
from typing import Dict, List, Tuple, Union, Optional
import pandas as pd
import numpy as np

# Configure logger for module-level reporting
logger = logging.getLogger(__name__)


class PreprocessorError(Exception):
    """Base exception class for preprocessor operations."""
    pass


class SchemaValidationError(PreprocessorError, KeyError):
    """Exception raised when dataset schema validation fails."""
    pass


class NassauPreprocessor:
    """A preprocessor pipeline for the Nassau Candy dataset.

    This class encapsulates data cleaning, type optimization, validation, and
    outlier detection strategies.
    """

    REQUIRED_COLUMNS = [
        "Row ID",
        "Order ID",
        "Order Date",
        "Ship Date",
        "Ship Mode",
        "Customer ID",
        "Country/Region",
        "City",
        "State/Province",
        "Postal Code",
        "Division",
        "Region",
        "Product ID",
        "Product Name",
        "Sales",
        "Units",
        "Gross Profit",
        "Cost",
    ]

    def __init__(self, date_shift_days: int = 1270) -> None:
        """Initializes the preprocessor.

        Args:
            date_shift_days (int): The number of days to shift ship dates backward
                to simulate realistic fulfillment cycles (default: 1270 days).
        """
        self.date_shift_days = date_shift_days
        logger.info(
            "Preprocessor initialized with date_shift_days=%d", date_shift_days
        )

    def load_data(self, file_path: str) -> pd.DataFrame:
        """Loads dataset from the specified CSV file.

        Args:
            file_path (str): The absolute or relative path to the CSV file.

        Returns:
            pd.DataFrame: Loaded raw dataframe.

        Raises:
            FileNotFoundError: If the file does not exist.
            PreprocessorError: If the file is not a valid CSV.
        """
        if not os.path.exists(file_path):
            logger.error("Data file not found at path: %s", file_path)
            raise FileNotFoundError("Required data file was not found.")

        try:
            logger.info("Loading raw data from %s...", file_path)
            df = pd.read_csv(file_path)
            logger.info("Successfully loaded raw dataset with shape %s", df.shape)
            return df
        except Exception as e:
            logger.error("Failed to load CSV file: %s", str(e))
            raise PreprocessorError("Failed to read the input data file.") from e

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validates that all required columns are present.

        Args:
            df (pd.DataFrame): Dataframe to validate.

        Returns:
            bool: True if schema is valid.

        Raises:
            SchemaValidationError: If one or more required columns are missing.
        """
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error("Schema validation failed. Missing columns: %s", missing_cols)
            raise SchemaValidationError("Dataset schema validation failed. Required columns are missing.")

        logger.info("Schema validation passed.")
        return True

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles missing values within the dataset.

        Drops rows containing nulls in critical identifiers or numeric columns.
        Imputes non-critical text columns.

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            pd.DataFrame: Cleaned dataframe.
        """
        df_cleaned = df.copy()

        # Check total missing before processing
        total_missing = df_cleaned.isnull().sum().sum()
        logger.info("Handling missing values. Initial null count: %d", total_missing)

        if total_missing > 0:
            # Critical columns where nulls are unacceptable
            critical_cols = ["Row ID", "Order ID", "Product ID", "Sales", "Units"]
            df_cleaned.dropna(subset=critical_cols, inplace=True)

            # Fill other categorical columns with placeholders
            text_cols = ["City", "State/Province", "Postal Code"]
            for col in text_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].fillna("Unknown")

            # Interpolate numeric columns if any remain missing
            for col in ["Gross Profit", "Cost"]:
                if col in df_cleaned.columns and df_cleaned[col].isnull().any():
                    df_cleaned[col] = df_cleaned[col].fillna(0.0)

            logger.info(
                "Missing values resolved. Remaining null count: %d",
                df_cleaned.isnull().sum().sum(),
            )
        else:
            logger.info("No missing values found.")

        return df_cleaned

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identifies and removes duplicate records based on Row ID.

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            pd.DataFrame: Deduplicated dataframe.
        """
        df_cleaned = df.copy()

        initial_count = len(df_cleaned)
        df_cleaned.drop_duplicates(subset=["Row ID"], keep="first", inplace=True)
        final_count = len(df_cleaned)

        removed_rows = initial_count - final_count
        if removed_rows > 0:
            logger.warning(
                "Removed %d duplicate rows based on Row ID.", removed_rows
            )
        else:
            logger.info("No duplicate rows found based on Row ID.")

        return df_cleaned

    def convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts date columns and adjusts lead time year offsets.

        Calculates lead_time_days and shifts Ship Date to create a realistic
        operational distribution.

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            pd.DataFrame: Dataframe with parsed datetime and lead time columns.
        """
        df_cleaned = df.copy()

        try:
            logger.info("Converting date columns and calculating lead times...")
            
            # Using format='mixed' allows fast performance with flexible formats
            for col in ["Order Date", "Ship Date"]:
                df_cleaned[col] = pd.to_datetime(df_cleaned[col], format="mixed")

            # Calculate raw lead time (original days)
            df_cleaned["raw_lead_time_days"] = (
                df_cleaned["Ship Date"] - df_cleaned["Order Date"]
            ).dt.days

            # Shift Ship Date backward to correct IT database epoch offset (e.g. ~3.5 years)
            # and calculate adjusted lead time (realistic 2-10 business days)
            df_cleaned["adjusted_ship_date"] = df_cleaned["Ship Date"] - pd.to_timedelta(
                self.date_shift_days, unit="D"
            )

            # Recalculate lead time (days)
            df_cleaned["lead_time_days"] = (
                df_cleaned["adjusted_ship_date"] - df_cleaned["Order Date"]
            ).dt.days

            # Correct any negative lead times that arise due to shift logic
            df_cleaned["lead_time_days"] = df_cleaned["lead_time_days"].clip(lower=1)

            logger.info("Dates successfully processed.")
            return df_cleaned
        except Exception as e:
            logger.error("Error during date conversion: %s", str(e))
            raise PreprocessorError("An error occurred during date processing.") from e

    def optimize_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimizes numerical and string column types to reduce memory use.

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            pd.DataFrame: Dataframe with optimized data types.
        """
        df_opt = df.copy()
        logger.info("Optimizing data types...")
        mem_before = df_opt.memory_usage(deep=True).sum() / 1024**2

        # Convert integers
        int_cols = ["Row ID", "Units"]
        for col in int_cols:
            if col in df_opt.columns:
                df_opt[col] = pd.to_numeric(df_opt[col], downcast="integer")

        # Convert floats
        float_cols = ["Sales", "Gross Profit", "Cost"]
        for col in float_cols:
            if col in df_opt.columns:
                df_opt[col] = pd.to_numeric(df_opt[col], downcast="float")

        # Convert categorical fields
        cat_cols = ["Ship Mode", "Division", "Region", "Country/Region"]
        for col in cat_cols:
            if col in df_opt.columns:
                df_opt[col] = df_opt[col].astype("category")

        mem_after = df_opt.memory_usage(deep=True).sum() / 1024**2
        logger.info(
            "Memory optimization complete: %.2f MB -> %.2f MB (%.1f%% reduction)",
            mem_before,
            mem_after,
            ((mem_before - mem_after) / mem_before) * 100,
        )
        return df_opt

    def detect_outliers_iqr(
        self, df: pd.DataFrame, columns: List[str], threshold: float = 3.0
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Identifies outliers using the Interquartile Range (IQR) method.

        Does not delete rows to avoid losing valuable transactional records.
        Instead, caps extreme values to the upper and lower bounds.

        Args:
            df (pd.DataFrame): Input dataframe.
            columns (List[str]): Columns to clean from outliers.
            threshold (float): IQR multiplier (default: 3.0 for extreme outliers).

        Returns:
            Tuple[pd.DataFrame, Dict[str, int]]: Capped dataframe and outliers count dict.
        """
        df_cleaned = df.copy()
        outliers_count = {}

        logger.info("Executing outlier detection and capping (threshold=%.1f)...", threshold)

        for col in columns:
            if col not in df_cleaned.columns:
                continue

            q25 = df_cleaned[col].quantile(0.25)
            q75 = df_cleaned[col].quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - (threshold * iqr)
            upper_bound = q75 + (threshold * iqr)

            # Identify count
            is_outlier = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
            count = is_outlier.sum()
            outliers_count[col] = count

            if count > 0:
                logger.warning(
                    "Column '%s': Found %d outliers. Capping values to range [%.2f, %.2f]",
                    col,
                    count,
                    lower_bound,
                    upper_bound,
                )
                df_cleaned[col] = np.clip(df_cleaned[col], lower_bound, upper_bound)
            else:
                logger.info("Column '%s': Zero outliers detected.", col)

        return df_cleaned, outliers_count

    def validate_financial_consistency(self, df: pd.DataFrame) -> bool:
        """Validates calculations (Sales = Cost + Gross Profit).

        Args:
            df (pd.DataFrame): Input dataframe.

        Returns:
            bool: True if consistency holds.
        """
        # Allow a margin of 0.05 for rounding differences
        diffs = np.abs((df["Sales"] - df["Cost"]) - df["Gross Profit"])
        violations = (diffs > 0.05).sum()

        if violations > 0:
            logger.warning(
                "Financial consistency check failed on %d records. Difference detected.",
                violations,
            )
            return False

        logger.info("Financial consistency checks successfully verified.")
        return True

    def run_pipeline(
        self, raw_file_path: str, processed_output_path: str
    ) -> pd.DataFrame:
        """Runs the entire preprocessor pipeline.

        Args:
            raw_file_path (str): Path to raw CSV.
            processed_output_path (str): Output path to save the cleaned CSV.

        Returns:
            pd.DataFrame: Cleaned, validated, and optimized dataframe.
        """
        logger.info("=== Starting Preprocessor Ingestion Pipeline ===")
        
        try:
            # 1. Load Data
            df = self.load_data(raw_file_path)

            # 2. Validate Schema
            self.validate_schema(df)

            # 3. Handle Duplicates
            df = self.remove_duplicates(df)

            # 4. Handle Missing Values
            df = self.handle_missing_values(df)

            # 5. Convert Dates and offsets
            df = self.convert_dates(df)

            # 6. Check Outliers
            df, outliers = self.detect_outliers_iqr(
                df, columns=["Sales", "Units", "Gross Profit", "Cost"], threshold=3.0
            )

            # 7. Financial Audits
            self.validate_financial_consistency(df)

            # 8. Optimize Types
            df = self.optimize_datatypes(df)

            # 9. Save Dataset
            os.makedirs(os.path.dirname(processed_output_path), exist_ok=True)
            df.to_csv(processed_output_path, index=False)
            logger.info("Saved cleaned dataset successfully to: %s", processed_output_path)
            
            logger.info("=== Preprocessor Ingestion Pipeline Completed Successfully ===")
            return df
        except Exception as e:
            logger.critical("Ingestion pipeline aborted due to critical error: %s", str(e))
            raise
