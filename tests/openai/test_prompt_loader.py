"""
Tests for the Prompt Loader module.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.openai.prompt_loader import (
    find_system_prompt_file,
    load_system_prompt,
    validate_system_prompt,
    load_and_validate_system_prompt,
    PromptValidationError,
    REQUIRED_SECTIONS
)

class TestPromptLoader:
    """Test cases for the Prompt Loader module."""
    
    def test_find_system_prompt_file_found(self):
        """Test finding the system prompt file in a common location."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock system prompt file
            prompt_path = Path(temp_dir) / "system-prompt.md"
            with open(prompt_path, 'w') as f:
                f.write("Test system prompt")
            
            # Call the function with the base path
            found_path = find_system_prompt_file(temp_dir)
            
            # Verify the correct file was found
            assert found_path == prompt_path
    
    def test_find_system_prompt_file_alternate_name(self):
        """Test finding the system prompt file with an alternate name."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock system prompt file with an alternate name
            prompt_path = Path(temp_dir) / "SYSTEM_PROMPT.md"
            with open(prompt_path, 'w') as f:
                f.write("Test system prompt")
            
            # Call the function with the base path
            found_path = find_system_prompt_file(temp_dir)
            
            # Verify the correct file was found
            assert found_path == prompt_path
    
    def test_find_system_prompt_file_in_subdirectory(self):
        """Test finding the system prompt file in a subdirectory."""
        # Create a temporary directory structure with subdirectories
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectories
            docs_dir = Path(temp_dir) / "docs"
            docs_dir.mkdir()
            
            # Create a mock system prompt file in the docs directory
            prompt_path = docs_dir / "system-prompt.md"
            with open(prompt_path, 'w') as f:
                f.write("Test system prompt")
            
            # Call the function with the base path
            found_path = find_system_prompt_file(temp_dir)
            
            # Verify the correct file was found
            assert found_path == prompt_path
    
    def test_find_system_prompt_file_not_found(self):
        """Test that FileNotFoundError is raised when the system prompt file is not found."""
        # Create a temporary directory with no system prompt files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Call the function with the base path
            with pytest.raises(FileNotFoundError) as excinfo:
                find_system_prompt_file(temp_dir)
            
            # Verify the error message mentions searching
            assert "System prompt file not found" in str(excinfo.value)
    
    def test_load_system_prompt_explicit_path(self):
        """Test loading the system prompt from an explicit path."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_file:
            prompt_content = "Test system prompt content"
            temp_file.write(prompt_content.encode('utf-8'))
            temp_file.close()
            
            try:
                # Call the function with the explicit path
                prompt = load_system_prompt(temp_file.name)
                
                # Verify the content was loaded correctly
                assert prompt == prompt_content
            finally:
                # Clean up
                os.unlink(temp_file.name)
    
    def test_load_system_prompt_file_not_found(self):
        """Test that FileNotFoundError is raised when the specified file is not found."""
        nonexistent_path = "/path/to/nonexistent/file.md"
        
        # Call the function with a nonexistent path
        with pytest.raises(FileNotFoundError) as excinfo:
            load_system_prompt(nonexistent_path)
        
        # Verify the error message mentions the path
        assert nonexistent_path in str(excinfo.value)
    
    def test_load_system_prompt_auto_find(self):
        """Test loading the system prompt by automatically finding the file."""
        prompt_content = "Test system prompt content"
        
        # Mock find_system_prompt_file to return a known path
        with patch('src.openai.prompt_loader.find_system_prompt_file') as mock_find_file, \
             patch('builtins.open', mock_open(read_data=prompt_content)):
            mock_find_file.return_value = Path("/mock/path/system-prompt.md")
            
            # Call the function without an explicit path
            prompt = load_system_prompt()
            
            # Verify find_system_prompt_file was called
            mock_find_file.assert_called_once()
            
            # Verify the content was loaded correctly
            assert prompt == prompt_content
    
    def test_validate_system_prompt_valid(self):
        """Test validating a valid system prompt."""
        # Create a valid system prompt with all required sections
        sections = []
        for section in REQUIRED_SECTIONS:
            sections.append(f"## {section}\nTest content for {section}")
        
        # Add specific content for the Output Contract section
        sections.append("""
## 8 · Output Contract

Return a JSON object with keys:  

```json
{
  "email_markdown": "<compiled email>",
  "flags": ["collection_pct_low", "case_acceptance_opportunity", ...],
  "kpi_table": {
    "net_production": { "value": 85187.40, "delta_mom": -0.12, "band": "Low" },
    ...
  },
  "version": "2.1"
}
```

Only Markdown appears inside `email_markdown`; no additional commentary outside the JSON envelope.
""")
        
        valid_prompt = "\n\n".join(sections)
        
        # Call the validation function
        result = validate_system_prompt(valid_prompt)
        
        # Verify the prompt was validated successfully
        assert result is True
    
    def test_validate_system_prompt_empty(self):
        """Test validation of an empty prompt raises an error."""
        # Call the validation function with an empty prompt
        with pytest.raises(PromptValidationError) as excinfo:
            validate_system_prompt("")
        
        # Verify the error message
        assert "System prompt is empty" in str(excinfo.value)
    
    def test_validate_system_prompt_missing_sections(self):
        """Test validation of a prompt with missing sections raises an error."""
        # Create a prompt missing some required sections
        valid_sections = REQUIRED_SECTIONS[:3]  # Only include the first 3 sections
        sections = []
        for section in valid_sections:
            sections.append(f"## {section}\nTest content for {section}")
        
        incomplete_prompt = "\n\n".join(sections)
        
        # Call the validation function
        with pytest.raises(PromptValidationError) as excinfo:
            validate_system_prompt(incomplete_prompt)
        
        # Verify the error message mentions missing sections
        assert "System prompt is missing required sections" in str(excinfo.value)
        
        # Check that all missing sections are mentioned
        error_message = str(excinfo.value)
        for section in REQUIRED_SECTIONS[3:]:
            assert section in error_message
    
    def test_validate_system_prompt_missing_json_structure(self):
        """Test validation of a prompt missing the JSON structure in section 8."""
        # Create a prompt with all sections but missing the JSON structure in section 8
        sections = []
        for section in REQUIRED_SECTIONS:
            if section == "8 · Output Contract":
                sections.append(f"## {section}\nMissing JSON structure")
            else:
                sections.append(f"## {section}\nTest content for {section}")
        
        invalid_prompt = "\n\n".join(sections)
        
        # Call the validation function
        with pytest.raises(PromptValidationError) as excinfo:
            validate_system_prompt(invalid_prompt)
        
        # Verify the error message mentions the missing JSON structure
        assert "missing JSON structure in section 8" in str(excinfo.value)
    
    def test_load_and_validate_system_prompt(self):
        """Test the combined load and validate function."""
        # Create a valid system prompt
        sections = []
        for section in REQUIRED_SECTIONS:
            sections.append(f"## {section}\nTest content for {section}")
        
        # Add JSON structure to section 8
        sections.append("""
## 8 · Output Contract

```json
{
  "email_markdown": "<compiled email>",
  "flags": [],
  "kpi_table": {}
}
```
""")
        
        valid_prompt = "\n\n".join(sections)
        
        # Mock the loading and validation functions
        with patch('src.openai.prompt_loader.load_system_prompt', return_value=valid_prompt) as mock_load, \
             patch('src.openai.prompt_loader.validate_system_prompt', return_value=True) as mock_validate:
            
            # Call the combined function
            result = load_and_validate_system_prompt("/mock/path")
            
            # Verify the loading function was called with the path
            mock_load.assert_called_once_with("/mock/path")
            
            # Verify the validation function was called with the prompt
            mock_validate.assert_called_once_with(valid_prompt)
            
            # Verify the result is the prompt
            assert result == valid_prompt 