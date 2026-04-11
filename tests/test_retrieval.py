# tests/test_retrieval.py

import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from rag.retrievers import IRDAIRetriever, StandardClauseRetriever

def test_irdai_retrieval():
    print("\n--- Testing IRDAI Knowledge Base Retrieval ---")
    rag_dir = os.path.join(project_root, "rag", "indices")
    
    try:
        retriever = IRDAIRetriever(rag_dir)
        query = "What are the rules for waiting periods in health insurance?"
        results = retriever.retrieve(query, k=3)
        
        print(f"Query: {query}")
        print(f"Found {len(results)} relevant IRDAI snippets:")
        for i, res in enumerate(results):
            print(f"\n[{i+1}] Source: {res['source']}")
            print(f"Text Snippet: {res['text'][:200]}...")
            
        if len(results) > 0:
            print("\n✅ IRDAI Retrieval SUCCESS")
        else:
            print("\n❌ IRDAI Retrieval FAILED (No results found)")
            
    except Exception as e:
        print(f"❌ Error during IRDAI retrieval: {e}")

def test_market_retrieval():
    print("\n--- Testing Market Standards (Standard Clauses) Retrieval ---")
    rag_dir = os.path.join(project_root, "rag", "indices")
    
    try:
        retriever = StandardClauseRetriever(rag_dir)
        query = "Room rent sublimits in Star Health or HDFC policies"
        results = retriever.retrieve(query, k=2)
        
        print(f"Query: {query}")
        print(f"Found {len(results)} relevant market benchmarks:")
        for i, res in enumerate(results):
            print(f"\n[{i+1}] Insurer: {res['metadata']['insurer']}")
            print(f"Text Snippet: {res['text'][:200]}...")
            
        if len(results) > 0:
            print("\n✅ Market Retrieval SUCCESS")
        else:
            print("\n❌ Market Retrieval FAILED")
            
    except Exception as e:
        print(f"❌ Error during Market retrieval: {e}")

if __name__ == "__main__":
    if not os.path.exists(os.path.join(project_root, "rag", "indices", "irdai_rules.index")):
        print("❌ FAISS indices not found! Please run Phase 2 indexing first.")
    else:
        test_irdai_retrieval()
        test_market_retrieval()
