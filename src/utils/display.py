"""
Display utilities for rendering output in the terminal.

This module provides functions for displaying formatted analysis results,
emails, and KPI data in the terminal using Rich.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text

# Initialize Rich console
console = Console()

def display_analysis_summary(analysis_results: Dict[str, Any]) -> None:
    """
    Display a summary of the KPI analysis results.
    
    Args:
        analysis_results: Dictionary containing the analysis results
    """
    summary = analysis_results.get("summary", {})
    
    # Create a panel with the analysis summary
    console.print(
        Panel.fit(
            f"Analysis complete:\n"
            f"Metrics below target: [bold red]{summary.get('metrics_below_target', 0)}[/bold red]\n"
            f"Metrics at target: [bold yellow]{summary.get('metrics_at_target', 0)}[/bold yellow]\n" 
            f"Metrics above target: [bold green]{summary.get('metrics_above_target', 0)}[/bold green]\n",
            title="Analysis Results",
            border_style="green",
        )
    )

def display_email(email_data: Dict[str, Any]) -> None:
    """
    Display the generated email in the terminal.
    
    Args:
        email_data: Dictionary containing the email data
    """
    # Create a panel with the email subject
    console.print(
        Panel.fit(
            f"[bold]{email_data.get('subject', 'Dental KPI Analysis')}[/bold]",
            title="Email Subject",
            border_style="blue",
        )
    )
    
    # Display the email content as markdown
    console.print(
        Panel.fit(
            Markdown(email_data.get("email", "")),
            title="Email Content",
            border_style="blue",
        )
    )
    
    # Display metadata
    console.print(
        f"Word count: [bold]{email_data.get('word_count', 0)}[/bold] | "
        f"Generated at: {email_data.get('generated_at', datetime.now().isoformat())}"
    )

def display_kpi_table(kpi_data: List[Dict[str, Any]], title: str = "KPI Analysis") -> None:
    """
    Display a table of KPI data with color-coded status.
    
    Args:
        kpi_data: List of KPI data dictionaries
        title: Title for the table
    """
    if not kpi_data:
        console.print("[yellow]No KPI data to display[/yellow]")
        return
    
    # Create a table for KPIs
    table = Table(title=title)
    table.add_column("KPI Name", style="cyan")
    table.add_column("Current Value", style="white")
    table.add_column("Target Value", style="white")
    table.add_column("Status", style="white")
    table.add_column("Insight", style="white")
    
    # Add rows to the table
    for kpi in kpi_data:
        status = kpi.get("status", "")
        status_style = get_status_style(status)
        
        table.add_row(
            kpi.get("name", ""),
            kpi.get("value", ""),
            kpi.get("target", ""),
            Text(status, style=status_style),
            kpi.get("insight", "")
        )
    
    console.print(table)

def display_welcome_message(file_path: str) -> None:
    """
    Display a welcome message with the file path.
    
    Args:
        file_path: Path to the input file
    """
    console.print(
        Panel.fit(
            f"[bold green]Dental Email Assistant[/bold green]\n"
            f"Processing KPI data from: [bold]{file_path}[/bold]",
            title="Welcome",
            border_style="blue",
        )
    )

def get_status_style(status: str) -> str:
    """
    Get the appropriate style for a KPI status.
    
    Args:
        status: Status string ('low', 'target', 'high', etc.)
        
    Returns:
        Style string for Rich
    """
    status = status.lower() if status else ""
    
    if status in ["low", "below", "behind"]:
        return "bold red"
    elif status in ["target", "on target", "on-target"]:
        return "bold yellow"
    elif status in ["high", "above", "ahead"]:
        return "bold green"
    else:
        return "white"

def display_error(message: str) -> None:
    """
    Display an error message.
    
    Args:
        message: Error message to display
    """
    console.print(f"[bold red]Error:[/bold red] {message}")

def display_success(message: str) -> None:
    """
    Display a success message.
    
    Args:
        message: Success message to display
    """
    console.print(f"[bold green]Success:[/bold green] {message}") 