import json
import re
from typing import List, Dict, Any
from datetime import datetime

def extract_metrics(text: str) -> Dict[str, Any]:
    metrics = {}
    
    # Extract case acceptance percentage if present
    if re.search(r'30-60%|≥ 80%', text):
        metrics['metric_name'] = 'case_acceptance_pct'
    
    # Extract revenue impact if present
    if re.search(r'\$500k-\$1M', text):
        metrics['metric_name'] = 'revenue_impact'
        
    return metrics

def ensure_semantic_header(text: str, section_title: str) -> str:
    """Ensure chunk starts with its semantic header."""
    if not text.startswith('##'):
        return f"## {section_title}\n{text}"
    return text

def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
    # Split the text into sections based on ## headers
    sections = re.split(r'(?=## )', text)
    chunks = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Extract section title if it exists
        title_match = re.match(r'## ([^\n]+)', section)
        section_title = title_match.group(1) if title_match else "Introduction"
        
        # Remove the title from the content
        content = section.replace(f"## {section_title}", "").strip() if title_match else section.strip()
        
        # Split content into smaller chunks if needed
        if len(content) > chunk_size:
            words = content.split()
            current_chunk = []
            current_length = 0
            
            for word in words:
                current_chunk.append(word)
                current_length += len(word) + 1  # +1 for space
                
                if current_length >= chunk_size:
                    chunk_text = " ".join(current_chunk)
                    # Add semantic header to chunk
                    chunk_text = ensure_semantic_header(chunk_text, section_title)
                    
                    # Extract any metrics from the chunk
                    metrics = extract_metrics(chunk_text)
                    
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source": "Case Acceptance Science Research",
                            "section": section_title,
                            "record_type": "research",
                            "benchmark_year": 2025,
                            **metrics,
                            "chunk_size": len(chunk_text),
                            "created_at": datetime.now().isoformat()
                        }
                    })
                    # Keep overlap words for next chunk
                    overlap_words = current_chunk[-int(len(word.split()) * (overlap/chunk_size)):]
                    current_chunk = overlap_words
                    current_length = sum(len(w) + 1 for w in overlap_words)
            
            # Add remaining words as final chunk if any
            if current_chunk:
                final_chunk = " ".join(current_chunk)
                final_chunk = ensure_semantic_header(final_chunk, section_title)
                metrics = extract_metrics(final_chunk)
                
                chunks.append({
                    "text": final_chunk,
                    "metadata": {
                        "source": "Case Acceptance Science Research",
                        "section": section_title,
                        "record_type": "research",
                        "benchmark_year": 2025,
                        **metrics,
                        "chunk_size": len(final_chunk),
                        "created_at": datetime.now().isoformat()
                    }
                })
        else:
            # If content is smaller than chunk_size, add it as is
            content = ensure_semantic_header(content, section_title)
            metrics = extract_metrics(content)
            
            chunks.append({
                "text": content,
                "metadata": {
                    "source": "Case Acceptance Science Research",
                    "section": section_title,
                    "record_type": "research",
                    "benchmark_year": 2025,
                    **metrics,
                    "chunk_size": len(content),
                    "created_at": datetime.now().isoformat()
                }
            })
    
    return chunks

def convert_to_jsonl(input_file: str, output_file: str):
    # Read the input file with utf-8-sig to handle BOM
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Split into chunks
    chunks = split_into_chunks(content)
    
    # Write to JSONL file
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    input_file = "Case Acceptance Science Research_.txt"
    output_file = "case_acceptance_chunks.jsonl"
    convert_to_jsonl(input_file, output_file)
    print(f"Conversion complete. Output saved to {output_file}") 