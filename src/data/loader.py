"""
CSV Data Loader Module

This module provides functionality to load and validate CSV data from local
files or URLs, ensuring they match the expected schema for dental KPI metrics.
"""

import pandas as pd
import requests
from pathlib import Path
from typing import Dict, List, Optional, Union
import urllib.parse

from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Define expected columns and their data types for detailed KPI metrics data
EXPECTED_COLUMNS = {
    "Date": "datetime64[ns]",
    "Location": "object",
    "MetricName": "object",
    "Value": "float64",
    "Target": "float64"
}

# Define expected columns for KPI definitions file (like dental_kpi_metrics.csv)
KPI_DEFINITION_COLUMNS = [
    "KPI", "Formula", "Low", "Target", "Stretch"
]


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
            try:
                response = requests.get(path_or_url, timeout=10)
                response.raise_for_status()  # Raise an error for bad status codes
                # Create a DataFrame from the downloaded content
                df = pd.read_csv(pd.io.common.StringIO(response.text))
            except requests.exceptions.RequestException as e:
                logger.error(f"Error downloading CSV from URL: {str(e)}")
                raise ConnectionError(f"Error downloading CSV from URL: {str(e)}")
        else:
            # Handle local files
            file_path = Path(path_or_url)
            if not file_path.exists():
                logger.error(f"File not found: {path_or_url}")
                raise FileNotFoundError(f"File not found: {path_or_url}")
                
            logger.debug(f"Loading local CSV file: {path_or_url}")
            df = pd.read_csv(file_path, skipinitialspace=True)
        
        # Clean column names (remove whitespace)
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
        
        logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    except FileNotFoundError:
        logger.error(f"File not found: {path_or_url}")
        raise
    except pd.errors.ParserError as e:
        logger.error(f"Invalid CSV format in file: {path_or_url}. Error: {str(e)}")
        raise ValueError(f"Invalid CSV format in file: {path_or_url}. Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading CSV data: {str(e)}")
        raise


def is_kpi_definition_file(df: pd.DataFrame) -> bool:
    """
    Determine if the DataFrame appears to be a KPI definition file.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if the DataFrame appears to be a KPI definition file
    """
    # Check if the first column is named 'KPI' (regardless of case)
    if len(df.columns) >= 3:  # At minimum, expect KPI, Formula, and some target columns
        if df.columns[0].strip().upper() == 'KPI':
            # Also check for formula column (second column)
            if df.columns[1].strip().upper() == 'FORMULA':
                return True
            
            # Check if any column has formula or similar in the name
            for col in df.columns:
                if 'FORMULA' in col.strip().upper():
                    return True
    return False


def validate_kpi_definition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the DataFrame appears to be a valid KPI definition file.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        The validated DataFrame
        
    Raises:
        ValueError: If the DataFrame doesn't contain the required KPI definition columns
    """
    logger.info("Validating KPI definition schema")
    
    # Convert column names to uppercase for case-insensitive comparison
    column_uppers = [col.strip().upper() for col in df.columns]
    
    # Check for required columns (case-insensitive)
    missing_columns = []
    if 'KPI' not in column_uppers:
        missing_columns.append('KPI')
    
    if 'FORMULA' not in column_uppers and not any('FORMULA' in col for col in column_uppers):
        missing_columns.append('Formula')
    
    if missing_columns:
        error_msg = f"KPI definition CSV is missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for target/threshold columns (at least one should exist)
    threshold_cols = ['LOW', 'TARGET', 'STRETCH']
    if not any(col in column_uppers for col in threshold_cols):
        error_msg = "KPI definition CSV is missing target threshold columns (Low, Target, or Stretch)"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Ensure there are KPI entries
    if len(df) == 0:
        error_msg = "KPI definition CSV contains no KPI entries"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("KPI definition schema validation successful")
    return df


def validate_kpi_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that the DataFrame has the expected columns and data types for KPI metrics data.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        The validated DataFrame (possibly with converted data types)
        
    Raises:
        ValueError: If the DataFrame is missing required columns or has invalid data types
    """
    logger.info("Validating KPI metrics data schema")
    
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
                if dtype == "datetime64[ns]":
                    # Try to parse dates, handling various formats
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception as e:
                        logger.warning(f"Failed to convert {col} to datetime, keeping as is: {str(e)}")
                elif dtype in ["float64", "int64"]:
                    # For numeric columns, convert and handle any errors
                    try:
                        # First strip any '%' signs and convert to appropriate numeric type
                        if df[col].dtype == 'object':
                            df[col] = df[col].str.replace('%', '').str.strip()
                        df[col] = df[col].astype(dtype)
                    except Exception as e:
                        logger.warning(f"Failed to convert {col} to {dtype}, attempting to handle mixed formats")
                        # Try more aggressive conversion for mixed formats
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except Exception as nested_e:
                            logger.warning(f"Still failed to convert {col}: {str(nested_e)}")
    except Exception as e:
        error_msg = f"Error converting data types: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for empty DataFrame after validation
    if df.empty:
        error_msg = "CSV contains no valid data after validation"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("KPI metrics data schema validation successful")
    return df


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the schema of the loaded DataFrame, detecting if it's a 
    KPI definition file or a KPI metrics data file.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        The validated DataFrame
        
    Raises:
        ValueError: If the DataFrame doesn't conform to either expected schema
    """
    # Detect if this appears to be a KPI definition file
    if is_kpi_definition_file(df):
        logger.info("Detected KPI definition file format")
        return validate_kpi_definition(df)
    else:
        logger.info("Detected KPI metrics data file format")
        return validate_kpi_data(df)


def load_and_validate_csv(path_or_url: Union[str, Path]) -> pd.DataFrame:
    """
    Load a CSV file and validate its schema, automatically detecting
    whether it's a KPI definition file or KPI metrics data file.
    
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