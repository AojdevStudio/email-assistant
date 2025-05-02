"""
Tests for the CSV data loader module.

This module tests the functionality to load and validate CSV data
from local files, ensuring proper validation for both KPI definition
files and KPI metrics data files.
"""

import os
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from src.data.loader import (
    load_csv, 
    validate_schema, 
    load_and_validate_csv,
    is_url,
    is_kpi_definition_file,
    validate_kpi_definition,
    validate_kpi_data
)

# Sample KPI definition data (like in dental_kpi_metrics.csv)
SAMPLE_KPI_DEFINITION = """
KPI                      , Formula                                  , Low     , Target      , Stretch
Collection %             , "total_collections / net_production"     , "< 95 %", "99 – 103 %", "> 105 %"
Case-Acceptance % (by $) , "accepted_tx$ / proposed_tx$"            , "< 50 %", "60 %"      , "≥ 70 %"
"""

# Sample KPI metrics data (like mentioned in README.md)
SAMPLE_KPI_METRICS = """
Date,Location,MetricName,Value,Target
2023-01-01,Downtown Office,Case Acceptance Rate,68,75
2023-01-01,Downtown Office,Production Per Hour,350,400
"""

# Invalid CSV samples for testing error handling
INVALID_KPI_DEFINITION = """
KPI
Collection %
"""

INVALID_KPI_METRICS = """
Date,Location
2023-01-01,Downtown Office
"""


def test_is_url():
    """Test the is_url function with various inputs."""
    assert is_url("http://example.com/data.csv") is True
    assert is_url("https://example.com/data.csv") is True
    assert is_url("file.csv") is False
    assert is_url("/path/to/file.csv") is False
    assert is_url("C:\\path\\to\\file.csv") is False


def test_is_kpi_definition_file():
    """Test the is_kpi_definition_file function."""
    # Valid KPI definition
    df = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_DEFINITION))
    assert is_kpi_definition_file(df) is True
    
    # KPI metrics data
    df = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_METRICS))
    assert is_kpi_definition_file(df) is False
    
    # Invalid format
    df = pd.DataFrame({'Column1': [1, 2], 'Column2': [3, 4]})
    assert is_kpi_definition_file(df) is False


@patch('src.data.loader.pd.read_csv')
def test_load_csv_local_file(mock_read_csv):
    """Test loading a CSV from a local file."""
    # Mock Path.exists to return True
    with patch('pathlib.Path.exists', return_value=True):
        # Set up the mock
        mock_df = pd.DataFrame({
            'Date': ['2023-01-01', '2023-01-02'],
            'Value': [1, 2]
        })
        mock_read_csv.return_value = mock_df
        
        # Call the function
        result = load_csv('test.csv')
        
        # Assertions
        mock_read_csv.assert_called_once()
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['Date', 'Value']


@patch('src.data.loader.requests.get')
def test_load_csv_url(mock_get):
    """Test loading a CSV from a URL."""
    # Set up the mock
    mock_response = MagicMock()
    mock_response.text = SAMPLE_KPI_METRICS
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    # Call the function with patched pd.read_csv
    with patch('src.data.loader.pd.read_csv', return_value=pd.DataFrame({
        'Date': ['2023-01-01', '2023-01-01'],
        'Location': ['Downtown Office', 'Downtown Office'],
        'MetricName': ['Case Acceptance Rate', 'Production Per Hour'],
        'Value': [68, 350],
        'Target': [75, 400]
    })):
        result = load_csv('http://example.com/data.csv')
    
    # Assertions
    mock_get.assert_called_once_with('http://example.com/data.csv', timeout=10)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


def test_validate_kpi_definition():
    """Test validation of KPI definition data."""
    # Valid KPI definition
    df = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_DEFINITION))
    result = validate_kpi_definition(df)
    assert isinstance(result, pd.DataFrame)
    
    # Invalid KPI definition (missing required columns)
    with pytest.raises(ValueError):
        df = pd.read_csv(pd.io.common.StringIO(INVALID_KPI_DEFINITION))
        validate_kpi_definition(df)
    
    # Empty DataFrame
    with pytest.raises(ValueError):
        validate_kpi_definition(pd.DataFrame())


