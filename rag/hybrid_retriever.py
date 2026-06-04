"""
CareBridge AI — Dual RAG Hybrid Retriever
==========================================
Provides two independent retrieval surfaces:

  1. irdai_retrieve(query)  → IRDAI Regulations & Master Circulars
  2. clause_retrieve(query) → Standard Clause Industry Benchmarks
  3. retrieve(query)        → Combined (merged + deduplicated)

Architecture:
  - Singleton pattern — indices loaded once at startup
  - FAISS FlatL2 exact search (fine for < 50k chunks)
  - Relevance threshold filtering (L2 distance < 1.2)
  - Source-aware result metadata
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

import numpy as np

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────

_RAG_DIR = Path(__file__).parent
_INDICES  = _RAG_DIR / "indices"

IRDAI_INDEX_PATH    = _INDICES / "irdai_regulations.index"
IRDAI_MAP_PATH      = _INDICES / "irdai_regulations_map.json"
CLAUSE_INDEX_PATH   = _INDICES / "standard_clauses.index"
CLAUSE_MAP_PATH     = _INDICES / "standard_clauses_map.json"

# Legacy paths (v1) — used as fallback if new indices not yet built
_LEGACY_IRDAI_INDEX  = _INDICES / "irdai_rules.index"
_LEGACY_IRDAI_MAP    = _INDICES / "irdai_chunks_mapping.json"
_LEGACY_CLAUSE_INDEX = _INDICES / "standard_clauses.index"
_LEGACY_CLAUSE_MAP   = _INDICES / "standard_clauses_mapping.json"

_RELEVANCE_THRESHOLD = 1.1  # L2 distance on normalized vectors (1.1 approx 0.45 cosine)


# ─────────────────────────────────────────────
# Internal index wrapper
# ─────────────────────────────────────────────

class _FaissIndex:
    """Thin wrapper around a FAISS index + chunk mapping."""

    def __init__(self, index_path: Path, map_path: Path, label: str):
        self.label = label
        self.index = None
        self.chunks: list[str] = []
        self._load(index_path, map_path)

    def _load(self, index_path: Path, map_path: Path):
        if not index_path.exists():
            print(f"  ⚠️  [{self.label}] index not found at {index_path} — will return empty results")
            return
        try:
            import faiss
            self.index = faiss.read_index(str(index_path))
            self.chunks = json.loads(map_path.read_text(encoding="utf-8"))
            print(f"  ✅ [{self.label}] loaded — {len(self.chunks):,} chunks")
        except Exception as e:
            print(f"  ❌ [{self.label}] load error: {e}")

    def retrieve(self, query_vec: np.ndarray, top_k: int = 5) -> list[dict]:
        """
        Return list of {text, score, source} dicts, filtered by threshold.
        """
        if self.index is None or not self.chunks:
            return []

        k = min(top_k * 2, len(self.chunks))
        distances, indices = self.index.search(
            np.array(query_vec, dtype=np.float32), k
        )

        results = []
        seen: set[str] = set()
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or dist > _RELEVANCE_THRESHOLD:
                continue
            chunk = self.chunks[idx]
            if chunk in seen:
                continue
            seen.add(chunk)
            results.append({"text": chunk, "score": float(dist), "source": self.label})
            if len(results) >= top_k:
                break

        return sorted(results, key=lambda x: x["score"])


# ─────────────────────────────────────────────
# Singleton retriever
# ─────────────────────────────────────────────

class HybridRegulatoryRetriever:
    """
    Dual-index semantic retriever.

    Usage:
        r = HybridRegulatoryRetriever()
        r.retrieve("pre-existing disease moratorium")         # combined
        r.irdai_retrieve("waiting period regulation")         # IRDAI only
        r.clause_retrieve("room rent sublimit benchmark")     # clauses only
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        print("🔄 Loading sentence transformer (multi-qa-MiniLM-L6-dot-v1)...")
        self._embed_model = SentenceTransformer("multi-qa-MiniLM-L6-dot-v1")
        print("✅ Embedding model loaded")

        # Load IRDAI index (new path → legacy fallback)
        irdai_idx  = IRDAI_INDEX_PATH  if IRDAI_INDEX_PATH.exists()  else _LEGACY_IRDAI_INDEX
        irdai_map  = IRDAI_MAP_PATH    if IRDAI_MAP_PATH.exists()    else _LEGACY_IRDAI_MAP
        clause_idx = CLAUSE_INDEX_PATH if CLAUSE_INDEX_PATH.exists() else _LEGACY_CLAUSE_INDEX
        clause_map = CLAUSE_MAP_PATH   if CLAUSE_MAP_PATH.exists()   else _LEGACY_CLAUSE_MAP

        self._irdai_index  = _FaissIndex(irdai_idx,  irdai_map,  "IRDAI-Regulations")
        self._clause_index = _FaissIndex(clause_idx, clause_map, "Standard-Clauses")

    def _embed(self, query: str) -> np.ndarray:
        vec = self._embed_model.encode([query])
        import faiss
        faiss.normalize_L2(vec)
        return vec

    # ── Public API ─────────────────────────────

    def irdai_retrieve(self, query: str, top_k: int = 4) -> str:
        """
        Retrieve from IRDAI Regulations index only.
        Returns formatted string for LLM injection.
        """
        vec = self._embed(query)
        results = self._irdai_index.retrieve(vec, top_k)
        return self._format(results, "IRDAI Regulatory Reference")

    def clause_retrieve(self, query: str, top_k: int = 4) -> str:
        """
        Retrieve from Standard Clause Benchmark index only.
        Returns formatted string for LLM injection.
        """
        vec = self._embed(query)
        results = self._clause_index.retrieve(vec, top_k)
        return self._format(results, "Industry Standard Benchmark")

    def retrieve(self, query: str, top_k: int = 5) -> str:
        """
        Combined retrieval from both indices.
        Merges, deduplicates, and selects top results by score.
        Legacy method — compatible with old post_rejection_engine.
        """
        vec = self._embed(query)

        irdai_results  = self._irdai_index.retrieve(vec, top_k)
        clause_results = self._clause_index.retrieve(vec, max(top_k - len(irdai_results), 2))

        # Merge, deduplicate, sort by relevance score (lower L2 = better)
        all_results: list[dict] = []
        seen: set[str] = set()
        for r in irdai_results + clause_results:
            if r["text"] not in seen:
                seen.add(r["text"])
                all_results.append(r)

        all_results = sorted(all_results, key=lambda x: x["score"])[:top_k]

        if not all_results:
            return "No relevant regulatory references found for this query."

        return self._format(all_results, "Regulatory & Benchmark Reference")

    def retrieve_for_rejection(self, rejection_text: str, policy_clause: str = "") -> str:
        """
        Targeted dual retrieval for the rejection audit use-case.
        Pulls IRDAI rules relevant to the rejection + benchmark for the clause.
        """
        irdai_text   = self.irdai_retrieve(rejection_text, top_k=3)
        clause_text  = self.clause_retrieve(
            policy_clause or rejection_text, top_k=2
        )
        return f"{irdai_text}\n\n{clause_text}".strip()

    # ── Formatting ─────────────────────────────

    @staticmethod
    def _format(results: list[dict], header: str) -> str:
        if not results:
            return f"[{header}] No relevant references found."
        lines = [f"[{header}]"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['text'].strip()}")
        return "\n".join(lines)

    @property
    def is_ready(self) -> bool:
        return (
            self._irdai_index.index is not None
            or self._clause_index.index is not None
        )


# ─────────────────────────────────────────────
# Singleton + thread-safe factory
# ─────────────────────────────────────────────

_instance: Optional[HybridRegulatoryRetriever] = None
_lock = threading.Lock()


def get_retriever() -> HybridRegulatoryRetriever:
    """Thread-safe singleton accessor."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = HybridRegulatoryRetriever()
    return _instance