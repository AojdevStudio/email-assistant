"""
Tests for the Data Analysis and Benchmark Comparison functionality.
"""
import pandas as pd
import pytest
import numpy as np
from typing import Dict, Tuple

from src.data.analyzer import (
    parse_benchmark_value,
    is_value_in_band,
    determine_kpi_band,
    load_benchmarks,
    calculate_variance,
    analyze_kpi_metrics,
    sanitize_dataframe
)

class TestAnalyzer:
    """Tests for the analyzer module."""
    
    def test_parse_benchmark_value(self):
        """Test parsing various benchmark string formats."""
        # Test with percentage
        assert parse_benchmark_value("< 95 %") == ("<", 0.95)
        assert parse_benchmark_value("> 105 %") == (">", 1.05)
        
        # Test with absolute values
        assert parse_benchmark_value("< 300") == ("<", 300.0)
        assert parse_benchmark_value("> 550") == (">", 550.0)
        
        # Test with ranges
        assert parse_benchmark_value("99 - 103 %") == ("range", (0.99, 1.03))
        assert parse_benchmark_value("300 - 500") == ("range", (300.0, 500.0))
        
        # Test with en-dash
        assert parse_benchmark_value("300 – 500") == ("range", (300.0, 500.0))
        
        # Test with equals
        assert parse_benchmark_value("60 %") == ("=", 0.6)
        assert parse_benchmark_value("80 %") == ("=", 0.8)
        
        # Test with other operators
        assert parse_benchmark_value("≥ 70 %") == ("≥", 0.7)
        assert parse_benchmark_value("≤ 3 %") == ("≤", 0.03)
    
    def test_is_value_in_band(self):
        """Test determining if a value is within a benchmark band."""
        # Test with less than
        assert is_value_in_band(0.9, "< 95 %") is True
        assert is_value_in_band(0.96, "< 95 %") is False
        
        # Test with greater than
        assert is_value_in_band(1.1, "> 105 %") is True
        assert is_value_in_band(1.04, "> 105 %") is False
        
        # Test with ranges
        assert is_value_in_band(1.0, "99 - 103 %") is True
        assert is_value_in_band(0.98, "99 - 103 %") is False
        assert is_value_in_band(1.04, "99 - 103 %") is False
        
        # Test with equals
        assert is_value_in_band(0.6, "60 %") is True
        assert is_value_in_band(0.59, "60 %") is False
    
    def test_determine_kpi_band(self):
        """Test determining which performance band a KPI value falls into."""
        # Sample benchmarks
        collection_benchmarks = {
            "low": "< 95 %",
            "target": "99 – 103 %",
            "stretch": "> 105 %"
        }
        
        writeoff_benchmarks = {
            "low": "> 5 %",
            "target": "< 3 %",
            "stretch": "< 2 %"
        }
        
        # Test Collection % - higher is better
        assert determine_kpi_band(0.94, collection_benchmarks) == "low"
        assert determine_kpi_band(1.0, collection_benchmarks) == "target"
        assert determine_kpi_band(1.06, collection_benchmarks) == "stretch"
        
        # Edge cases for Collection %
        assert determine_kpi_band(0.97, collection_benchmarks) == "low"  # Between low and target
        assert determine_kpi_band(1.04, collection_benchmarks) == "stretch"  # Between target and stretch
        
        # Test Write-offs % - lower is better
        assert determine_kpi_band(0.06, writeoff_benchmarks) == "low"
        assert determine_kpi_band(0.025, writeoff_benchmarks) == "target"
        assert determine_kpi_band(0.015, writeoff_benchmarks) == "stretch"
    
    def test_load_benchmarks(self):
        """Test loading benchmarks from a DataFrame."""
        # Create a sample benchmark DataFrame
        data = {
            "KPI": ["Collection %", "Case-Acceptance %"],
            "Low": ["< 95 %", "< 50 %"],
            "Target": ["99 - 103 %", "60 %"],
            "Stretch": ["> 105 %", "≥ 70 %"]
        }
        benchmark_df = pd.DataFrame(data)
        
        # Load benchmarks
        benchmarks = load_benchmarks(benchmark_df)
        
        # Verify contents
        assert "Collection %" in benchmarks
        assert "Case-Acceptance %" in benchmarks
        assert benchmarks["Collection %"]["low"] == "< 95 %"
        assert benchmarks["Collection %"]["target"] == "99 - 103 %"
        assert benchmarks["Collection %"]["stretch"] == "> 105 %"
        assert benchmarks["Case-Acceptance %"]["low"] == "< 50 %"
        assert benchmarks["Case-Acceptance %"]["target"] == "60 %"
        assert benchmarks["Case-Acceptance %"]["stretch"] == "≥ 70 %"
        
        # Test with None
        default_benchmarks = load_benchmarks(None)
        assert "Collection %" in default_benchmarks
        assert "Write-offs %" in default_benchmarks
    
    def test_calculate_variance(self):
        """Test calculating variance between a value and its target."""
        # Test with positive variance
        variance_pct, flag = calculate_variance(120, 100)
        assert pytest.approx(variance_pct) == 0.2
        assert flag == "positive"
        
        # Test with significant positive variance
        variance_pct, flag = calculate_variance(150, 100)
        assert pytest.approx(variance_pct) == 0.5
        assert flag == "significant_positive"
        
        # Test with negative variance
        variance_pct, flag = calculate_variance(90, 100)
        assert pytest.approx(variance_pct) == -0.1
        assert flag == "negative"
        
        # Test with significant negative variance
        variance_pct, flag = calculate_variance(70, 100)
        assert pytest.approx(variance_pct) == -0.3
        assert flag == "significant_negative"
        
        # Test with neutral variance
        variance_pct, flag = calculate_variance(100, 100)
        assert pytest.approx(variance_pct) == 0.0
        assert flag == "neutral"
        
        # Test with zero target
        variance_pct, flag = calculate_variance(100, 0)
        assert pytest.approx(variance_pct) == 0.0
        assert flag == "neutral"
    
    def test_analyze_kpi_metrics(self):
        """Test analyzing KPI metrics with benchmarks."""
        # Create a sample KPI DataFrame
        data = {
            "Date": ["2023-01-01", "2023-01-01", "2023-01-01"],
            "Location": ["Downtown Office", "Downtown Office", "Downtown Office"],
            "MetricName": ["Collection %", "Case-Acceptance %", "Write-offs %"],
            "Value": [0.94, 0.65, 0.04],
            "Target": [1.0, 0.6, 0.03]
        }
        metrics_df = pd.DataFrame(data)
        
        # Create a sample benchmark DataFrame
        benchmark_data = {
            "KPI": ["Collection %", "Case-Acceptance %", "Write-offs %"],
            "Low": ["< 95 %", "< 50 %", "> 5 %"],
            "Target": ["99 - 103 %", "60 %", "< 3 %"],
            "Stretch": ["> 105 %", "≥ 70 %", "< 2 %"]
        }
        benchmark_df = pd.DataFrame(benchmark_data)
        
        # Analyze metrics
        results = analyze_kpi_metrics(metrics_df, benchmark_df, seed=42)
        
        # Verify results
        assert len(results["metrics"]) == 3
        assert results["summary"]["total_metrics"] == 3
        
        # With our improved metric band classification:
        # - Collection % (0.94) is below target (99 - 103%) - should be "low"
        # - Case-Acceptance % (0.65) is above target (60%) - should be "stretch"
        # - Write-offs % (0.04) is better than low (> 5%) but not in stretch (< 2%) - should be "target"
        assert results["summary"]["metrics_below_target"] == 1  # Collection %
        assert results["summary"]["metrics_at_target"] == 1     # Write-offs %
        assert results["summary"]["metrics_above_target"] == 1  # Case-Acceptance %
        
        # Check for specific metrics
        collection = next(m for m in results["metrics"] if m["name"] == "Collection %")
        assert collection["band"] == "low"
        assert collection["variance_flag"] == "negative"
        
        case_acceptance = next(m for m in results["metrics"] if m["name"] == "Case-Acceptance %")
        assert case_acceptance["band"] == "stretch"
        assert case_acceptance["variance_flag"] == "positive"
        
        writeoffs = next(m for m in results["metrics"] if m["name"] == "Write-offs %")
        assert writeoffs["band"] == "target"
        assert writeoffs["variance_flag"] in ["negative", "neutral", "positive"]
        
        # Check flags
        assert "collection_%_low" in results["flags"]
        assert any(flag for flag in results["flags"] if "case-acceptance" in flag and "opportunity" in flag)
    
    def test_sanitize_dataframe(self):
        """Test sanitizing a DataFrame for upload."""
        # Create a sample DataFrame with various issues
        data = {
            "Date": ["2023-01-01", None, "invalid"],
            "Location": ["Downtown Office", "Uptown Office", None],
            "MetricName": ["Collection %", "Case-Acceptance %", "Write-offs %"],
            "Value": [0.94, "invalid", None],
            "Target": [1.0, 0.6, None]
        }
        df = pd.DataFrame(data)
        
        # Sanitize the DataFrame
        sanitized_df = sanitize_dataframe(df)
        
        # Verify column names are cleaned
        assert all(isinstance(col, str) for col in sanitized_df.columns)
        
        # Verify missing values are handled
        assert sanitized_df.isnull().sum().sum() == 0
        
        # Verify numeric columns are numeric
        assert pd.api.types.is_numeric_dtype(sanitized_df["Value"])
        assert pd.api.types.is_numeric_dtype(sanitized_df["Target"])
        
        # Verify dates are formatted
        assert sanitized_df["Date"].iloc[0] == "2023-01-01" 