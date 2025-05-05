"""
Tests for the Email Generator module.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json

from src.email.generator import EmailGenerator
from src.openai.client import OpenAIClient

class TestEmailGenerator:
    """Tests for the EmailGenerator class."""

    @pytest.fixture
    def mock_openai_client(self):
        """Fixture for a mocked OpenAI client."""
        mock_client = MagicMock(spec=OpenAIClient)
        
        # Mock the process_kpi_data method
        mock_response = {
            "content": json.dumps({
                "subject": "April 2023 KPI Analysis",
                "body": "# April 2023 KPI Analysis\n\nOverall performance is mixed with some areas of concern.\n\n## Key Performance Metrics\n\n* Collection %: **94%** vs target **99%**\n* Case-Acceptance %: **65%** vs target **60%**\n\n## Recommendations\n\n* Improve collections process by reviewing outstanding accounts weekly\n* Continue successful case presentation approach",
                "kpi_analysis": [
                    {"name": "Collection %", "value": "94%", "target": "99%", "status": "low"},
                    {"name": "Case-Acceptance %", "value": "65%", "target": "60%", "status": "high"}
                ],
                "recommendations": [
                    "Improve collections process by reviewing outstanding accounts weekly",
                    "Continue successful case presentation approach"
                ]
            }),
            "message_id": "msg_123",
            "created_at": 1619827200
        }
        mock_client.process_kpi_data.return_value = mock_response
        
        return mock_client
    
    @pytest.fixture
    def sample_analysis_results(self):
        """Fixture for sample analysis results."""
        return {
            "summary": {
                "metrics_below_target": 1,
                "metrics_at_target": 0,
                "metrics_above_target": 1
            },
            "flags": ["Collections below target", "High cancellation rate"],
            "data": {
                "Collection %": 94,
                "Case-Acceptance %": 65
            },
            "benchmarks": None
        }
    
    def test_email_generator_initialization(self, mock_openai_client):
        """Test EmailGenerator initialization."""
        # Test with provided client
        generator = EmailGenerator(mock_openai_client)
        assert generator.openai_client is mock_openai_client
        
        # Test without client (should create a new one)
        with patch("src.email.generator.OpenAIClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            
            generator = EmailGenerator()
            assert generator.openai_client is mock_client_instance
    
    def test_generate_email(self, mock_openai_client, sample_analysis_results):
        """Test generating an email from analysis results."""
        generator = EmailGenerator(mock_openai_client)
        
        result = generator.generate_email(sample_analysis_results)
        
        # Check that the OpenAI client was called correctly
        mock_openai_client.process_kpi_data.assert_called_once()
        
        # Check that the result contains expected keys
        assert "email" in result
        assert "subject" in result
        assert "generated_at" in result
        assert "word_count" in result
        assert "raw_response" in result
        assert "analysis_summary" in result
        
        # Check subject is extracted correctly
        assert result["subject"] == "April 2023 KPI Analysis"
        
        # Check that the word count is calculated
        assert isinstance(result["word_count"], int)
        assert result["word_count"] > 0
        
        # Check that the analysis summary is included
        assert result["analysis_summary"] == sample_analysis_results["summary"]
    
    def test_generate_email_with_empty_results(self, mock_openai_client):
        """Test generating an email with empty analysis results."""
        generator = EmailGenerator(mock_openai_client)
        
        with pytest.raises(ValueError) as excinfo:
            generator.generate_email({})
        
        assert "Analysis results cannot be empty" in str(excinfo.value)
    
    def test_generate_email_without_summary(self, mock_openai_client):
        """Test generating an email without a summary section."""
        generator = EmailGenerator(mock_openai_client)
        
        with pytest.raises(ValueError) as excinfo:
            generator.generate_email({"data": {}})
        
        assert "Analysis results must contain a 'summary' section" in str(excinfo.value)
    
    def test_get_email_system_prompt(self, mock_openai_client, sample_analysis_results):
        """Test generating a system prompt from analysis results."""
        generator = EmailGenerator(mock_openai_client)
        
        prompt = generator._get_email_system_prompt(sample_analysis_results)
        
        # Check that the prompt contains key information from the analysis
        assert "1 below target" in prompt
        assert "1 above target" in prompt
        assert "Collections below target, High cancellation rate" in prompt
        
        # Check that the prompt includes required formatting instructions
        assert "executive-focused email" in prompt
        assert "JSON" in prompt
        assert "subject" in prompt
        assert "body" in prompt
        assert "kpi_analysis" in prompt
        assert "recommendations" in prompt
    
    def test_process_with_openai_exception(self, mock_openai_client, sample_analysis_results):
        """Test handling exceptions from the OpenAI client."""
        generator = EmailGenerator(mock_openai_client)
        
        # Mock the process_kpi_data method to raise an exception
        mock_openai_client.process_kpi_data.side_effect = Exception("API error")
        
        with pytest.raises(ValueError) as excinfo:
            generator._process_with_openai(sample_analysis_results)
        
        assert "Error processing with OpenAI: API error" in str(excinfo.value)
    
    def test_count_words(self, mock_openai_client):
        """Test word counting functionality."""
        generator = EmailGenerator(mock_openai_client)
        
        assert generator._count_words("") == 0
        assert generator._count_words("Hello") == 1
        assert generator._count_words("Hello world") == 2
        assert generator._count_words("Hello,   world!") == 2
        assert generator._count_words("\n\nHello\nworld\n\n") == 2 