"""
File output utilities for saving analysis results and email content.

This module provides functions for saving analysis results, emails,
and other output to files in the specified output directory.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Union, Optional
from datetime import datetime

from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

def ensure_output_directory(output_dir: Union[str, Path]) -> Path:
    """
    Ensure the output directory exists, creating it if necessary.
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Path: The Path object for the output directory
    
    Raises:
        PermissionError: If unable to create the directory due to permissions
    """
    output_path = Path(output_dir)
    
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    except PermissionError as e:
        logger.error(f"Permission error creating output directory: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating output directory: {e}")
        raise

def save_email(
    email_data: Dict[str, Any], 
    output_dir: Union[str, Path] = "./output",
    timestamp: Optional[str] = None,
    save_json: bool = True,
    save_markdown: bool = True
) -> Dict[str, Path]:
    """
    Save email data to files in the output directory.
    
    Args:
        email_data: Dictionary containing the email data
        output_dir: Path to the output directory
        timestamp: Optional timestamp to use in filenames (default: current time)
        save_json: Whether to save the complete JSON data
        save_markdown: Whether to save the email content as Markdown
        
    Returns:
        Dictionary with paths to the saved files
    
    Raises:
        PermissionError: If unable to write to the output directory
        OSError: If an I/O error occurs during file writing
    """
    # Ensure the output directory exists
    output_path = ensure_output_directory(output_dir)
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize return dictionary
    saved_files = {}
    
    try:
        # Save JSON if requested
        if save_json:
            json_path = output_path / f"{timestamp}_report.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, indent=2)
            saved_files['json'] = json_path
            logger.info(f"Saved JSON report to {json_path}")
        
        # Save Markdown if requested
        if save_markdown:
            md_path = output_path / f"{timestamp}_email.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(email_data.get('email', ''))
            saved_files['markdown'] = md_path
            logger.info(f"Saved Markdown email to {md_path}")
        
        return saved_files
        
    except PermissionError as e:
        logger.error(f"Permission error saving files: {e}")
        raise
    except OSError as e:
        logger.error(f"I/O error saving files: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving files: {e}")
        raise

def save_analysis_results(
    analysis_results: Dict[str, Any],
    output_dir: Union[str, Path] = "./output",
    timestamp: Optional[str] = None
) -> Path:
    """
    Save analysis results to a JSON file in the output directory.
    
    Args:
        analysis_results: Dictionary containing the analysis results
        output_dir: Path to the output directory
        timestamp: Optional timestamp to use in filenames (default: current time)
        
    Returns:
        Path to the saved file
    """
    # Ensure the output directory exists
    output_path = ensure_output_directory(output_dir)
    
    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save the analysis results
    json_path = output_path / f"{timestamp}_analysis.json"
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2)
        logger.info(f"Saved analysis results to {json_path}")
        return json_path
    except Exception as e:
        logger.error(f"Error saving analysis results: {e}")
        raise 