"""
CSV Data Loader Module

This module provides functionality to load and validate CSV data from local
files or URLs, ensuring they match the expected schema for dental KPI metrics.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
import urllib.parse

from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define expected columns and their data types
EXPECTED_COLUMNS = {
    # This will be updated with the actual column names from the dental KPI metrics
    # For now, using placeholder column definitions
    "Date": "datetime64[ns]",
    "Location": "object",
    "MetricName": "object",
    "Value": "float64",
    "Target": "float64",
}


def is_url(path_or_url: str) -> bool:
    """
    Check if the provided string is a URL.
    
    Args:
        path_or_url: String that might be a URL or a local file path
        
    Returns:
        True if the string appears to be a URL, False otherwise
    """
    try:
        result = urllib.parse.urlparse(path_or_url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def load_csv(path_or_url: Union[str, Path]) -> pd.DataFrame:
    """
    Load CSV data from a local file path or URL.
    
    Args:
        path_or_url: Path to a local CSV file or a URL to a remote CSV file
        
    Returns:
        A pandas DataFrame containing the loaded CSV data
        
    Raises:
        FileNotFoundError: If the file doesn't exist at the specified path
        ValueError: If the file format is invalid or missing required columns
        ConnectionError: If there's an issue downloading the file from a URL
    """
    # Convert Path objects to strings
    if isinstance(path_or_url, Path):
        path_or_url = str(path_or_url)
    
    logger.info(f"Loading CSV data from: {path_or_url}")
    
    try:
        # Handle URLs
        if is_url(path_or_url):
            logger.debug(f"Detected URL, downloading CSV from: {path_or_url}")
            df = pd.read_csv(path_or_url)
        else:
            # Handle local files
            logger.debug(f"Loading local CSV file: {path_or_url}")
            df = pd.read_csv(path_or_url)
        
        logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    except FileNotFoundError:
        logger.error(f"File not found: {path_or_url}")
        raise
    except pd.errors.ParserError:
        logger.error(f"Invalid CSV format in file: {path_or_url}")
        raise ValueError(f"Invalid CSV format in file: {path_or_url}")
    except Exception as e:
        logger.error(f"Error loading CSV data: {str(e)}")
        raise


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the DataFrame has the expected columns and data types.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        The validated DataFrame (possibly with converted data types)
        
    Raises:
        ValueError: If the DataFrame is missing required columns or has invalid data types
    """
    logger.info("Validating CSV schema")
    
    # Check for required columns
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        error_msg = f"CSV is missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Attempt to convert data types
    try:
        for col, dtype in EXPECTED_COLUMNS.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
    except Exception as e:
        error_msg = f"Error converting data types: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("CSV schema validation successful")
    return df


def load_and_validate_csv(path_or_url: Union[str, Path]) -> pd.DataFrame:
    """
    Load a CSV file and validate its schema.
    
    Args:
        path_or_url: Path to a local CSV file or a URL to a remote CSV file
        
    Returns:
        A validated pandas DataFrame containing the loaded CSV data
        
    Raises:
        FileNotFoundError: If the file doesn't exist at the specified path
        ValueError: If the file format is invalid or missing required columns
        ConnectionError: If there's an issue downloading the file from a URL
    """
    df = load_csv(path_or_url)
    return validate_schema(df) 