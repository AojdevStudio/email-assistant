"""
CLI command for generating dental KPI analysis emails.
"""
import sys
import json
from pathlib import Path
import argparse
from typing import Dict, Any, Optional, Union

from src.data.analyzer import analyze_kpi_data
from src.data.loader import load_kpi_data
from src.email.generator import EmailGenerator
from src.utils.logging import get_logger

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
        # Load KPI data
        logger.info(f"Loading KPI data from {args.input}")
        kpi_data = load_kpi_data(args.input)
        
        # Analyze KPI data
        logger.info("Analyzing KPI data")
        analysis_results = analyze_kpi_data(kpi_data)
        
        # Create email generator
        logger.info("Generating email from analysis results")
        email_generator = EmailGenerator()
        
        # Generate email
        email_result = email_generator.generate_email(analysis_results)
        
        # Determine output
        if args.output:
            output_path = Path(args.output)
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the email to the output file
            with open(output_path, 'w', encoding='utf-8') as f:
                if args.format == 'json':
                    json.dump(email_result, f, indent=2)
                else:
                    f.write(email_result['email'])
            
            logger.info(f"Email generated and saved to {args.output}")
            
            # If verbose, print summary
            if args.verbose:
                print(f"Email generated with {email_result['word_count']} words")
                print(f"Subject: {email_result['subject']}")
                print(f"Generated at: {email_result['generated_at']}")
        else:
            # Print to stdout
            if args.format == 'json':
                print(json.dumps(email_result, indent=2))
            else:
                print(email_result['email'])
        
        return 0
    
    except Exception as e:
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