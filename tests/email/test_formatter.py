"""
Tests for the Email Formatter module.
"""
import pytest
import json
from typing import Dict, Any

from src.email.formatter import (
    parse_json_response,
    format_email_markdown,
    format_response,
    format_kpi_entry,
    get_status_formatting,
    count_words,
    trim_content,
    trim_section
)

class TestEmailFormatter:
    """Tests for email formatter functions."""

    def test_parse_json_response_with_triple_backticks(self):
        """Test parsing JSON with triple backticks."""
        # Sample response with triple backticks
        response = """
        Here's the analysis of your data:

        ```json
        {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"},
                {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high"}
            ],
            "recommendations": [
                "Focus on collections process",
                "Continue case presentation approach"
            ]
        }
        ```

        Let me know if you need any clarification.
        """

        parsed = parse_json_response(response)
        assert parsed["subject"] == "April 2023 KPI Analysis"
        assert len(parsed["kpi_analysis"]) == 2
        assert parsed["kpi_analysis"][0]["name"] == "Collection %"
        assert parsed["kpi_analysis"][0]["status"] == "low"

    def test_parse_json_response_with_simple_triple_backticks(self):
        """Test parsing JSON with simple triple backticks (no json label)."""
        # Sample response with triple backticks but no json label
        response = """
        Here's the analysis of your data:

        ```
        {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"}
            ],
            "recommendations": [
                "Focus on collections process"
            ]
        }
        ```
        """

        parsed = parse_json_response(response)
        assert parsed["subject"] == "April 2023 KPI Analysis"
        assert len(parsed["kpi_analysis"]) == 1

    def test_parse_json_response_with_raw_json(self):
        """Test parsing raw JSON without backticks."""
        # Sample response with raw JSON
        response = """
        {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"}
            ],
            "recommendations": [
                "Focus on collections process"
            ]
        }
        """

        parsed = parse_json_response(response)
        assert parsed["subject"] == "April 2023 KPI Analysis"
        assert len(parsed["kpi_analysis"]) == 1

    def test_parse_json_response_with_invalid_json(self):
        """Test parsing invalid JSON raises appropriate error."""
        # Sample response with invalid JSON
        response = """
        Here's the analysis of your data:

        ```json
        {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed,
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"}
            ],
            "recommendations": [
                "Focus on collections process"
            ]
        }
        ```
        """

        with pytest.raises(ValueError) as excinfo:
            parse_json_response(response)
        assert "Failed to parse JSON" in str(excinfo.value)

    def test_get_status_formatting(self):
        """Test getting formatting details for different KPI statuses."""
        # Test known statuses
        low_format = get_status_formatting("low")
        assert low_format["prefix"] == "⚠️ "
        assert low_format["priority"] == 1

        target_format = get_status_formatting("target")
        assert target_format["prefix"] == ""
        assert target_format["priority"] == 3

        high_format = get_status_formatting("high")
        assert high_format["prefix"] == "🎯 "
        assert high_format["priority"] == 2

        stretch_format = get_status_formatting("stretch")
        assert stretch_format["prefix"] == "🚀 "
        assert stretch_format["priority"] == 2

        # Test unknown status
        unknown_format = get_status_formatting("unknown")
        assert unknown_format["prefix"] == ""
        assert unknown_format["priority"] == 3

        # Test case insensitivity
        mixed_case_format = get_status_formatting("LoW")
        assert mixed_case_format["prefix"] == "⚠️ "

    def test_format_kpi_entry(self):
        """Test formatting a KPI entry for the email."""
        # Test low status KPI
        low_kpi = {
            "name": "Collection %",
            "value": "94%",
            "target": "99%",
            "status": "low"
        }
        low_entry = format_kpi_entry(low_kpi)
        assert "⚠️ **Collection %**" in low_entry
        assert "**94%**" in low_entry
        assert "**99%**" in low_entry

        # Test high status KPI
        high_kpi = {
            "name": "Case-Acceptance %",
            "value": "65%",
            "target": "60%",
            "status": "high"
        }
        high_entry = format_kpi_entry(high_kpi)
        assert "🎯 **Case-Acceptance %**" in high_entry
        assert "**65%**" in high_entry
        assert "**60%**" in high_entry

        # Test KPI with insight
        insight_kpi = {
            "name": "Production $/Hr",
            "value": "300",
            "target": "350",
            "status": "target",
            "insight": "Trending upward over last quarter"
        }
        insight_entry = format_kpi_entry(insight_kpi)
        assert "**Production $/Hr**" in insight_entry
        assert "**300**" in insight_entry
        assert "**350**" in insight_entry
        assert "* Trending upward over last quarter" in insight_entry

    def test_count_words(self):
        """Test word counting functionality."""
        assert count_words("") == 0
        assert count_words("Hello") == 1
        assert count_words("Hello world") == 2
        assert count_words("Hello,   world!") == 2
        assert count_words("\n\nHello\nworld\n\n") == 2
        assert count_words("One. Two. Three.") == 3

    def test_trim_section(self):
        """Test trimming a section to meet word limits."""
        # Test bullet list trimming
        bullet_list = "* First item\n* Second item\n* Third item\n* Fourth item"
        assert trim_section(bullet_list, 4) == "* First item\n* Second"
        
        # Test paragraph trimming
        paragraph = "First sentence. Second sentence. Third sentence."
        assert trim_section(paragraph, 2) == "First sentence."
        assert trim_section(paragraph, 4) == "First sentence. Second sentence."

    def test_trim_content(self):
        """Test trimming content based on section priorities."""
        sections = [
            {"content": "# Title", "priority": 1, "position": 0},
            {"content": "Low priority content", "priority": 5, "position": 1},
            {"content": "High priority content", "priority": 2, "position": 2},
            {"content": "Medium priority content", "priority": 3, "position": 3}
        ]
        
        # All content should fit within 10 words
        all_content = "# Title\n\nLow priority content\n\nHigh priority content\n\nMedium priority content"
        assert trim_content(all_content, 10) == "# Title\n\nHigh priority content\n\n---\n*Note: This email has been condensed. Full report available in dashboard.*"

    def test_format_email_markdown_with_valid_data(self):
        """Test formatting valid parsed data into markdown."""
        # Sample parsed data
        parsed_data = {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"},
                {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high"}
            ],
            "recommendations": [
                "Focus on collections process",
                "Continue case presentation approach"
            ]
        }

        markdown = format_email_markdown(parsed_data)
        
        # Check basic formatting
        assert "# April 2023 KPI Analysis" in markdown
        assert "Overall performance is mixed." in markdown
        assert "## Key Performance Metrics" in markdown
        assert "⚠️ **Collection %**" in markdown
        assert "🎯 **Case-Acceptance %**" in markdown
        assert "**94%**" in markdown
        assert "**99%**" in markdown
        assert "## Recommendations" in markdown
        assert "* Focus on collections process" in markdown
        assert "*Generated by Dental Analytics Email Assistant*" in markdown

    def test_format_email_markdown_with_missing_fields(self):
        """Test handling of missing required fields."""
        # Sample parsed data with missing fields
        parsed_data = {
            "subject": "April 2023 KPI Analysis",
            # Missing summary
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"}
            ]
            # Missing recommendations
        }

        with pytest.raises(ValueError) as excinfo:
            format_email_markdown(parsed_data)
        assert "Missing required fields" in str(excinfo.value)
    
    def test_format_email_markdown_with_word_limit(self):
        """Test formatting with word limit enforcement."""
        # Create a large dataset
        parsed_data = {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed with some metrics showing improvement while others are falling behind target. This analysis covers the last quarter's performance across all locations.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low",
                 "insight": "Collections have dropped steadily over the last three months, particularly for accounts over 90 days."},
                {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high",
                 "insight": "Case acceptance has improved significantly since implementing the new presentation protocol."},
                {"name": "Production $/Hr — Doctor", "value": "300", "target": "350", "status": "target",
                 "insight": "Doctor production per hour has remained stable but still below target."},
                {"name": "Production $/Hr — Hygiene", "value": "120", "target": "150", "status": "low",
                 "insight": "Hygiene production is well below target and has been declining."}
            ],
            "recommendations": [
                "Focus on collections process by implementing automated reminders for accounts over 60 days",
                "Continue case presentation approach to maintain high case acceptance rates",
                "Review hygiene appointment scheduling to maximize production per hour",
                "Consider additional hygiene training on presenting treatment recommendations"
            ]
        }
        
        # Format with a tight word limit
        markdown = format_email_markdown(parsed_data, max_words=50)
        
        # Verify that the content has been trimmed
        assert count_words(markdown) <= 50
        # Verify that at least some content is preserved
        assert "April 2023 KPI Analysis" in markdown
        assert "Note: This email has been condensed" in markdown
        # Verify that high priority content is included
        assert "Key Performance Metrics" in markdown
        assert "⚠️" in markdown  # At least one warning symbol is preserved

    def test_format_response_end_to_end(self):
        """Test end-to-end response formatting."""
        # Sample assistant response
        response = """
        Here's the analysis of your data:

        ```json
        {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"},
                {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high"}
            ],
            "recommendations": [
                "Focus on collections process",
                "Continue case presentation approach"
            ]
        }
        ```
        """

        markdown = format_response(response)
        
        # Check the final output
        assert "# April 2023 KPI Analysis" in markdown
        assert "⚠️ **Collection %**" in markdown
        assert "* Focus on collections process" in markdown
        
        # Test with word limit
        short_markdown = format_response(response, max_words=20)
        # The word limit includes the condensed note, so we'll check it's at least shorter
        assert count_words(short_markdown) < count_words(markdown)
        assert "Note: This email has been condensed" in short_markdown 