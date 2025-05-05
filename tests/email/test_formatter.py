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
    format_kpi_symbol,
    get_status_formatting,
    format_kpi_value,
    get_kpi_prefix,
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
        
        # Test new statuses
        critical_format = get_status_formatting("critical")
        assert critical_format["prefix"] == "🔥 "
        assert critical_format["priority"] == 0
        
        info_format = get_status_formatting("info")
        assert info_format["prefix"] == "ℹ️ "
        assert info_format["priority"] == 4

        # Test unknown status
        unknown_format = get_status_formatting("unknown")
        assert unknown_format["prefix"] == ""
        assert unknown_format["priority"] == 3

        # Test case insensitivity
        mixed_case_format = get_status_formatting("LoW")
        assert mixed_case_format["prefix"] == "⚠️ "
        
        # Test None status
        none_format = get_status_formatting(None)
        assert none_format["prefix"] == ""
        assert none_format["priority"] == 3

    def test_format_kpi_symbol(self):
        """Test getting symbols for different KPI statuses and formats."""
        # Test different format types for "low" status
        assert format_kpi_symbol("low", "symbol") == "⚠️"
        assert format_kpi_symbol("low", "html_entity") == "&#9888;&#65039;"
        assert format_kpi_symbol("low", "fallback") == "(!)"
        assert format_kpi_symbol("low", "prefix") == "⚠️ "
        
        # Test different statuses with symbol format
        assert format_kpi_symbol("target", "symbol") == "✓"
        assert format_kpi_symbol("high", "symbol") == "🎯"
        assert format_kpi_symbol("stretch", "symbol") == "🚀"
        assert format_kpi_symbol("unknown", "symbol") == ""
        
        # Test different statuses with fallback format
        assert format_kpi_symbol("target", "fallback") == "(✓)"
        assert format_kpi_symbol("high", "fallback") == "(+)"
        assert format_kpi_symbol("stretch", "fallback") == "(++)"
        
        # Test invalid format type
        assert format_kpi_symbol("low", "invalid_format") == ""
        
    def test_format_kpi_value(self):
        """Test formatting KPI values with different output formats."""
        # Test markdown format
        assert format_kpi_value("94%", "markdown") == "**94%**"
        assert format_kpi_value(94, "markdown") == "**94**"
        assert format_kpi_value(None, "markdown") == "N/A"
        
        # Test HTML format
        assert format_kpi_value("94%", "html") == "<strong>94%</strong>"
        assert format_kpi_value("<script>alert('XSS')</script>", "html") == "<strong>&lt;script&gt;alert('XSS')&lt;/script&gt;</strong>"
        assert format_kpi_value(None, "html") == "N/A"
        
        # Test plaintext format
        assert format_kpi_value("94%", "plaintext") == "94%"
        assert format_kpi_value(94, "plaintext") == "94"
        assert format_kpi_value(None, "plaintext") == "N/A"
        
    def test_get_kpi_prefix(self):
        """Test getting KPI prefixes for different statuses and output formats."""
        # Test markdown format
        assert get_kpi_prefix("low", "markdown") == "⚠️ "
        assert get_kpi_prefix("target", "markdown") == ""
        assert get_kpi_prefix("high", "markdown") == "🎯 "
        assert get_kpi_prefix("critical", "markdown") == "🔥 "
        assert get_kpi_prefix("info", "markdown") == "ℹ️ "
        assert get_kpi_prefix("unknown", "markdown") == ""
        assert get_kpi_prefix(None, "markdown") == ""
        
        # Test HTML format
        assert get_kpi_prefix("low", "html") == "&#9888;&#65039; "
        assert get_kpi_prefix("target", "html") == ""
        assert get_kpi_prefix("high", "html") == "&#127919; "
        assert get_kpi_prefix("critical", "html") == "&#128293; "
        
        # Test plaintext format
        assert get_kpi_prefix("low", "plaintext") == "(!)" + " "
        assert get_kpi_prefix("target", "plaintext") == "(✓)" + " "
        assert get_kpi_prefix("high", "plaintext") == "(+)" + " "
        assert get_kpi_prefix("critical", "plaintext") == "(!!) " + " "

    def test_format_kpi_entry(self):
        """Test formatting a KPI entry for the email."""
        # Test low status KPI with markdown format
        low_kpi = {
            "name": "Collection %",
            "value": "94%",
            "target": "99%",
            "status": "low"
        }
        low_entry = format_kpi_entry(low_kpi, "markdown")
        assert "⚠️ **Collection %**" in low_entry
        assert "**94%**" in low_entry
        assert "**99%**" in low_entry

        # Test high status KPI with markdown format
        high_kpi = {
            "name": "Case-Acceptance %",
            "value": "65%",
            "target": "60%",
            "status": "high"
        }
        high_entry = format_kpi_entry(high_kpi, "markdown")
        assert "🎯 **Case-Acceptance %**" in high_entry
        assert "**65%**" in high_entry
        assert "**60%**" in high_entry

        # Test KPI with insight in markdown format
        insight_kpi = {
            "name": "Production $/Hr",
            "value": "300",
            "target": "350",
            "status": "target",
            "insight": "Trending upward over last quarter"
        }
        insight_entry = format_kpi_entry(insight_kpi, "markdown")
        assert "**Production $/Hr**" in insight_entry
        assert "**300**" in insight_entry
        assert "**350**" in insight_entry
        assert "* Trending upward over last quarter" in insight_entry
        
        # Test critical status KPI
        critical_kpi = {
            "name": "Collection %",
            "value": "85%",
            "target": "99%",
            "status": "critical"
        }
        critical_entry = format_kpi_entry(critical_kpi, "markdown")
        assert "🔥 **Collection %**" in critical_entry
        
        # Test info status KPI
        info_kpi = {
            "name": "New Metric",
            "value": "10",
            "target": "N/A",
            "status": "info"
        }
        info_entry = format_kpi_entry(info_kpi, "markdown")
        assert "ℹ️ **New Metric**" in info_entry
        
        # Test KPI with missing status
        missing_status_kpi = {
            "name": "Metric X",
            "value": "100",
            "target": "100"
        }
        missing_status_entry = format_kpi_entry(missing_status_kpi, "markdown")
        assert "**Metric X**" in missing_status_entry
        assert "**100**" in missing_status_entry

    def test_format_kpi_entry_plaintext(self):
        """Test formatting a KPI entry for the email in plaintext format."""
        # Test low status KPI with plaintext format
        low_kpi = {
            "name": "Collection %",
            "value": "94%",
            "target": "99%",
            "status": "low"
        }
        low_entry = format_kpi_entry(low_kpi, "plaintext")
        assert "(!) Collection %" in low_entry
        assert "94%" in low_entry
        assert "99%" in low_entry
        
        # Test high status KPI with plaintext format
        high_kpi = {
            "name": "Case-Acceptance %",
            "value": "65%",
            "target": "60%",
            "status": "high"
        }
        high_entry = format_kpi_entry(high_kpi, "plaintext")
        assert "(+) Case-Acceptance %" in high_entry
        assert "65%" in high_entry
        assert "60%" in high_entry
        
        # Test critical status KPI
        critical_kpi = {
            "name": "Collection %",
            "value": "85%",
            "target": "99%",
            "status": "critical"
        }
        critical_entry = format_kpi_entry(critical_kpi, "plaintext")
        assert "(!!) Collection %" in critical_entry

    def test_format_kpi_entry_html(self):
        """Test formatting a KPI entry for the email in HTML format."""
        # Test low status KPI with HTML format
        low_kpi = {
            "name": "Collection %",
            "value": "94%",
            "target": "99%",
            "status": "low"
        }
        low_entry = format_kpi_entry(low_kpi, "html")
        assert "&#9888;&#65039; <strong style='color: yellow'>Collection %</strong>" in low_entry
        assert "<strong>94%</strong>" in low_entry
        assert "<strong>99%</strong>" in low_entry
        
        # Test with HTML special characters in name
        html_kpi = {
            "name": "<script>alert('XSS')</script>",
            "value": "100%",
            "target": "100%",
            "status": "target"
        }
        html_entry = format_kpi_entry(html_kpi, "html")
        assert "&lt;script&gt;alert('XSS')&lt;/script&gt;" in html_entry
        assert "<strong>100%</strong>" in html_entry
        
        # Test with HTML special characters in insight
        insight_html_kpi = {
            "name": "Production $/Hr",
            "value": "300",
            "target": "350",
            "status": "target",
            "insight": "<script>alert('XSS')</script>"
        }
        insight_html_entry = format_kpi_entry(insight_html_kpi, "html")
        assert "&lt;script&gt;alert('XSS')&lt;/script&gt;" in insight_html_entry
        
    def test_format_kpi_entry_with_edge_cases(self):
        """Test formatting KPI entries with edge cases."""
        # Test with None values
        none_value_kpi = {
            "name": "Missing Data",
            "value": None,
            "target": None,
            "status": "low"
        }
        none_entry = format_kpi_entry(none_value_kpi, "markdown")
        assert "⚠️ **Missing Data**" in none_entry
        assert "N/A" in none_entry
        
        # Test with empty name
        empty_name_kpi = {
            "name": "",
            "value": "100",
            "target": "100",
            "status": "target"
        }
        empty_name_entry = format_kpi_entry(empty_name_kpi, "markdown")
        assert "****" in empty_name_entry  # Empty name with bold markers
        
        # Test with missing name (should use 'Unknown Metric')
        missing_name_kpi = {
            "value": "100",
            "target": "100",
            "status": "target"
        }
        missing_name_entry = format_kpi_entry(missing_name_kpi, "markdown")
        assert "**Unknown Metric**" in missing_name_entry

    def test_count_words(self):
        """Test counting words in text."""
        assert count_words("This is a test.") == 4
        assert count_words("One") == 1
        assert count_words("") == 0
        assert count_words("   ") == 0
        assert count_words("Word with    multiple    spaces") == 4

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
        assert trim_content(all_content, sections, 10) == "# Title\n\nHigh priority content\n\n---\n*Note: This email has been condensed. Full report available in dashboard.*"

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

    def test_format_email_markdown_with_different_output_formats(self):
        """Test formatting email in different output formats."""
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

        # Test plaintext output
        plaintext = format_email_markdown(parsed_data, output_format="plaintext")
        assert "# April 2023 KPI Analysis" in plaintext
        assert "(!) Collection %" in plaintext
        assert "(+) Case-Acceptance %" in plaintext
        assert "94%" in plaintext
        assert "99%" in plaintext
        
        # Test HTML output
        html_output = format_email_markdown(parsed_data, output_format="html")
        assert "# April 2023 KPI Analysis" in html_output
        assert "&#9888;&#65039; <strong style='color: yellow'>Collection %</strong>" in html_output
        assert "&#127919; <strong style='color: green'>Case-Acceptance %</strong>" in html_output
        assert "<strong>94%</strong>" in html_output
        assert "<strong>99%</strong>" in html_output
        assert "<hr><em>Generated by Dental Analytics Email Assistant</em>" in html_output

    def test_format_email_markdown_with_word_limit(self):
        """Test formatting with word limit enforcement."""
        # Sample parsed data with lots of recommendations (to exceed word limit)
        parsed_data = {
            "subject": "April 2023 KPI Analysis",
            "summary": "Overall performance is mixed with several areas of improvement identified.",
            "kpi_analysis": [
                {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"},
                {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high"},
                {"name": "Production $/Hr", "value": "300", "target": "350", "status": "target"},
                {"name": "Hygiene Re-appt %", "value": "65%", "target": "80%", "status": "low"}
            ],
            "recommendations": [
                "Focus on collections process by reviewing outstanding claims weekly",
                "Continue case presentation approach with emphasis on patient education",
                "Implement automated appointment reminders to reduce no-shows",
                "Develop a hygiene reactivation campaign for patients overdue > 6 months",
                "Review fee schedule and consider selective fee increases of 2-3%",
                "Evaluate team efficiency with time-motion studies in weak areas",
                "Consider implementing a referral incentive program for existing patients"
            ]
        }

        # Test with a very restrictive word limit
        markdown = format_email_markdown(parsed_data, max_words=100)
        
        # Check that low-band KPIs are still included despite the trimming
        assert "⚠️ **Collection %**" in markdown
        assert "⚠️ **Hygiene Re-appt %**" in markdown
        
        # Ensure we have a note about condensed content
        assert "This email has been condensed" in markdown
        
        # Verify word count is within limit
        assert count_words(markdown) <= 100

    def test_format_response_end_to_end(self):
        """Test the complete format_response function."""
        # Sample response with markdown formatting
        response = """
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
        
        # Test default markdown output
        markdown = format_response(response)
        assert "⚠️ **Collection %**" in markdown
        assert "🎯 **Case-Acceptance %**" in markdown
        
        # Test plaintext output
        plaintext = format_response(response, output_format="plaintext")
        assert "(!) Collection %" in plaintext
        assert "(+) Case-Acceptance %" in plaintext
        
        # Test HTML output
        html_output = format_response(response, output_format="html")
        assert "&#9888;&#65039;" in html_output
        assert "&#127919;" in html_output
        assert "<strong style='color: yellow'>Collection %</strong>" in html_output
        assert "<strong style='color: green'>Case-Acceptance %</strong>" in html_output

    def test_html_escaping_in_output(self):
        """Test HTML entities are properly escaped in HTML output."""
        # Sample data with special characters that need escaping
        parsed_data = {
            "subject": "Q2 KPI Analysis & Trends",
            "summary": "Performance has improved in most areas, but some metrics need attention.",
            "kpi_analysis": [
                {"name": "Accounts Receivable > 90 days", "value": "15%", "target": "<10%", "status": "low"},
                {"name": "New Patient Conversion Rate", "value": "65%", "target": "60%", "status": "high"}
            ],
            "recommendations": [
                "Address AR >90 days with targeted follow-up",
                "Consider expanding successful marketing channels"
            ]
        }
        
        # Test HTML output with special characters
        html_output = format_email_markdown(parsed_data, output_format="html")
        
        # Check that special characters are properly escaped
        assert "Q2 KPI Analysis &amp; Trends" in html_output
        assert "Accounts Receivable &gt; 90 days" in html_output
        assert "<strong>&lt;10%</strong>" in html_output
        assert "AR &gt;90 days" in html_output 