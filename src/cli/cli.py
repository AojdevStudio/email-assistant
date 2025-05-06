"""
Command Line Interface for the Dental Email Assistant

This module provides the command-line interface for the Dental Email Assistant
application, powered by Typer and Rich.
"""

import sys
from pathlib import Path
from typing import Optional
import argparse
from datetime import datetime

from rich.console import Console

from src.utils.logging import get_logger
from src.email.generator import EmailGenerator
from src.data.loader import load_kpi_data
from src.data.analyzer import analyze_kpi_data
from src.cli.email_command import setup_email_parser
from src.utils.display import (
    display_welcome_message, 
    display_analysis_summary, 
    display_success, 
    display_error
)
from src.utils.file_output import save_analysis_results, ensure_output_directory

# Initialize logger
logger = get_logger(__name__)

# Initialize Rich console
console = Console()

def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Dental Email Assistant - Generate executive summary emails from dental practice KPI data",
    )
    
    subparsers = parser.add_subparsers(
        title="commands", 
        dest="command", 
        help="Command to execute"
    )
    
    # Setup analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", 
        help="Analyze dental practice KPI data"
    )
    analyze_parser.add_argument(
        "-f", "--file", 
        required=True,
        help="Path to the CSV file containing KPI data"
    )
    analyze_parser.add_argument(
        "-s", "--save", 
        action="store_true",
        help="Save the generated analysis to the output directory"
    )
    analyze_parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory for saved files (default: ./output)"
    )
    analyze_parser.set_defaults(func=analyze_command)
    
    # Setup email command
    setup_email_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute the command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 0

def analyze_command(args):
    """
    Command to analyze dental practice KPI data.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Log the start of the analysis
        logger.info(f"Starting analysis of {args.file}")
        
        # Display a welcome message
        display_welcome_message(args.file)
        
        # Load and analyze data
        kpi_data = load_kpi_data(args.file)
        analysis_results = analyze_kpi_data(kpi_data)
        
        # Display analysis summary
        display_analysis_summary(analysis_results)
        
        # Save files if requested
        if args.save:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_file = save_analysis_results(
                    analysis_results=analysis_results,
                    output_dir=args.output,
                    timestamp=timestamp
                )
                display_success(f"Analysis saved to: {saved_file}")
            except Exception as e:
                display_error(f"Failed to save analysis results: {str(e)}")
                logger.error(f"Error saving analysis results: {str(e)}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        display_error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main()) 