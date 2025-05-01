import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def upload_to_vectorstore(file_path):
    # Get API key from environment variable or prompt user
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
    
    try:
        print(f"Step 1: Uploading {file_path} to OpenAI files...")
        # First upload the file to OpenAI
        with open(file_path, "rb") as file:
            files = {"file": file}
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.post(
                "https://api.openai.com/v1/files",
                headers=headers,
                files=files,
                data={"purpose": "assistants"}
            )
            
            if response.status_code != 200:
                print(f"Error uploading file: {response.text}")
                return
                
            file_id = response.json()["id"]
            print(f"File uploaded successfully with ID: {file_id}")
            
        print("\nStep 2: Adding file to vector store...")
        # Add the file to the vector store
        vector_store_id = "vs_68139e9fcd1081918e742a34439c1a93"
        response = requests.post(
            f"https://api.openai.com/v1/vector_stores/{vector_store_id}/files",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"file_id": file_id}
        )
        
        if response.status_code == 200:
            print("Success! File has been added to the vector store.")
        else:
            print(f"Error: Failed to add file to vector store. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Upload the KPI metrics
    upload_to_vectorstore("dental_kpi_metrics.txt") 