"""
CLI command for generating dental KPI analysis emails.
"""
import sys
import json
from pathlib import Path
import argparse
from typing import Dict, Any, Optional, Union
from datetime import datetime

from src.data.analyzer import analyze_kpi_data
from src.data.loader import load_kpi_data
from src.email.generator import EmailGenerator
from src.utils.logging import get_logger
from src.utils.display import display_email, display_welcome_message, display_analysis_summary, display_kpi_table, display_success, display_error
from src.utils.file_output import save_email, ensure_output_directory

# Initialize logger
logger = get_logger(__name__)

def generate_email_command(args: argparse.Namespace) -> int:
    """
    Generate an executive email from KPI data using OpenAI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Display welcome message
        display_welcome_message(args.input)
        
        # Load KPI data
        logger.info(f"Loading KPI data from {args.input}")
        kpi_data = load_kpi_data(args.input)
        
        # Analyze KPI data
        logger.info("Analyzing KPI data")
        analysis_results = analyze_kpi_data(kpi_data)
        
        # Display analysis summary
        display_analysis_summary(analysis_results)
        
        # Create email generator
        logger.info("Generating email from analysis results")
        email_generator = EmailGenerator()
        
        # Generate email
        email_result = email_generator.generate_email(analysis_results)
        
        # Display email
        display_email(email_result)
        
        # Display KPI table if available
        if "kpi_analysis" in email_result and isinstance(email_result["kpi_analysis"], list):
            display_kpi_table(email_result["kpi_analysis"], "KPI Analysis")
        
        # Save files if requested
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = args.output_dir if hasattr(args, "output_dir") else "./output"
            
            try:
                saved_files = save_email(
                    email_data=email_result,
                    output_dir=output_dir,
                    timestamp=timestamp,
                    save_json=True,
                    save_markdown=True
                )
                
                # Display success message with saved file paths
                for file_type, file_path in saved_files.items():
                    display_success(f"{file_type.capitalize()} file saved to: {file_path}")
                    
            except Exception as e:
                display_error(f"Failed to save output files: {str(e)}")
                logger.error(f"Error saving files: {str(e)}")
        
        return 0
    
    except Exception as e:
        display_error(str(e))
        logger.error(f"Error generating email: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def setup_email_parser(subparsers):
    """
    Set up the email command parser.
    
    Args:
        subparsers: Subparsers object from argparse
    """
    email_parser = subparsers.add_parser(
        'email',
        help='Generate executive email from KPI data'
    )
    
    email_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to the KPI data CSV file'
    )
    
    email_parser.add_argument(
        '-o', '--output',
        help='Path to save the generated email (defaults to stdout)'
    )
    
    email_parser.add_argument(
        '--output-dir',
        default='./output',
        help='Directory to save output files when using --save (default: ./output)'
    )
    
    email_parser.add_argument(
        '-s', '--save',
        action='store_true',
        help='Save the generated email and report to the output directory'
    )
    
    email_parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='Output format (markdown or complete JSON response)'
    )
    
    email_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    email_parser.set_defaults(func=generate_email_command) 