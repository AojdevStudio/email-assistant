"""
Tests for the output display and file saving functionality.
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
from unittest.mock import patch, MagicMock

from src.utils.file_output import ensure_output_directory, save_email, save_analysis_results
from src.utils.display import (
    get_status_style,
    display_email,
    display_analysis_summary,
    display_kpi_table
)

# Sample data for testing
SAMPLE_EMAIL_DATA = {
    "subject": "Dental KPI Analysis - Test",
    "email": "# Dental KPI Analysis\n\nThis is a test email.\n\n## Key Findings\n\n* Finding 1\n* Finding 2\n",
    "word_count": 15,
    "generated_at": "2023-01-01T12:00:00",
    "kpi_analysis": [
        {
            "name": "New Patient Count",
            "value": "25",
            "target": "30",
            "status": "low",
            "insight": "Below target by 5 patients"
        },
        {
            "name": "Revenue",
            "value": "$10,000",
            "target": "$8,000",
            "status": "high",
            "insight": "Above target by $2,000"
        }
    ]
}

SAMPLE_ANALYSIS_RESULTS = {
    "summary": {
        "metrics_below_target": 3,
        "metrics_at_target": 2,
        "metrics_above_target": 5
    },
    "data": {
        "practice_name": "Test Practice",
        "date_range": "Jan 1 - Jan 31, 2023"
    }
}


class TestFileOutput:
    """Tests for the file output functionality."""
    
    def test_ensure_output_directory(self):
        """Test ensuring an output directory exists."""
        with tempfile.TemporaryDirectory() as tempdir:
            test_dir = Path(tempdir) / "test_output"
            assert not test_dir.exists()
            
            # Call function to create directory
            result = ensure_output_directory(test_dir)
            
            assert test_dir.exists()
            assert test_dir.is_dir()
            assert result == test_dir
    
    def test_save_email(self):
        """Test saving email data to files."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Save email data
            timestamp = "20230101_120000"
            saved_files = save_email(
                email_data=SAMPLE_EMAIL_DATA,
                output_dir=tempdir,
                timestamp=timestamp,
                save_json=True,
                save_markdown=True
            )
            
            # Check JSON file
            json_path = Path(tempdir) / f"{timestamp}_report.json"
            assert json_path.exists()
            assert json_path == saved_files['json']
            
            # Check content of JSON file
            with open(json_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
                assert json_content['subject'] == SAMPLE_EMAIL_DATA['subject']
            
            # Check Markdown file
            md_path = Path(tempdir) / f"{timestamp}_email.md"
            assert md_path.exists()
            assert md_path == saved_files['markdown']
            
            # Check content of Markdown file
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                assert md_content == SAMPLE_EMAIL_DATA['email']
    
    def test_save_analysis_results(self):
        """Test saving analysis results to a file."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Save analysis results
            timestamp = "20230101_120000"
            saved_file = save_analysis_results(
                analysis_results=SAMPLE_ANALYSIS_RESULTS,
                output_dir=tempdir,
                timestamp=timestamp
            )
            
            # Check file exists
            json_path = Path(tempdir) / f"{timestamp}_analysis.json"
            assert json_path.exists()
            assert json_path == saved_file
            
            # Check content of file
            with open(json_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
                assert json_content['summary'] == SAMPLE_ANALYSIS_RESULTS['summary']


class TestDisplay:
    """Tests for the display functionality."""
    
    def test_get_status_style(self):
        """Test getting the style for a status."""
        assert get_status_style("low") == "bold red"
        assert get_status_style("target") == "bold yellow"
        assert get_status_style("high") == "bold green"
        assert get_status_style("unknown") == "white"
        assert get_status_style("") == "white"
    
    @patch('src.utils.display.console')
    def test_display_email(self, mock_console):
        """Test displaying an email."""
        display_email(SAMPLE_EMAIL_DATA)
        # Verify console.print was called at least 3 times (subject, body, metadata)
        assert mock_console.print.call_count >= 3
    
    @patch('src.utils.display.console')
    def test_display_analysis_summary(self, mock_console):
        """Test displaying an analysis summary."""
        display_analysis_summary(SAMPLE_ANALYSIS_RESULTS)
        # Verify console.print was called at least once
        assert mock_console.print.call_count >= 1
    
    @patch('src.utils.display.console')
    def test_display_kpi_table(self, mock_console):
        """Test displaying a KPI table."""
        display_kpi_table(SAMPLE_EMAIL_DATA["kpi_analysis"])
        # Verify console.print was called at least once
        assert mock_console.print.call_count >= 1
    
    @patch('src.utils.display.console')
    def test_display_kpi_table_empty(self, mock_console):
        """Test displaying an empty KPI table."""
        display_kpi_table([])
        # Verify console.print was called once with a warning message
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "No KPI data" in args 