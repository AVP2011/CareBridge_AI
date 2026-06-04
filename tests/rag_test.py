
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[1]))

from rag.hybrid_retriever import get_retriever

def test_rag_retrieval():
    print("🔄 Testing RAG Retrieval...")
    try:
        retriever = get_retriever()
        
        # Query about moratorium
        query = "What is the 8-year moratorium rule for health insurance?"
        print(f"Query: {query}")
        
        result = retriever.retrieve(query)
        
        print("\nRETRIEVED CONTEXT:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        # Check if we got anything related to 8 years or moratorium
        success = "8" in result or "moratorium" in result.lower() or "eight" in result.lower()
        
        if success:
            print("✅ RAG Retrieval Verified.")
        else:
            print("❌ RAG Retrieval Failed to find relevant context.")
            print(f"Result snippet: {result[:200]}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error during RAG test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_rag_retrieval()
