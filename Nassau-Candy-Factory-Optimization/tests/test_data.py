"""Unit tests for the Nassau Candy dataset preprocessing module.

This module tests duplicate removal, date parsing, outlier detection,
datatype optimization, and schema validation.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from data.preprocessor import NassauPreprocessor


class TestNassauPreprocessor(unittest.TestCase):
    """Test suite for the NassauPreprocessor class."""

    def setUp(self) -> None:
        """Sets up mock test data."""
        self.preprocessor = NassauPreprocessor(date_shift_days=10)
        self.mock_data = pd.DataFrame(
            {
                "Row ID": [1, 2, 2, 3],  # Duplicate Row ID 2
                "Order ID": ["ORD-1", "ORD-2", "ORD-2", "ORD-3"],
                "Order Date": ["01-01-2024", "02-01-2024", "02-01-2024", "03-01-2024"],
                "Ship Date": ["15-01-2024", "16-01-2024", "16-01-2024", "17-01-2024"],
                "Ship Mode": ["Standard", "Second Class", "Second Class", "First Class"],
                "Customer ID": ["C-1", "C-2", "C-2", "C-3"],
                "Country/Region": ["United States", "United States", "United States", "Canada"],
                "City": ["Houston", "Los Angeles", "Los Angeles", "Toronto"],
                "State/Province": ["Texas", "California", "California", "Ontario"],
                "Postal Code": ["77095", "90049", "90049", "M5V"],
                "Division": ["Chocolate", "Chocolate", "Chocolate", "Sugar"],
                "Region": ["Interior", "Pacific", "Pacific", "Atlantic"],
                "Product ID": ["PROD-1", "PROD-2", "PROD-2", "PROD-3"],
                "Product Name": ["Wonka Bar", "Kazookles", "Kazookles", "Nerds"],
                "Sales": [10.0, 20.0, 20.0, 1000.0],  # Outlier in row 4
                "Units": [2, 4, 4, 10],
                "Gross Profit": [4.0, 8.0, 8.0, 400.0],
                "Cost": [6.0, 12.0, 12.0, 600.0],
            }
        )

    def test_schema_validation_passes(self) -> None:
        """Tests that a correct schema passes validation."""
        self.assertTrue(self.preprocessor.validate_schema(self.mock_data))

    def test_schema_validation_fails(self) -> None:
        """Tests that an incorrect schema raises a KeyError."""
        invalid_data = self.mock_data.drop(columns=["Sales"])
        with self.assertRaises(KeyError):
            self.preprocessor.validate_schema(invalid_data)

    def test_remove_duplicates(self) -> None:
        """Tests that duplicate records are correctly removed based on Row ID."""
        cleaned = self.preprocessor.remove_duplicates(self.mock_data)
        self.assertEqual(len(cleaned), 3)
        self.assertEqual(list(cleaned["Row ID"]), [1, 2, 3])

    def test_date_conversion(self) -> None:
        """Tests date parsing and adjusted lead time calculations."""
        # Clean duplicates first
        cleaned = self.preprocessor.remove_duplicates(self.mock_data)
        dated = self.preprocessor.convert_dates(cleaned)

        self.assertTrue(pd.api.types.is_datetime64_any_dtype(dated["Order Date"]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(dated["Ship Date"]))
        
        # Row 1 original gap is 14 days (15-Jan - 1-Jan)
        # With date_shift_days=10, the adjusted lead time should be 4 days
        self.assertEqual(dated.iloc[0]["lead_time_days"], 4)

    def test_datatype_optimization(self) -> None:
        """Tests numerical downcasting and category encoding."""
        optimized = self.preprocessor.optimize_datatypes(self.mock_data)
        self.assertEqual(optimized["Ship Mode"].dtype, "category")
        self.assertEqual(optimized["Division"].dtype, "category")
        # Sales should be downcast to float32
        self.assertEqual(optimized["Sales"].dtype, np.float32)
        # Units should be downcast to int8/int16
        self.assertTrue(
            optimized["Units"].dtype in [np.int8, np.int16, np.int32, np.int64]
        )

    def test_outlier_detection_iqr(self) -> None:
        """Tests outlier detection using IQR and capping values."""
        # Row 4 (Sales=1000) is an outlier compared to 10 and 20.
        # Running outlier detection on Sales should cap the 1000 value
        capped, counts = self.preprocessor.detect_outliers_iqr(
            self.mock_data, columns=["Sales"], threshold=1.5
        )
        self.assertEqual(counts["Sales"], 1)
        self.assertLess(capped.iloc[3]["Sales"], 1000.0)


if __name__ == "__main__":
    unittest.main()
