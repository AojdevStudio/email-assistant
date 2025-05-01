import json

def convert_jsonl_to_text():
    input_file = "case_acceptance_chunks.jsonl"
    output_file = "case_acceptance_content.txt"
    
    print(f"Converting {input_file} to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                try:
                    # Parse each JSON line
                    data = json.loads(line.strip())
                    
                    # Extract the text content - assuming it's in a 'text' or 'content' field
                    # Adjust these field names based on your JSONL structure
                    content = data.get('text', data.get('content', ''))
                    
                    if content:
                        # Write the content with a separator
                        outfile.write(content + "\n\n---\n\n")
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                except Exception as e:
                    print(f"Error processing line: {e}")
    
    print("Conversion complete!")

if __name__ == "__main__":
    convert_jsonl_to_text() 