def test_validate_kpi_data():
    """Test validation of KPI metrics data."""
    # Valid KPI metrics data
    df = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_METRICS))
    result = validate_kpi_data(df)
    assert isinstance(result, pd.DataFrame)
    
    # Invalid KPI metrics data (missing required columns)
    with pytest.raises(ValueError):
        df = pd.read_csv(pd.io.common.StringIO(INVALID_KPI_METRICS))
        validate_kpi_data(df)
    
    # Empty DataFrame
    with pytest.raises(ValueError):
        validate_kpi_data(pd.DataFrame())


def test_validate_schema():
    """Test schema validation for both KPI definition and metrics data."""
    # KPI definition format
    df_def = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_DEFINITION))
    result_def = validate_schema(df_def)
    assert isinstance(result_def, pd.DataFrame)
    
    # KPI metrics format
    df_metrics = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_METRICS))
    result_metrics = validate_schema(df_metrics)
    assert isinstance(result_metrics, pd.DataFrame)


@patch('src.data.loader.load_csv')
@patch('src.data.loader.validate_schema')
def test_load_and_validate_csv(mock_validate_schema, mock_load_csv):
    """Test the end-to-end load and validate function."""
    # Set up mocks
    mock_df = pd.DataFrame({'Column1': [1, 2]})
    mock_load_csv.return_value = mock_df
    mock_validate_schema.return_value = mock_df
    
    # Call the function
    result = load_and_validate_csv('test.csv')
    
    # Assertions
    mock_load_csv.assert_called_once_with('test.csv')
    mock_validate_schema.assert_called_once_with(mock_df)
    assert result is mock_df


@patch('src.data.loader.load_csv')
def test_load_and_validate_csv_integration(mock_load_csv):
    """Integration test for loading and validating CSV data."""
    # Test with KPI definition data
    df_def = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_DEFINITION))
    mock_load_csv.return_value = df_def
    result_def = load_and_validate_csv('kpi_definitions.csv')
    assert isinstance(result_def, pd.DataFrame)
    
    # Test with KPI metrics data
    df_metrics = pd.read_csv(pd.io.common.StringIO(SAMPLE_KPI_METRICS))
    mock_load_csv.return_value = df_metrics
    result_metrics = load_and_validate_csv('kpi_metrics.csv')
    assert isinstance(result_metrics, pd.DataFrame)


def test_load_csv_file_not_found():
    """Test load_csv with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_csv('non_existent_file.csv')


@patch('src.data.loader.requests.get')
def test_load_csv_url_error(mock_get):
    """Test handling of URL download errors."""
    # Set up mock to raise an exception
    mock_get.side_effect = Exception("Connection error")
    
    # Call the function and expect an exception
    with pytest.raises(Exception):
        load_csv('http://example.com/data.csv')


def test_handle_percentage_values():
    """Test handling of percentage values in CSV."""
    # Create a DataFrame with percentage values
    csv_data = """Date,Location,MetricName,Value,Target
2023-01-01,Downtown Office,Collection Rate,95%,99%"""
    
    df = pd.read_csv(pd.io.common.StringIO(csv_data))
    
    # Patch load_csv to return our DataFrame
    with patch('src.data.loader.load_csv', return_value=df):
        result = load_and_validate_csv('test.csv')
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    # The Value column should be converted to float
    assert pd.api.types.is_numeric_dtype(result['Value'])
    assert result['Value'].iloc[0] == 95.0


def test_real_kpi_definition_file():
    """Integration test using the actual dental_kpi_metrics.csv file."""
    # Path to the actual KPI definition file in the project root
    kpi_def_path = Path(__file__).parent.parent.parent / 'dental_kpi_metrics.csv'
    
    # Skip test if file doesn't exist
    if not kpi_def_path.exists():
        pytest.skip(f"Real KPI definition file not found at {kpi_def_path}")
    
    # Load and validate the file
    result = load_and_validate_csv(kpi_def_path)
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert "KPI" in result.columns
    assert len(result) > 0
    assert "Formula" in result.columns
    # Check if either Low, Target, or Stretch columns are present
    target_columns = [col for col in result.columns if col in ["Low", "Target", "Stretch"]]
    assert len(target_columns) > 0 