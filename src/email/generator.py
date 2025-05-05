"""
Email Generation Module

This module provides functionality to generate executive emails
from the OpenAI Assistant's response, using the KPI analysis results.
"""

from typing import Dict, Any, Optional, List, Union
import time
from datetime import datetime

from src.email.formatter import format_response, parse_json_response
from src.openai.client import OpenAIClient
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

class EmailGenerator:
    """
    A class for generating executive emails based on dental KPI analysis.
    """
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Initialize the email generator.
        
        Args:
            openai_client: Optional OpenAI client instance. If not provided,
                          a new client will be created.
        """
        self.openai_client = openai_client or OpenAIClient()
        logger.info("Email generator initialized")
    
    def generate_email(
        self,
        analysis_results: Dict[str, Any],
        max_words: int = 350,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Generate an executive email from KPI analysis results.
        
        Args:
            analysis_results: Dictionary containing the KPI analysis results
            max_words: Maximum words allowed in the email (default: 350)
            output_format: Output format ('markdown', 'plaintext', or 'html')
            
        Returns:
            A dictionary containing the formatted email and metadata
            
        Raises:
            ValueError: If the analysis results are invalid or the API call fails
        """
        logger.info("Generating email from analysis results")
        
        try:
            # Validate analysis results
            if not analysis_results:
                raise ValueError("Analysis results cannot be empty")
            
            if "summary" not in analysis_results:
                raise ValueError("Analysis results must contain a 'summary' section")
                
            # Send analysis results to OpenAI for email generation
            response = self._process_with_openai(analysis_results)
            
            # Parse and format the response
            parsed_data = parse_json_response(response["content"])
            
            # Format the email according to the specified output format
            formatted_email = format_response(
                response_content=response["content"],
                max_words=max_words,
                output_format=output_format
            )
            
            # Return the email and metadata
            return {
                "email": formatted_email,
                "subject": parsed_data.get("subject", "Dental KPI Analysis"),
                "generated_at": datetime.now().isoformat(),
                "word_count": self._count_words(formatted_email),
                "raw_response": response,
                "analysis_summary": analysis_results.get("summary", {})
            }
            
        except Exception as e:
            error_msg = f"Error generating email: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _process_with_openai(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the analysis results with OpenAI to generate an email draft.
        
        Args:
            analysis_results: Dictionary containing KPI analysis results
            
        Returns:
            The OpenAI Assistant's response
            
        Raises:
            ValueError: If the OpenAI API call fails
        """
        try:
            # Use the OpenAI client's process_kpi_data method
            response = self.openai_client.process_kpi_data(
                df=analysis_results.get("data", {}),
                system_prompt=self._get_email_system_prompt(analysis_results),
                benchmark_df=analysis_results.get("benchmarks", None)
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing with OpenAI: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _get_email_system_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate a system prompt for the OpenAI Assistant based on the analysis results.
        
        Args:
            analysis_results: Dictionary containing KPI analysis results
            
        Returns:
            A system prompt string
        """
        # Extract key metrics for the prompt
        metrics_below = analysis_results.get("summary", {}).get("metrics_below_target", 0)
        metrics_at = analysis_results.get("summary", {}).get("metrics_at_target", 0)
        metrics_above = analysis_results.get("summary", {}).get("metrics_above_target", 0)
        flags = ", ".join(analysis_results.get("flags", []))
        
        # Build a comprehensive system prompt
        prompt = f"""
        You are an executive dental practice analyst. Create a concise, executive-focused email 
        analyzing the KPI data provided. Format your response as valid JSON with the following structure:
        
        {{
            "subject": "Clear, specific email subject line",
            "body": "The main email content in markdown format",
            "kpi_analysis": [
                {{"name": "KPI Name", "value": "Current Value", "target": "Target Value", "status": "low/target/high", "insight": "Brief insight"}}
            ],
            "recommendations": ["1-3 SMART recommendations based on the data"]
        }}
        
        Key requirements:
        - Executive tone: Professional, data-driven, and action-oriented
        - Structure: Clear sections with bullet points for key metrics
        - Length: Maximum 350 words
        - Format: Use markdown with bold for important figures
        - KPIs: Include status ('low' for below target, 'target' for on-target, 'high' for above target)
        - Focus on metrics that need attention (currently {metrics_below} below target, {metrics_at} at target, and {metrics_above} above target)
        - Highlight these key flags: {flags if flags else "none identified"}
        - Include SMART recommendations (Specific, Measurable, Achievable, Relevant, Time-bound)
        
        Your analysis should be insightful but concise, focusing on what an executive needs to know and do.
        """
        
        return prompt.strip()
    
    def _count_words(self, text: str) -> int:
        """
        Count the number of words in a text.
        
        Args:
            text: The text to count words in
            
        Returns:
            The number of words in the text
        """
        return len([word for word in text.split() if word]) 