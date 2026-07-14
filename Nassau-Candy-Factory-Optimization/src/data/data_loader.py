"""Data loader module for loading and coordinating dataset assets.

This module coordinates raw file ingestion and manages data loader pipelines.
"""

import os
import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

def get_raw_dataset(file_path: str) -> pd.DataFrame:
    """Ingests a raw CSV file.

    Args:
        file_path (str): The file path to the raw CSV file.

    Returns:
        pd.DataFrame: The loaded pandas dataframe.

    Raises:
        FileNotFoundError: If the file path does not exist (with a generic message).
    """
    if not os.path.exists(file_path):
        logger.error("Dataset not found at path: %s", file_path)
        raise FileNotFoundError("Required dataset file was not found.")
        
    logger.info("Reading raw dataset from %s...", file_path)
    return pd.read_csv(file_path)
