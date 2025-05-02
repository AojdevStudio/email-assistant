#!/usr/bin/env python3
"""
Dental Email Assistant - Main entry point

This module serves as the entry point for the Dental Analytics Email Assistant application.
It orchestrates the entire workflow:
1. Loading and validating KPI data
2. Sending data to OpenAI for analysis
3. Parsing and formatting the response
4. Generating and outputting the email report
"""

import sys
from pathlib import Path

from src.utils.logging import get_logger
from src.cli import cli

logger = get_logger(__name__)

def main():
    """Main entry point for the application."""
    logger.info("Starting Dental Email Assistant")
    return cli.app()

if __name__ == "__main__":
    sys.exit(main()) 