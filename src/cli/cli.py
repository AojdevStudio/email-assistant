"""
Command Line Interface for the Dental Email Assistant

This module provides the command-line interface for the Dental Email Assistant
application, powered by Typer and Rich.
"""

import sys
from pathlib import Path
from typing import Optional
import argparse

from rich.console import Console
from rich.panel import Panel

from src.utils.logging import get_logger
from src.email.generator import EmailGenerator
from src.data.loader import load_kpi_data
from src.data.analyzer import analyze_kpi_data
from src.cli.email_command import setup_email_parser

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
        console.print(
            Panel.fit(
                f"[bold green]Dental Email Assistant[/bold green]\n"
                f"Analyzing KPI data from: [bold]{args.file}[/bold]",
                title="Welcome",
                border_style="blue",
            )
        )
        
        # Load and analyze data
        kpi_data = load_kpi_data(args.file)
        analysis_results = analyze_kpi_data(kpi_data)
        
        # Print analysis summary
        console.print(
            Panel.fit(
                f"Analysis complete:\n"
                f"Metrics below target: [bold red]{analysis_results['summary']['metrics_below_target']}[/bold red]\n"
                f"Metrics at target: [bold yellow]{analysis_results['summary']['metrics_at_target']}[/bold yellow]\n" 
                f"Metrics above target: [bold green]{analysis_results['summary']['metrics_above_target']}[/bold green]\n",
                title="Analysis Results",
                border_style="green",
            )
        )
        
        # Save files if requested
        if args.save:
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save analysis as JSON
            analysis_file = output_path / "analysis.json"
            with open(analysis_file, 'w') as f:
                import json
                json.dump(analysis_results, f, indent=2)
            
            console.print(f"Analysis saved to: [bold]{analysis_file}[/bold]")
            
        return 0
    
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 