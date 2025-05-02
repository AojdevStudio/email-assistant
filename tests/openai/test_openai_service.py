"""
Tests for the OpenAI Service module.
"""

import os
import io
import time
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open, call

from src.openai.openai_service import OpenAIService, MAX_FILE_SIZE_MB, DEFAULT_TIMEOUT
from src.openai.prompt_loader import PromptValidationError
from openai import APIError, APIConnectionError, RateLimitError

class TestOpenAIService:
    """Test cases for the OpenAIService class."""
    
    def test_init_with_explicit_api_key(self):
        """Test initialization with an explicitly provided API key."""
        test_api_key = "test_key_123"
        
        with patch('openai.OpenAI') as mock_openai:
            service = OpenAIService(api_key=test_api_key)
            
            # Check that the API key was set correctly
            assert service.api_key == test_api_key
            
            # Check that the OpenAI client was initialized with the correct API key
            mock_openai.assert_called_once_with(api_key=test_api_key)
    
    def test_init_with_env_api_key(self):
        """Test initialization with an API key from environment variables."""
        test_api_key = "env_key_456"
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": test_api_key}), \
             patch('openai.OpenAI') as mock_openai:
            service = OpenAIService()
            
            # Check that the API key was retrieved from the environment
            assert service.api_key == test_api_key
            
            # Check that the OpenAI client was initialized with the correct API key
            mock_openai.assert_called_once_with(api_key=test_api_key)
    
    def test_init_without_api_key(self):
        """Test initialization without an API key raises an error."""
        with patch.dict(os.environ, {}, clear=True), \
             patch('openai.OpenAI'):
            with pytest.raises(ValueError) as excinfo:
                OpenAIService()
            
            # Check that the error message mentions the API key
            assert "OpenAI API key not found" in str(excinfo.value)
    
    def test_init_client_exception(self):
        """Test handling of exceptions during client initialization."""
        test_api_key = "test_key_789"
        test_error = Exception("Test client initialization error")
        
        with patch('openai.OpenAI') as mock_openai:
            # Make the OpenAI constructor raise an exception
            mock_openai.side_effect = test_error
            
            with pytest.raises(Exception) as excinfo:
                OpenAIService(api_key=test_api_key)
            
            # Check that the exception was propagated
            assert excinfo.value == test_error
    
    def test_handle_api_error_rate_limit(self):
        """Test handling of RateLimitError."""
        service = OpenAIService(api_key="test_key")
        error = RateLimitError("Rate limit exceeded")
        
        with pytest.raises(RateLimitError):
            service.handle_api_error("test operation", error)
    
    def test_handle_api_error_connection(self):
        """Test handling of APIConnectionError."""
        service = OpenAIService(api_key="test_key")
        error = APIConnectionError("Connection failed")
        
        with pytest.raises(APIConnectionError):
            service.handle_api_error("test operation", error)
    
    def test_handle_api_error_api_error(self):
        """Test handling of APIError."""
        service = OpenAIService(api_key="test_key")
        error = APIError("API error occurred")
        
        with pytest.raises(APIError):
            service.handle_api_error("test operation", error)
    
    def test_handle_api_error_other(self):
        """Test handling of other exceptions."""
        service = OpenAIService(api_key="test_key")
        error = ValueError("Some other error")
        
        with pytest.raises(ValueError):
            service.handle_api_error("test operation", error)
    
    def test_dataframe_to_csv_bytes_valid(self):
        """Test conversion of a DataFrame to CSV bytes with valid size."""
        # Create a small test DataFrame
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        
        service = OpenAIService(api_key="test_key")
        csv_bytes, size_bytes = service.dataframe_to_csv_bytes(df)
        
        # Verify the result is bytes and has content
        assert isinstance(csv_bytes, bytes)
        assert size_bytes > 0
        
        # Verify the content is as expected
        csv_str = csv_bytes.decode('utf-8')
        assert "A,B" in csv_str
        assert "1,a" in csv_str
        assert "2,b" in csv_str
        assert "3,c" in csv_str
    
    def test_dataframe_to_csv_bytes_size_exceeded(self):
        """Test that a DataFrame exceeding the max size raises ValueError."""
        # Create a mock DataFrame that will exceed the size limit
        df = MagicMock(spec=pd.DataFrame)
        
        # Mock the to_csv method to write a large amount of data
        def mock_to_csv(buffer, index=None):
            # Write a string that's larger than the max file size
            large_bytes = b'X' * (MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
            buffer.write(large_bytes)
        
        df.to_csv.side_effect = mock_to_csv
        
        service = OpenAIService(api_key="test_key")
        
        with pytest.raises(ValueError) as excinfo:
            service.dataframe_to_csv_bytes(df)
        
        # Check the error message mentions the file size
        assert "File size" in str(excinfo.value)
        assert "exceeds maximum allowed size" in str(excinfo.value)
    
    def test_upload_dataframe_success(self):
        """Test successful upload of a DataFrame."""
        # Create a small test DataFrame
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['a', 'b', 'c']
        })
        
        # Mock the OpenAI client and response
        mock_file_response = MagicMock()
        mock_file_response.id = "file-123456"
        
        with patch.object(OpenAIService, 'dataframe_to_csv_bytes', return_value=(b'csv_data', 100)) as mock_to_csv_bytes:
            service = OpenAIService(api_key="test_key")
            service.client = MagicMock()
            service.client.files.create.return_value = mock_file_response
            
            file_id = service.upload_dataframe(df, "test.csv")
            
            # Check that dataframe_to_csv_bytes was called with the DataFrame
            mock_to_csv_bytes.assert_called_once_with(df)
            
            # Check that the client's create method was called with the correct arguments
            service.client.files.create.assert_called_once()
            create_args = service.client.files.create.call_args[1]
            assert create_args["purpose"] == "assistants"
            assert create_args["filename"] == "test.csv"
            
            # Check that the correct file ID was returned
            assert file_id == "file-123456"
    
    def test_upload_dataframe_api_error(self):
        """Test handling of API errors during DataFrame upload."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock the OpenAI client to raise an API error
        with patch.object(OpenAIService, 'dataframe_to_csv_bytes', return_value=(b'csv_data', 100)):
            service = OpenAIService(api_key="test_key")
            service.client = MagicMock()
            service.client.files.create.side_effect = APIError("API Error")
            
            with pytest.raises(APIError):
                service.upload_dataframe(df)
    
    def test_upload_dataframe_size_error(self):
        """Test handling of file size errors during DataFrame upload."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock dataframe_to_csv_bytes to raise a ValueError for file size
        size_error = ValueError(f"File size exceeds maximum allowed size ({MAX_FILE_SIZE_MB} MB)")
        
        with patch.object(OpenAIService, 'dataframe_to_csv_bytes', side_effect=size_error):
            service = OpenAIService(api_key="test_key")
            
            with pytest.raises(ValueError) as excinfo:
                service.upload_dataframe(df)
            
            # Check that the error was propagated
            assert str(excinfo.value) == str(size_error)
    
    def test_create_thread_success(self):
        """Test successful thread creation."""
        # Mock the OpenAI client response
        mock_thread = MagicMock()
        mock_thread.id = "thread-123456"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.create.return_value = mock_thread
        
        thread = service.create_thread()
        
        # Check that the client's create method was called
        service.client.beta.threads.create.assert_called_once()
        
        # Check that the correct thread was returned
        assert thread.id == "thread-123456"
    
    def test_create_thread_api_error(self):
        """Test handling of API errors during thread creation."""
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.create.side_effect = APIError("API Error")
        
        with pytest.raises(APIError):
            service.create_thread()
    
    def test_add_message_success(self):
        """Test successful message creation."""
        # Mock the OpenAI client response
        mock_message = MagicMock()
        mock_message.id = "msg-123456"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.messages.create.return_value = mock_message
        
        thread_id = "thread-123456"
        content = "Test message content"
        
        message = service.add_message(thread_id, content)
        
        # Check that the client's create method was called with the correct arguments
        service.client.beta.threads.messages.create.assert_called_once()
        create_args = service.client.beta.threads.messages.create.call_args[1]
        assert create_args["thread_id"] == thread_id
        assert create_args["content"] == content
        assert create_args["role"] == "user"
        assert create_args["file_ids"] == []
        
        # Check that the correct message was returned
        assert message.id == "msg-123456"
    
    def test_add_message_with_files(self):
        """Test message creation with file attachments."""
        # Mock the OpenAI client response
        mock_message = MagicMock()
        mock_message.id = "msg-123456"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.messages.create.return_value = mock_message
        
        thread_id = "thread-123456"
        content = "Test message content"
        file_ids = ["file-123", "file-456"]
        
        message = service.add_message(thread_id, content, file_ids)
        
        # Check that the client's create method was called with the correct arguments
        service.client.beta.threads.messages.create.assert_called_once()
        create_args = service.client.beta.threads.messages.create.call_args[1]
        assert create_args["thread_id"] == thread_id
        assert create_args["content"] == content
        assert create_args["role"] == "user"
        assert create_args["file_ids"] == file_ids
        
        # Check that the correct message was returned
        assert message.id == "msg-123456"
    
    def test_add_message_api_error(self):
        """Test handling of API errors during message creation."""
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.messages.create.side_effect = APIError("API Error")
        
        with pytest.raises(APIError):
            service.add_message("thread-123456", "Test content")
    
    def test_add_kpi_analysis_message(self):
        """Test the KPI analysis message creation."""
        thread_id = "thread-123456"
        file_id = "file-123456"
        
        # Mock the add_message method
        with patch.object(OpenAIService, 'add_message', return_value=MagicMock()) as mock_add_message:
            service = OpenAIService(api_key="test_key")
            
            # Call the method without custom instructions
            service.add_kpi_analysis_message(thread_id, file_id)
            
            # Check that add_message was called with the correct arguments
            mock_add_message.assert_called_once()
            call_args = mock_add_message.call_args[1]
            assert call_args["thread_id"] == thread_id
            assert call_args["file_ids"] == [file_id]
            assert "analyze" in call_args["content"]
            
            # Reset the mock
            mock_add_message.reset_mock()
            
            # Call the method with custom instructions
            custom_instructions = "Custom analysis instructions"
            service.add_kpi_analysis_message(thread_id, file_id, custom_instructions)
            
            # Check that add_message was called with the custom instructions
            mock_add_message.assert_called_once()
            call_args = mock_add_message.call_args[1]
            assert call_args["content"] == custom_instructions
    
    def test_run_assistant_success(self):
        """Test successful assistant run."""
        # Mock the OpenAI client and responses
        mock_run = MagicMock()
        mock_run.id = "run-123456"
        mock_run.status = "completed"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.runs.create.return_value = mock_run
        service.client.beta.threads.runs.retrieve.return_value = mock_run
        
        # Test parameters
        thread_id = "thread-123456"
        assistant_id = "asst-123456"
        
        # Run the assistant
        run = service.run_assistant(thread_id, assistant_id)
        
        # Check that the client's methods were called with the correct arguments
        service.client.beta.threads.runs.create.assert_called_once_with(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        service.client.beta.threads.runs.retrieve.assert_called_once_with(
            thread_id=thread_id,
            run_id=mock_run.id
        )
        
        # Check that the correct run was returned
        assert run.id == "run-123456"
    
    def test_run_assistant_polling(self):
        """Test assistant run with status polling."""
        # Create a series of run statuses to simulate polling
        thread_id = "thread-123456"
        assistant_id = "asst-123456"
        run_id = "run-123456"
        
        # Mock the initial run creation
        initial_run = MagicMock()
        initial_run.id = run_id
        
        # Create status responses for polling: in_progress → completed
        in_progress_run = MagicMock()
        in_progress_run.id = run_id
        in_progress_run.status = "in_progress"
        
        completed_run = MagicMock()
        completed_run.id = run_id
        completed_run.status = "completed"
        
        # Set up the client mock
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.runs.create.return_value = initial_run
        
        # Set up the retrieve mock to return different statuses
        service.client.beta.threads.runs.retrieve.side_effect = [
            in_progress_run,  # First check: in_progress
            completed_run     # Second check: completed
        ]
        
        # Mock time.sleep to avoid actual waiting
        with patch('time.sleep'):
            # Run the assistant
            run = service.run_assistant(thread_id, assistant_id)
            
            # Check that create was called once with the correct arguments
            service.client.beta.threads.runs.create.assert_called_once_with(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Check that retrieve was called twice with the correct arguments
            assert service.client.beta.threads.runs.retrieve.call_count == 2
            for call_args in service.client.beta.threads.runs.retrieve.call_args_list:
                kwargs = call_args[1]
                assert kwargs["thread_id"] == thread_id
                assert kwargs["run_id"] == run_id
            
            # Check that the completed run was returned
            assert run.status == "completed"
    
    def test_run_assistant_timeout(self):
        """Test assistant run timeout."""
        thread_id = "thread-123456"
        assistant_id = "asst-123456"
        run_id = "run-123456"
        
        # Mock run with status that never completes
        mock_run = MagicMock()
        mock_run.id = run_id
        mock_run.status = "in_progress"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.runs.create.return_value = mock_run
        service.client.beta.threads.runs.retrieve.return_value = mock_run
        
        # Set a very short timeout
        short_timeout = 0.1
        
        # Mock time.sleep to prevent actual waiting, but allow time.time to advance
        with patch('time.sleep'):
            # Advance time.time each time it's called
            original_time = time.time
            counter = [0]
            
            def mock_time():
                counter[0] += 0.2  # Increment more than timeout to trigger timeout
                return original_time() + counter[0]
            
            with patch('time.time', side_effect=mock_time):
                # Run should time out
                with pytest.raises(TimeoutError) as excinfo:
                    service.run_assistant(thread_id, assistant_id, timeout=short_timeout)
                
                # Check the error message mentions timeout
                assert "timed out" in str(excinfo.value)
    
    def test_run_assistant_failure(self):
        """Test assistant run failure."""
        thread_id = "thread-123456"
        assistant_id = "asst-123456"
        run_id = "run-123456"
        
        # Mock failed run
        initial_run = MagicMock()
        initial_run.id = run_id
        
        failed_run = MagicMock()
        failed_run.id = run_id
        failed_run.status = "failed"
        failed_run.last_error = "Something went wrong"
        
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.runs.create.return_value = initial_run
        service.client.beta.threads.runs.retrieve.return_value = failed_run
        
        # Mock time.sleep to avoid actual waiting
        with patch('time.sleep'):
            # Run should raise a RuntimeError
            with pytest.raises(RuntimeError) as excinfo:
                service.run_assistant(thread_id, assistant_id)
            
            # Check the error message mentions the failure
            assert "Run failed with status" in str(excinfo.value)
    
    def test_get_response_success(self):
        """Test successful response retrieval."""
        thread_id = "thread-123456"
        
        # Mock message content
        text_content = MagicMock()
        text_content.text = MagicMock()
        text_content.text.value = "This is the response content."
        
        # Mock message
        mock_message = MagicMock()
        mock_message.id = "msg-123456"
        mock_message.role = "assistant"
        mock_message.content = [text_content]
        mock_message.created_at = 1622222222
        
        # Mock messages list
        mock_messages = MagicMock()
        mock_messages.data = [mock_message]  # Assistant message is first in list
        
        # Set up the client mock
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.messages.list.return_value = mock_messages
        
        # Get the response
        response = service.get_response(thread_id)
        
        # Check that list was called with the correct arguments
        service.client.beta.threads.messages.list.assert_called_once_with(
            thread_id=thread_id,
            order="desc"
        )
        
        # Check the response content
        assert response["message_id"] == "msg-123456"
        assert response["thread_id"] == thread_id
        assert response["content"] == "This is the response content."
        assert response["created_at"] == 1622222222
    
    def test_get_response_no_assistant_messages(self):
        """Test response retrieval with no assistant messages."""
        thread_id = "thread-123456"
        
        # Mock message from user (not from assistant)
        mock_user_message = MagicMock()
        mock_user_message.role = "user"
        
        # Mock messages list with only user message
        mock_messages = MagicMock()
        mock_messages.data = [mock_user_message]
        
        # Set up the client mock
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.threads.messages.list.return_value = mock_messages
        
        # Should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            service.get_response(thread_id)
        
        # Check the error message
        assert "No assistant messages found" in str(excinfo.value)
    
    def test_analyze_kpi_data_success(self):
        """Test successful KPI data analysis flow."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock successful responses for each step
        file_id = "file-123456"
        thread_id = "thread-123456"
        message_id = "msg-123456"
        assistant_id = "asst-123456"
        
        # Mock thread
        mock_thread = MagicMock()
        mock_thread.id = thread_id
        
        # Mock response content
        mock_response = {
            "message_id": message_id,
            "thread_id": thread_id,
            "content": "Analysis results",
            "created_at": 1622222222
        }
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock each method in the flow
        with patch.object(service, 'upload_dataframe', return_value=file_id) as mock_upload, \
             patch.object(service, 'create_thread', return_value=mock_thread) as mock_create_thread, \
             patch.object(service, 'add_kpi_analysis_message') as mock_add_message, \
             patch.object(service, 'run_assistant') as mock_run, \
             patch.object(service, 'get_response', return_value=mock_response) as mock_get_response:
            
            # Run the analysis
            result = service.analyze_kpi_data(df, assistant_id)
            
            # Check that each method was called with the correct arguments
            mock_upload.assert_called_once_with(df, "kpi_data.csv")
            mock_create_thread.assert_called_once()
            mock_add_message.assert_called_once_with(thread_id, file_id, None)
            mock_run.assert_called_once_with(thread_id, assistant_id, DEFAULT_TIMEOUT)
            mock_get_response.assert_called_once_with(thread_id)
            
            # Check the result
            assert result["message_id"] == message_id
            assert result["thread_id"] == thread_id
            assert result["content"] == "Analysis results"
            assert result["created_at"] == 1622222222
            assert result["file_id"] == file_id
            assert result["assistant_id"] == assistant_id
    
    def test_analyze_kpi_data_custom_params(self):
        """Test KPI data analysis with custom parameters."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock successful responses
        file_id = "file-123456"
        thread_id = "thread-123456"
        assistant_id = "asst-123456"
        
        # Custom parameters
        custom_instructions = "Custom analysis instructions"
        custom_timeout = 600
        custom_filename = "custom_file.csv"
        
        # Mock thread
        mock_thread = MagicMock()
        mock_thread.id = thread_id
        
        # Mock response
        mock_response = {
            "message_id": "msg-123456",
            "thread_id": thread_id,
            "content": "Analysis results",
            "created_at": 1622222222
        }
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock each method in the flow
        with patch.object(service, 'upload_dataframe', return_value=file_id) as mock_upload, \
             patch.object(service, 'create_thread', return_value=mock_thread) as mock_create_thread, \
             patch.object(service, 'add_kpi_analysis_message') as mock_add_message, \
             patch.object(service, 'run_assistant') as mock_run, \
             patch.object(service, 'get_response', return_value=mock_response) as mock_get_response:
            
            # Run the analysis with custom parameters
            service.analyze_kpi_data(
                df, 
                assistant_id,
                instructions=custom_instructions,
                timeout=custom_timeout,
                filename=custom_filename
            )
            
            # Check that the custom parameters were passed correctly
            mock_upload.assert_called_once_with(df, custom_filename)
            mock_add_message.assert_called_once_with(thread_id, file_id, custom_instructions)
            mock_run.assert_called_once_with(thread_id, assistant_id, custom_timeout)
    
    def test_analyze_kpi_data_error_handling(self):
        """Test error handling in the KPI data analysis flow."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock an error in one of the steps
        error = APIError("API error in upload")
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock upload_dataframe to raise an error
        with patch.object(service, 'upload_dataframe', side_effect=error):
            # The error should be propagated
            with pytest.raises(APIError) as excinfo:
                service.analyze_kpi_data(df, "asst-123456")
            
            # Check that the error was propagated
            assert excinfo.value == error
    
    def test_create_assistant_with_system_prompt(self):
        """Test creating an assistant with a system prompt."""
        # Mock system prompt path and content
        system_prompt_path = "/mock/path/system-prompt.md"
        system_prompt_content = "Test system prompt content"
        
        # Mock assistant response
        mock_assistant = MagicMock()
        mock_assistant.id = "asst-123456"
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        service.client = MagicMock()
        service.client.beta.assistants.create.return_value = mock_assistant
        
        # Mock the load_and_validate_system_prompt function
        with patch('src.openai.openai_service.load_and_validate_system_prompt', 
                return_value=system_prompt_content) as mock_load_prompt:
            
            # Call the method
            assistant = service.create_assistant(
                system_prompt_path=system_prompt_path,
                name="Test Assistant",
                model="gpt-4o"
            )
            
            # Check that load_and_validate_system_prompt was called with the correct path
            mock_load_prompt.assert_called_once_with(system_prompt_path)
            
            # Check that the assistant was created with the correct parameters
            service.client.beta.assistants.create.assert_called_once()
            create_args = service.client.beta.assistants.create.call_args[1]
            assert create_args["name"] == "Test Assistant"
            assert create_args["model"] == "gpt-4o"
            assert create_args["instructions"] == system_prompt_content
            assert create_args["tools"] == [{"type": "code_interpreter"}]
            
            # Check that the correct assistant was returned
            assert assistant == mock_assistant
    
    def test_create_assistant_prompt_validation_error(self):
        """Test error handling when the system prompt fails validation."""
        # Mock system prompt path
        system_prompt_path = "/mock/path/system-prompt.md"
        
        # Mock a validation error
        validation_error = PromptValidationError("Invalid system prompt")
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock load_and_validate_system_prompt to raise a validation error
        with patch('src.openai.openai_service.load_and_validate_system_prompt', 
                side_effect=validation_error) as mock_load_prompt:
            
            # The error should be propagated
            with pytest.raises(PromptValidationError) as excinfo:
                service.create_assistant(system_prompt_path=system_prompt_path)
            
            # Check that the error was propagated
            assert excinfo.value == validation_error
            
            # Check that load_and_validate_system_prompt was called with the correct path
            mock_load_prompt.assert_called_once_with(system_prompt_path)
            
            # Check that no assistant was created
            assert not service.client.beta.assistants.create.called
    
    def test_analyze_kpi_data_with_system_prompt(self):
        """Test analyzing KPI data with a system prompt."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock system prompt path
        system_prompt_path = "/mock/path/system-prompt.md"
        
        # Mock assistant
        mock_assistant = MagicMock()
        mock_assistant.id = "asst-123456"
        
        # Mock response
        mock_response = {
            "message_id": "msg-123456",
            "thread_id": "thread-123456",
            "content": "Analysis results",
            "created_at": 1622222222,
            "file_id": "file-123456",
            "assistant_id": "asst-123456"
        }
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock the methods
        with patch.object(service, 'create_assistant', return_value=mock_assistant) as mock_create_assistant, \
             patch.object(service, 'analyze_kpi_data', return_value=mock_response) as mock_analyze_kpi_data:
            
            # Call the method
            result = service.analyze_kpi_data_with_system_prompt(
                df,
                system_prompt_path=system_prompt_path,
                instructions="Custom instructions",
                model="gpt-4o",
                timeout=600,
                filename="custom.csv"
            )
            
            # Check that create_assistant was called with the correct parameters
            mock_create_assistant.assert_called_once_with(
                system_prompt_path=system_prompt_path,
                model="gpt-4o"
            )
            
            # Check that analyze_kpi_data was called with the correct parameters
            mock_analyze_kpi_data.assert_called_once_with(
                df=df,
                assistant_id=mock_assistant.id,
                instructions="Custom instructions",
                timeout=600,
                filename="custom.csv"
            )
            
            # Check that the correct response was returned
            assert result == mock_response
    
    def test_analyze_kpi_data_with_system_prompt_error(self):
        """Test error handling in the analyze_kpi_data_with_system_prompt method."""
        # Create a test DataFrame
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        # Mock system prompt path
        system_prompt_path = "/mock/path/system-prompt.md"
        
        # Mock an error in create_assistant
        error = FileNotFoundError("System prompt file not found")
        
        # Set up the service mock
        service = OpenAIService(api_key="test_key")
        
        # Mock create_assistant to raise an error
        with patch.object(service, 'create_assistant', side_effect=error) as mock_create_assistant:
            
            # The error should be propagated
            with pytest.raises(FileNotFoundError) as excinfo:
                service.analyze_kpi_data_with_system_prompt(
                    df,
                    system_prompt_path=system_prompt_path
                )
            
            # Check that the error was propagated
            assert excinfo.value == error
            
            # Check that create_assistant was called with the correct parameters
            mock_create_assistant.assert_called_once_with(
                system_prompt_path=system_prompt_path,
                model="gpt-4o"
            ) 