# rag/irdai_retriever.py

import faiss
import json
import os
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pathlib import Path

class IRDAIRetriever:
    def __init__(self, index_dir: str):
        self.index_path = os.path.join(index_dir, "irdai_rules.index")
        self.mapping_path = os.path.join(index_dir, "irdai_chunks_mapping.json")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load index and mapping
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path, 'r') as f:
            self.chunks = json.load(f)

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve top-k relevant IRDAI regulatory chunks.
        """
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                results.append({
                    "text": self.chunks[idx]['text'],
                    "source": self.chunks[idx]['source'],
                    "score": float(dist)
                })
        return results

# rag/standard_clause_retriever.py

class StandardClauseRetriever:
    def __init__(self, index_dir: str):
        self.index_path = os.path.join(index_dir, "standard_clauses.index")
        self.mapping_path = os.path.join(index_dir, "standard_clauses_mapping.json")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load index and mapping
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path, 'r') as f:
            self.clauses = json.load(f)

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve top-k similar clauses from other policies.
        """
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                results.append({
                    "text": self.clauses[idx]['text'],
                    "metadata": self.clauses[idx]['metadata'],
                    "score": float(dist)
                })
        return results
