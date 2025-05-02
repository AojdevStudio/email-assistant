"""
OpenAI Integration Module

This module provides functionality to interact with the OpenAI API,
specifically using the Assistants API for dental KPI analysis.
"""

import os
import time
from typing import Dict, List, Optional, Any, Union

import pandas as pd
from openai import OpenAI
from openai.types.beta.threads import Thread
from openai.types.beta.threads.thread_message import ThreadMessage
from openai.types.beta.threads.run import Run

from src.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Default timeout in seconds for waiting for a run to complete
DEFAULT_TIMEOUT = 300

class OpenAIClient:
    """
    A wrapper around the OpenAI client for working with the Assistants API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
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
        
        # Initialize the client
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI client initialized")
    
    def upload_dataframe(self, df: pd.DataFrame, filename: str = "kpi_data.csv") -> str:
        """
        Upload a DataFrame as a CSV file to OpenAI.
        
        Args:
            df: The DataFrame to upload
            filename: The name to give the file
            
        Returns:
            The file ID assigned by OpenAI
            
        Raises:
            Exception: If there's an error uploading the file
        """
        logger.info(f"Uploading DataFrame with {len(df)} rows as '{filename}'")
        
        try:
            # Convert DataFrame to CSV
            csv_content = df.to_csv(index=False)
            
            # Upload the file
            file_response = self.client.files.create(
                file=csv_content.encode('utf-8'),
                purpose="assistants",
                filename=filename
            )
            
            file_id = file_response.id
            logger.info(f"File uploaded successfully with ID: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
    
    def create_thread(self) -> Thread:
        """
        Create a new thread for the conversation.
        
        Returns:
            The created Thread object
            
        Raises:
            Exception: If there's an error creating the thread
        """
        logger.info("Creating new thread")
        
        try:
            thread = self.client.beta.threads.create()
            logger.info(f"Thread created with ID: {thread.id}")
            return thread
            
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise
    
    def add_message(
        self, 
        thread_id: str, 
        content: str, 
        file_ids: Optional[List[str]] = None
    ) -> ThreadMessage:
        """
        Add a message to the thread.
        
        Args:
            thread_id: The ID of the thread
            content: The content of the message
            file_ids: Optional list of file IDs to attach to the message
            
        Returns:
            The created ThreadMessage object
            
        Raises:
            Exception: If there's an error adding the message
        """
        logger.info(f"Adding message to thread {thread_id}")
        
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
                file_ids=file_ids or []
            )
            
            logger.info(f"Message added with ID: {message.id}")
            return message
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise
    
    def run_assistant(
        self, 
        thread_id: str, 
        assistant_id: str, 
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Run the assistant on the thread and wait for completion.
        
        Args:
            thread_id: The ID of the thread
            assistant_id: The ID of the assistant
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            A dictionary containing the response content
            
        Raises:
            TimeoutError: If the run doesn't complete within the timeout
            Exception: If there's an error running the assistant
        """
        logger.info(f"Running assistant {assistant_id} on thread {thread_id}")
        
        try:
            # Start the run
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            logger.info(f"Run created with ID: {run.id}")
            
            # Poll for completion
            start_time = time.time()
            while True:
                # Check for timeout
                if time.time() - start_time > timeout:
                    error_msg = f"Run timed out after {timeout} seconds"
                    logger.error(error_msg)
                    raise TimeoutError(error_msg)
                
                # Get run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                # Check if run is completed
                if run.status == "completed":
                    logger.info(f"Run completed successfully")
                    break
                
                # Check for failures
                if run.status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Run {run.id} ended with status: {run.status}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # Wait before polling again
                time.sleep(1)
            
            # Get messages (the response)
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            # Parse and return the latest assistant message
            assistant_messages = [
                msg for msg in messages.data 
                if msg.role == "assistant"
            ]
            
            if not assistant_messages:
                error_msg = "No assistant messages found in the thread"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Get the latest message
            latest_message = assistant_messages[0]
            
            # Extract content
            content_parts = []
            for content in latest_message.content:
                if hasattr(content, 'text'):
                    content_parts.append(content.text.value)
            
            response_content = "\n".join(content_parts)
            logger.info(f"Retrieved response with {len(response_content)} characters")
            
            return {
                "message_id": latest_message.id,
                "content": response_content,
                "created_at": latest_message.created_at
            }
            
        except Exception as e:
            logger.error(f"Error running assistant: {str(e)}")
            raise
    
    def process_kpi_data(
        self, 
        df: pd.DataFrame, 
        system_prompt: str,
        benchmark_df: Optional[pd.DataFrame] = None,
        assistant_id: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process KPI data using the OpenAI Assistant and return the response.
        
        This is the main helper function that encapsulates the entire API flow:
        1. Analyze and benchmark KPI data
        2. Sanitize DataFrame data
        3. Upload sanitized data
        4. Create a thread
        5. Add a message with analysis instructions and context
        6. Run the assistant
        7. Extract and return the response
        
        Args:
            df: The DataFrame containing KPI data
            system_prompt: The system prompt to use for the analysis
            benchmark_df: Optional DataFrame containing benchmark definitions
            assistant_id: Optional ID of an existing assistant to use
            seed: Optional random seed for deterministic results
            
        Returns:
            A dictionary containing the response content and analysis results
            
        Raises:
            Various exceptions based on what fails in the process
        """
        try:
            # Import analyzer here to avoid circular imports
            from src.data.analyzer import analyze_kpi_metrics, sanitize_dataframe
            
            # Analyze KPI metrics
            logger.info("Analyzing KPI data against benchmarks")
            analysis_results = analyze_kpi_metrics(df, benchmark_df, seed)
            
            # Sanitize the DataFrame for upload
            logger.info("Sanitizing DataFrame for upload")
            sanitized_df = sanitize_dataframe(df)
            
            # Create assistant if ID not provided
            if not assistant_id:
                logger.info("Creating new assistant")
                assistant = self.client.beta.assistants.create(
                    model="gpt-4o",
                    name="Dental KPI Analyzer",
                    instructions=system_prompt,
                    tools=[{"type": "code_interpreter"}]
                )
                assistant_id = assistant.id
                logger.info(f"Assistant created with ID: {assistant_id}")
            
            # Upload the sanitized DataFrame
            file_id = self.upload_dataframe(sanitized_df)
            
            # Create a thread
            thread = self.create_thread()
            
            # Add a message with the file and analysis context
            message_content = (
                "Please analyze the attached dental KPI data according to the system prompt. "
                f"The data contains {len(df)} rows and {len(df.columns)} columns. "
                f"There are {analysis_results['summary']['metrics_below_target']} metrics below target, "
                f"{analysis_results['summary']['metrics_at_target']} at target, and "
                f"{analysis_results['summary']['metrics_above_target']} above target. "
                f"The following flags have been identified: {', '.join(analysis_results['flags'])}"
            )
            
            self.add_message(
                thread_id=thread.id,
                content=message_content,
                file_ids=[file_id]
            )
            
            # Run the assistant and get the response
            response = self.run_assistant(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            
            # Include the analysis results in the response
            response["analysis_results"] = analysis_results
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing KPI data: {str(e)}")
            raise 