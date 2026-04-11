# scripts/index_knowledge_base.py

import json
import os
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add project root to path
import sys
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.known_providers_db import _RAW_PROVIDER_DATA

def build_irdai_index(chunks_path: str, index_dir: str):
    print("🧠 Loading IRDAI chunks...")
    if not os.path.exists(chunks_path):
        print(f"❌ Chunks file not found at {chunks_path}")
        return

    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"🚀 Embedding {len(chunks)} IRDAI chunks...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, "irdai_rules.index"))
    
    # Save chunks mapping for retrieval
    with open(os.path.join(index_dir, "irdai_chunks_mapping.json"), 'w') as f:
        json.dump(chunks, f)
        
    print(f"✅ IRDAI Index built and saved to {index_dir}")

def build_standard_clauses_index(index_dir: str):
    print("🧠 Building Standard Clauses Index from DB...")
    
    clauses = []
    for provider in _RAW_PROVIDER_DATA:
        insurer = provider.get("insurer")
        policy = provider.get("policy_name", "Standard Plan")
        for c in provider.get("clauses", []):
            clause_text = f"{c.get('title')}: {c.get('description', '')}"
            clauses.append({
                "text": clause_text,
                "metadata": {
                    "insurer": insurer,
                    "policy": policy,
                    "category": c.get("category"),
                    "title": c.get("title")
                }
            })
            
    print(f"🚀 Embedding {len(clauses)} standard clauses...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [c['text'] for c in clauses]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    
    os.makedirs(index_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(index_dir, "standard_clauses.index"))
    
    with open(os.path.join(index_dir, "standard_clauses_mapping.json"), 'w') as f:
        json.dump(clauses, f)
        
    print(f"✅ Standard Clauses Index built and saved to {index_dir}")

if __name__ == "__main__":
    CHUNKS_PATH = os.path.join(project_root, "rag", "processed_chunks", "irdai_chunks.json")
    INDEX_DIR = os.path.join(project_root, "rag", "indices")
    
    build_irdai_index(CHUNKS_PATH, INDEX_DIR)
    build_standard_clauses_index(INDEX_DIR)
