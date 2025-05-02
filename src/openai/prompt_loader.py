"""
Prompt Loader Module

This module handles loading and validating the system prompt from the system-prompt.md
file for use with the OpenAI Assistant.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Section headings in system prompt
REQUIRED_SECTIONS = [
    "1 · Role & Mission",
    "2 · Communication Signature",
    "3 · Data Input Contract",
    "4 · Benchmark Retrieval",
    "5 · Analysis Workflow",
    "6 · Email Skeleton",
    "7 · Dynamic Rules",
    "8 · Output Contract"
]

class PromptValidationError(Exception):
    """Exception raised when a system prompt fails validation."""
    pass

def find_system_prompt_file(base_path: Optional[str] = None) -> Path:
    """
    Find the system prompt file by looking in common locations.
    
    Args:
        base_path: Optional base directory to start the search
        
    Returns:
        Path to the system prompt file
        
    Raises:
        FileNotFoundError: If the system prompt file cannot be found
    """
    # Common filenames for system prompt
    filenames = ["system-prompt.md", "SYSTEM_PROMPT.md", "system_prompt.md"]
    
    # Common locations to check relative to base_path
    search_paths = [
        "",                  # Current directory
        "./",                # Explicit current directory
        "../",               # Parent directory
        "docs/",             # Docs directory
        "prompts/",          # Prompts directory
    ]
    
    # Determine the base path
    if base_path:
        base = Path(base_path)
    else:
        # Try to use the current working directory if not specified
        base = Path.cwd()
    
    # Search for the file in common locations
    for path in search_paths:
        for filename in filenames:
            file_path = base / path / filename
            if file_path.exists():
                logger.info(f"Found system prompt file at: {file_path}")
                return file_path
    
    # If we get here, the file was not found
    error_msg = f"System prompt file not found. Searched in: {', '.join(search_paths)}"
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

def load_system_prompt(file_path: Optional[str] = None) -> str:
    """
    Load the system prompt from the specified file or find it automatically.
    
    Args:
        file_path: Optional explicit path to the system prompt file
        
    Returns:
        The system prompt as a string
        
    Raises:
        FileNotFoundError: If the system prompt file cannot be found
    """
    # Find the system prompt file if not specified
    if file_path:
        prompt_file = Path(file_path)
        if not prompt_file.exists():
            error_msg = f"System prompt file not found at: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    else:
        prompt_file = find_system_prompt_file()
    
    # Read the file
    try:
        logger.info(f"Loading system prompt from: {prompt_file}")
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        
        logger.info(f"Successfully loaded system prompt ({len(prompt)} chars)")
        return prompt
        
    except Exception as e:
        error_msg = f"Error reading system prompt file: {str(e)}"
        logger.error(error_msg)
        raise

def validate_system_prompt(prompt: str) -> bool:
    """
    Validate that the system prompt contains all required sections,
    particularly section 8 mentioned in acceptance criteria.
    
    Args:
        prompt: The system prompt to validate
        
    Returns:
        True if the prompt is valid
        
    Raises:
        PromptValidationError: If the prompt is invalid
    """
    # Check if the prompt is empty
    if not prompt or not prompt.strip():
        error_msg = "System prompt is empty"
        logger.error(error_msg)
        raise PromptValidationError(error_msg)
    
    # Check for all required sections
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        section_pattern = rf"#+\s*{re.escape(section)}"
        if not re.search(section_pattern, prompt, re.IGNORECASE):
            missing_sections.append(section)
    
    if missing_sections:
        error_msg = f"System prompt is missing required sections: {', '.join(missing_sections)}"
        logger.error(error_msg)
        raise PromptValidationError(error_msg)
    
    # Specifically check for section 8 (Output Contract) with JSON structure
    if "8 · Output Contract" in REQUIRED_SECTIONS:
        output_contract_pattern = r'```json\s*{\s*"email_markdown":'
        if not re.search(output_contract_pattern, prompt, re.DOTALL):
            error_msg = "System prompt is missing JSON structure in section 8 (Output Contract)"
            logger.error(error_msg)
            raise PromptValidationError(error_msg)
    
    logger.info("System prompt validation successful")
    return True

def load_and_validate_system_prompt(file_path: Optional[str] = None) -> str:
    """
    Load and validate the system prompt from the specified file or find it automatically.
    
    Args:
        file_path: Optional explicit path to the system prompt file
        
    Returns:
        The validated system prompt as a string
        
    Raises:
        FileNotFoundError: If the system prompt file cannot be found
        PromptValidationError: If the prompt is invalid
    """
    prompt = load_system_prompt(file_path)
    validate_system_prompt(prompt)
    return prompt 