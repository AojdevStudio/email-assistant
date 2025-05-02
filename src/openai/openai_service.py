"""
OpenAI Service Module

This module provides a service layer for interacting with the OpenAI Assistants API v2,
with minimal functionality needed for the MVP. It handles client initialization,
basic error handling, and logging.
"""

import os
import io
import time
from typing import Optional, Dict, Any, List, Tuple, Union

import pandas as pd
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from openai.types.beta.threads import Thread
from openai.types.beta.threads.thread_message import ThreadMessage
from openai.types.beta.threads.run import Run
from openai.types.beta.assistant import Assistant

from src.utils.logging import get_logger
from src.openai.prompt_loader import load_and_validate_system_prompt, PromptValidationError

# Initialize logger
logger = get_logger(__name__)

# Constants
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB for validation
DEFAULT_TIMEOUT = 300   # Default timeout in seconds for run completion
POLL_INTERVAL = 1.0     # Time to wait between status checks in seconds
DEFAULT_MODEL = "gpt-4o"  # Default model for OpenAI assistants

class OpenAIService:
    """
    Service for interacting with the OpenAI Assistants API v2.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client with the given API key or from environment.
        
        Args:
            api_key: OpenAI API key. If not provided, it will be read from the
                    OPENAI_API_KEY environment variable.
        
        Raises:
            ValueError: If the API key is not provided and not found in environment variables.
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            error_msg = "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or provide it explicitly."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Initialize the client
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def handle_api_error(self, operation: str, error: Exception) -> None:
        """
        Handle common OpenAI API errors with appropriate logging.
        
        Args:
            operation: Description of the operation being performed
            error: The exception that was raised
            
        Raises:
            The original exception after logging
        """
        if isinstance(error, RateLimitError):
            logger.error(f"Rate limit exceeded during {operation}: {str(error)}")
        elif isinstance(error, APIConnectionError):
            logger.error(f"Connection error during {operation}: {str(error)}")
        elif isinstance(error, APIError):
            logger.error(f"API error during {operation}: {str(error)}")
        else:
            logger.error(f"Unexpected error during {operation}: {str(error)}")
        
        # Re-raise the exception
        raise
    
    def dataframe_to_csv_bytes(self, df: pd.DataFrame) -> Tuple[bytes, int]:
        """
        Convert a DataFrame to CSV bytes for uploading.
        
        Args:
            df: The DataFrame to convert
            
        Returns:
            A tuple containing the CSV bytes and the size in bytes
            
        Raises:
            ValueError: If the file size exceeds the maximum allowed size
        """
        # Create a buffer for the CSV data
        buffer = io.BytesIO()
        
        # Save DataFrame to the buffer as CSV
        df.to_csv(buffer, index=False)
        
        # Get the CSV data as bytes
        csv_bytes = buffer.getvalue()
        
        # Calculate size in MB
        size_bytes = len(csv_bytes)
        size_mb = size_bytes / (1024 * 1024)
        
        # Validate file size
        if size_mb > MAX_FILE_SIZE_MB:
            error_msg = f"File size ({size_mb:.2f} MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB} MB)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return csv_bytes, size_bytes
    
    def upload_dataframe(self, df: pd.DataFrame, filename: str = "kpi_data.csv") -> str:
        """
        Upload a DataFrame as a CSV file to OpenAI for use with Assistants API.
        
        Args:
            df: The DataFrame to upload
            filename: The name to give the file
            
        Returns:
            The file ID assigned by OpenAI
            
        Raises:
            ValueError: If the file size exceeds the maximum allowed size
            Various OpenAI API errors for upload failures
        """
        operation = f"uploading DataFrame as {filename}"
        logger.info(f"Starting {operation} with {len(df)} rows")
        
        try:
            # Convert DataFrame to CSV bytes and validate size
            csv_bytes, size_bytes = self.dataframe_to_csv_bytes(df)
            
            logger.info(f"Prepared CSV file of size {size_bytes/1024:.2f} KB")
            
            # Upload the file to OpenAI
            file_response = self.client.files.create(
                file=csv_bytes,
                purpose="assistants",
                filename=filename
            )
            
            file_id = file_response.id
            logger.info(f"File uploaded successfully with ID: {file_id}")
            
            return file_id
            
        except (ValueError, APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def create_thread(self) -> Thread:
        """
        Create a new thread for conversation with the assistant.
        
        Returns:
            The created Thread object
            
        Raises:
            Various OpenAI API errors if thread creation fails
        """
        operation = "creating thread"
        logger.info("Starting thread creation")
        
        try:
            # Create a new thread
            thread = self.client.beta.threads.create()
            
            logger.info(f"Thread created successfully with ID: {thread.id}")
            return thread
            
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def add_message(
        self,
        thread_id: str,
        content: str,
        file_ids: Optional[List[str]] = None
    ) -> ThreadMessage:
        """
        Add a user message to a thread, optionally with file attachments.
        
        Args:
            thread_id: The ID of the thread to add the message to
            content: The content of the message
            file_ids: Optional list of file IDs to attach to the message
            
        Returns:
            The created ThreadMessage object
            
        Raises:
            Various OpenAI API errors if message creation fails
        """
        operation = f"adding message to thread {thread_id}"
        logger.info(f"Starting {operation}")
        
        # Use empty list if file_ids is None
        file_ids = file_ids or []
        
        try:
            # Add the message to the thread
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
                file_ids=file_ids
            )
            
            logger.info(f"Message added successfully with ID: {message.id}")
            
            # Log file attachments if any
            if file_ids:
                logger.info(f"Message includes {len(file_ids)} file attachment(s)")
            
            return message
            
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def add_kpi_analysis_message(
        self,
        thread_id: str,
        file_id: str,
        instructions: Optional[str] = None
    ) -> ThreadMessage:
        """
        Add a specialized message for KPI analysis with file attachment.
        
        Args:
            thread_id: The ID of the thread to add the message to
            file_id: The ID of the uploaded KPI data file
            instructions: Optional additional instructions for the analysis
            
        Returns:
            The created ThreadMessage object
            
        Raises:
            Various OpenAI API errors if message creation fails
        """
        # Default analysis instructions if none provided
        if not instructions:
            instructions = (
                "Please analyze the attached dental KPI data file. "
                "Identify key trends, highlight any metrics outside of normal ranges, "
                "and provide meaningful insights about practice performance. "
                "Format your response for an executive email summary."
            )
        
        logger.info(f"Adding KPI analysis message with file ID: {file_id}")
        
        # Add the message with the file attachment
        return self.add_message(
            thread_id=thread_id,
            content=instructions,
            file_ids=[file_id]
        )
    
    def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Run:
        """
        Run the assistant on a thread and wait for completion.
        
        Args:
            thread_id: The ID of the thread
            assistant_id: The ID of the assistant to run
            timeout: Maximum time in seconds to wait for completion
            
        Returns:
            The completed Run object
            
        Raises:
            TimeoutError: If the run doesn't complete within the timeout
            Various OpenAI API errors if the run fails
        """
        operation = f"running assistant {assistant_id} on thread {thread_id}"
        logger.info(f"Starting {operation}")
        
        try:
            # Create a run
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            logger.info(f"Run created with ID: {run.id}")
            
            # Poll for completion
            start_time = time.time()
            while True:
                # Check for timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    error_msg = f"Run timed out after {elapsed_time:.1f} seconds (timeout: {timeout}s)"
                    logger.error(error_msg)
                    raise TimeoutError(error_msg)
                
                # Check run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                # Log progress
                logger.info(f"Run status: {run.status} (elapsed: {elapsed_time:.1f}s)")
                
                # Check if run is completed
                if run.status == "completed":
                    logger.info(f"Run completed successfully after {elapsed_time:.1f}s")
                    break
                
                # Check for failures
                if run.status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Run failed with status: {run.status}, reason: {getattr(run, 'last_error', 'unknown')}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Wait before checking again
                time.sleep(POLL_INTERVAL)
            
            return run
            
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except (TimeoutError, RuntimeError) as e:
            # These errors are already logged in the code above
            raise
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def get_response(self, thread_id: str) -> Dict[str, Any]:
        """
        Get the latest assistant response from a thread.
        
        Args:
            thread_id: The ID of the thread to get responses from
            
        Returns:
            A dictionary containing the response content and metadata
            
        Raises:
            ValueError: If no assistant messages are found
            Various OpenAI API errors if message retrieval fails
        """
        operation = f"retrieving response from thread {thread_id}"
        logger.info(f"Starting {operation}")
        
        try:
            # List all messages in the thread
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc"  # Most recent first
            )
            
            # Find the most recent assistant message
            assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
            
            if not assistant_messages:
                error_msg = "No assistant messages found in the thread"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            latest_message = assistant_messages[0]
            
            # Extract text content from the message
            content_parts = []
            for content in latest_message.content:
                if hasattr(content, 'text'):
                    content_parts.append(content.text.value)
            
            response_content = "\n".join(content_parts)
            
            # Construct response dictionary
            response = {
                "message_id": latest_message.id,
                "thread_id": thread_id,
                "content": response_content,
                "created_at": latest_message.created_at
            }
            
            logger.info(f"Retrieved response ({len(response_content)} chars) from message {latest_message.id}")
            return response
            
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except ValueError as e:
            # Re-raise the "no assistant messages" error
            raise
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def create_assistant(
        self,
        system_prompt_path: Optional[str] = None,
        name: str = "Dental Analytics Email Assistant",
        model: str = DEFAULT_MODEL,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Assistant:
        """
        Create a new OpenAI Assistant with the system prompt for dental KPI analysis.
        
        Args:
            system_prompt_path: Optional path to the system prompt file
            name: Name for the assistant
            model: OpenAI model to use for the assistant
            tools: Optional list of tools to enable for the assistant
            
        Returns:
            The created Assistant object
            
        Raises:
            FileNotFoundError: If the system prompt file cannot be found
            PromptValidationError: If the system prompt is invalid
            Various OpenAI API errors if assistant creation fails
        """
        operation = "creating assistant"
        logger.info(f"Starting {operation} with model {model}")
        
        try:
            # Load and validate the system prompt
            system_prompt = load_and_validate_system_prompt(system_prompt_path)
            logger.info(f"Loaded system prompt ({len(system_prompt)} chars)")
            
            # Set up the default tools if none provided
            if tools is None:
                tools = [{"type": "code_interpreter"}]
            
            # Create the assistant
            assistant = self.client.beta.assistants.create(
                name=name,
                model=model,
                instructions=system_prompt,
                tools=tools
            )
            
            logger.info(f"Assistant created successfully with ID: {assistant.id}")
            return assistant
            
        except (FileNotFoundError, PromptValidationError) as e:
            # These errors are already logged by the prompt_loader module
            raise
        except (APIError, APIConnectionError, RateLimitError) as e:
            self.handle_api_error(operation, e)
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {str(e)}")
            raise
    
    def analyze_kpi_data(
        self,
        df: pd.DataFrame,
        assistant_id: str,
        instructions: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        filename: str = "kpi_data.csv"
    ) -> Dict[str, Any]:
        """
        A complete helper function that handles the entire KPI data analysis flow.
        
        Args:
            df: The DataFrame containing KPI data
            assistant_id: The ID of the assistant to use
            instructions: Optional custom instructions for the analysis
            timeout: Maximum time to wait for completion
            filename: Name to use for the uploaded file
            
        Returns:
            A dictionary containing the response and metadata
            
        Raises:
            Various errors from the component functions
        """
        logger.info(f"Starting full KPI data analysis flow with {len(df)} rows")
        
        try:
            # Upload the DataFrame
            file_id = self.upload_dataframe(df, filename)
            logger.info(f"KPI data uploaded with file ID: {file_id}")
            
            # Create a new thread
            thread = self.create_thread()
            thread_id = thread.id
            logger.info(f"Created thread with ID: {thread_id}")
            
            # Add message with the file
            self.add_kpi_analysis_message(thread_id, file_id, instructions)
            logger.info("Added KPI analysis message to thread")
            
            # Run the assistant
            self.run_assistant(thread_id, assistant_id, timeout)
            logger.info("Assistant run completed")
            
            # Get the response
            response = self.get_response(thread_id)
            logger.info(f"Retrieved response with {len(response['content'])} characters")
            
            # Add extra metadata to the response
            response["file_id"] = file_id
            response["assistant_id"] = assistant_id
            
            return response
            
        except Exception as e:
            logger.error(f"Error in KPI data analysis flow: {str(e)}")
            raise
    
    def analyze_kpi_data_with_system_prompt(
        self,
        df: pd.DataFrame,
        system_prompt_path: Optional[str] = None,
        instructions: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        filename: str = "kpi_data.csv"
    ) -> Dict[str, Any]:
        """
        Analyze KPI data by creating a new assistant with the system prompt.
        
        This function combines creating an assistant with the system prompt and
        analyzing KPI data in one convenient method.
        
        Args:
            df: The DataFrame containing KPI data
            system_prompt_path: Optional path to the system prompt file
            instructions: Optional custom instructions for the analysis
            model: OpenAI model to use for the assistant
            timeout: Maximum time to wait for completion
            filename: Name to use for the uploaded file
            
        Returns:
            A dictionary containing the response and metadata
            
        Raises:
            FileNotFoundError: If the system prompt file cannot be found
            PromptValidationError: If the system prompt is invalid
            Various errors from the component functions
        """
        logger.info(f"Starting KPI analysis with system prompt using model {model}")
        
        try:
            # Create a new assistant with the system prompt
            assistant = self.create_assistant(
                system_prompt_path=system_prompt_path,
                model=model
            )
            logger.info(f"Created assistant with ID: {assistant.id}")
            
            # Use the assistant to analyze the data
            response = self.analyze_kpi_data(
                df=df,
                assistant_id=assistant.id,
                instructions=instructions,
                timeout=timeout,
                filename=filename
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in KPI analysis with system prompt: {str(e)}")
            raise 