"""Main entry point to execute the data preprocessing pipeline.

Loads raw data, cleans it using NassauPreprocessor, and saves it.
"""

import os
import sys
import logging

# Ensure src/ is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from data.preprocessor import NassauPreprocessor

# Set logging level
logging.basicConfig(level=logging.INFO)

def main():
    # Try local project subdirectory first, then parent directory fallback
    raw_path_local = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data", "raw", "Nassau Candy Distributor.csv")
    )
    raw_path_parent = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "Nassau Candy Distributor.csv")
    )
    raw_path = raw_path_local if os.path.exists(raw_path_local) else raw_path_parent
    
    processed_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "data", "processed", "clean_data.csv")
    )
    
    preprocessor = NassauPreprocessor(date_shift_days=1270)
    
    try:
        cleaned_df = preprocessor.run_pipeline(raw_path, processed_path)
        print(f"Success! Cleaned data shape: {cleaned_df.shape}")
    except Exception:
        logging.exception("Preprocessing pipeline failed")
        print("Preprocessing failed. Check logs for details.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
