
import os
import sys
import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

def debug_faiss():
    model_name = "multi-qa-MiniLM-L6-dot-v1"
    print(f"🔄 Loading {model_name}...")
    model = SentenceTransformer(model_name)
    
    idx_path = "rag/indices/standard_clauses.index"
    map_path = "rag/indices/standard_clauses_map.json"
    
    print(f"🔄 Loading index: {idx_path}")
    index = faiss.read_index(idx_path)
    chunks = json.loads(Path(map_path).read_text(encoding="utf-8"))
    
    query = "8-year moratorium rule"
    print(f"Query: {query}")
    
    qvec = model.encode([query])
    distances, indices = index.search(np.array(qvec, dtype=np.float32), 5)
    
    print("\nRAW SEARCH RESULTS:")
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1: continue
        print(f"Dist: {dist:.4f} | Chunk: {chunks[idx][:80]}...")

if __name__ == "__main__":
    debug_faiss()
