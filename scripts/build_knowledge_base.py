# scripts/build_knowledge_base.py

import os
import json
from pathlib import Path
from typing import List, Dict
import re

# Add the project root to sys.path to import services
import sys
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.pdf_extractor_robust import RobustPDFExtractor

def chunk_text(text: str, source_name: str, chunk_size: int = 800, overlap: int = 150) -> List[Dict]:
    """
    Split text into overlapping chunks while trying to preserve context.
    """
    # Remove excessive newlines but keep some structure
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to find a good breaking point (end of sentence or paragraph)
        if end < text_len:
            # Look for last period or newline in the last 100 chars of the chunk
            search_window = text[max(start, end-100):end]
            break_point = max(search_window.rfind('.'), search_window.rfind('\n'))
            if break_point != -1:
                end = max(start, end - (100 - break_point))
        
        chunk_text = text[start:end].strip()
        if len(chunk_text) > 50:  # Skip very small fragments
            chunks.append({
                "text": chunk_text,
                "source": source_name,
                "metadata": {
                    "start_char": start,
                    "end_char": end,
                    "source_file": source_name
                }
            })
            
        start = end - overlap
        if start < 0: start = 0
        if end >= text_len: break
        
    return chunks

def process_all_policies(input_dir: str, output_path: str):
    extractor = RobustPDFExtractor()
    input_path = Path(input_dir)
    all_chunks = []
    
    if not input_path.exists():
        print(f"❌ Input directory {input_dir} not found.")
        return

    pdf_files = list(input_path.glob("*.pdf"))
    print(f"📂 Found {len(pdf_files)} PDFs to process.")
    
    for pdf_file in pdf_files:
        print(f"📄 Processing {pdf_file.name}...")
        try:
            text, method = extractor.extract_text(str(pdf_file))
            chunks = chunk_text(text, pdf_file.name)
            all_chunks.extend(chunks)
            print(f"✅ Extracted {len(chunks)} chunks using {method}")
        except Exception as e:
            print(f"❌ Failed to process {pdf_file.name}: {e}")
            
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
        
    print(f"\n✨ Knowledge base built with {len(all_chunks)} total chunks.")
    print(f"💾 Saved to: {output_path}")

if __name__ == "__main__":
    INPUT_DIR = os.path.join(project_root, "imp policies")
    OUTPUT_PATH = os.path.join(project_root, "rag", "processed_chunks", "irdai_chunks.json")
    process_all_policies(INPUT_DIR, OUTPUT_PATH)
