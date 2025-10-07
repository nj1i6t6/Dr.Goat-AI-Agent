"""Lightweight in-memory vector store for RAG retrieval."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .ai import EmbeddingError, embed_query

try:  # pragma: no cover - import tested indirectly via search path
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency fallback
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_VECTOR_PATH = _REPO_ROOT / "docs" / "rag_vectors" / "corpus.parquet"

_VECTOR_CACHE: List[Dict[str, object]] = []
_VECTOR_MTIME: float | None = None
_VECTOR_LOCK = threading.Lock()
_VECTOR_MISSING_WARNED = False
_FAISS_INDEX: "faiss.Index" | None = None  # type: ignore[name-defined]
_EMBEDDING_MATRIX: np.ndarray | None = None
_FAISS_UNAVAILABLE_WARNED = False


def load_vectors(path: str | os.PathLike[str] = _DEFAULT_VECTOR_PATH) -> List[Dict[str, object]]:
    """Load vectors from a parquet file into memory."""
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(resolved_path)

    df = pd.read_parquet(resolved_path)
    required_columns = {"doc_path", "chunk_index", "text", "embedding"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in vector store: {missing}")

    vectors: List[Dict[str, object]] = []
    for row in df.itertuples(index=False):
        embedding_values = getattr(row, "embedding")
        vector = np.asarray(embedding_values, dtype=np.float32)
        meta = getattr(row, "meta", {})
        vectors.append(
            {
                "text": getattr(row, "text"),
                "embedding": vector,
                "doc": getattr(row, "doc_path"),
                "idx": int(getattr(row, "chunk_index")),
                "meta": meta if isinstance(meta, dict) else _safe_json(meta),
            }
        )
    return vectors


def ensure_vectors(path: str | os.PathLike[str] = _DEFAULT_VECTOR_PATH) -> List[Dict[str, object]]:
    """Ensure vectors are loaded into memory, pulling from Git LFS if required."""
    global _VECTOR_CACHE, _VECTOR_MTIME, _VECTOR_MISSING_WARNED
    resolved_path = Path(path)

    with _VECTOR_LOCK:
        if resolved_path.exists():
            mtime = resolved_path.stat().st_mtime
            if _VECTOR_MTIME != mtime:
                try:
                    _VECTOR_CACHE = load_vectors(resolved_path)
                    _rebuild_index(_VECTOR_CACHE)
                    _VECTOR_MTIME = mtime
                    _VECTOR_MISSING_WARNED = False
                    LOGGER.info("Loaded %s RAG chunks from %s", len(_VECTOR_CACHE), resolved_path)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.error("Failed to load RAG vectors from %s: %s", resolved_path, exc)
                    _clear_cache()
            return _VECTOR_CACHE

        # File missing; attempt to pull from Git LFS once.
        if not _VECTOR_MISSING_WARNED:
            _attempt_git_lfs_pull()
            if resolved_path.exists():
                try:
                    _VECTOR_CACHE = load_vectors(resolved_path)
                    _rebuild_index(_VECTOR_CACHE)
                    _VECTOR_MTIME = resolved_path.stat().st_mtime
                    _VECTOR_MISSING_WARNED = False
                    LOGGER.info("Loaded %s RAG chunks from %s", len(_VECTOR_CACHE), resolved_path)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.error("Failed to load RAG vectors from %s after git lfs pull: %s", resolved_path, exc)
                    _clear_cache()
            if not resolved_path.exists():
                LOGGER.warning("RAG vectors missing – fallback to no-context mode")
                _VECTOR_MISSING_WARNED = True
        return _VECTOR_CACHE


def rag_query(
    query: str,
    top_k: int = 5,
    min_sim: float = 0.75,
    api_key: str | None = None,
) -> List[Dict[str, object]]:
    """Return the top matching chunks for the provided query string."""
    if not query:
        return []

    vectors = ensure_vectors()
    if not vectors:
        return []

    try:
        query_vector = embed_query(query, api_key=api_key)
    except EmbeddingError as exc:
        LOGGER.warning("Failed to embed query for RAG lookup: %s", exc)
        return []

    if not _FAISS_AVAILABLE:
        return _linear_search(query_vector, vectors, top_k=top_k, min_sim=min_sim)

    index = _FAISS_INDEX
    embeddings = _EMBEDDING_MATRIX
    if index is None or embeddings is None:
        return []

    query_vector = np.asarray(query_vector, dtype=np.float32)
    faiss.normalize_L2(query_vector.reshape(1, -1))

    search_k = min(len(vectors), max(top_k * 2, top_k))
    distances, indices = index.search(query_vector.reshape(1, -1), search_k)

    results: List[Dict[str, object]] = []
    for score, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        if score < min_sim:
            continue
        item = vectors[idx]
        results.append(
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "score": float(score),
                "meta": item.get("meta", {}),
            }
        )
        if len(results) >= top_k:
            break

    return results


def _safe_json(value: object) -> Dict[str, object]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:  # pragma: no cover - best effort conversion
        return {"raw": value}


def _attempt_git_lfs_pull() -> None:
    repo_root = _REPO_ROOT
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return

    try:
        commands = (["git", "lfs", "install", "--local"], ["git", "lfs", "pull"])
        for cmd_args in commands:
            result = subprocess.run(
                cmd_args,
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                LOGGER.warning(
                    "Command '%s' failed with code %s: %s",
                    " ".join(cmd_args),
                    result.returncode,
                    stderr,
                )
                break
    except FileNotFoundError:  # pragma: no cover - git not available in some envs
        LOGGER.warning("git or git-lfs not available; cannot pull RAG vectors")


def _rebuild_index(vectors: List[Dict[str, object]]) -> None:
    """Build or refresh the FAISS index from in-memory vectors."""
    global _FAISS_INDEX, _EMBEDDING_MATRIX
    if not vectors:
        _FAISS_INDEX = None
        _EMBEDDING_MATRIX = None
        return

    embeddings = np.vstack([item["embedding"] for item in vectors]).astype(np.float32)
    if _FAISS_AVAILABLE:
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        _FAISS_INDEX = index
    else:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        embeddings = embeddings / norms
        _FAISS_INDEX = None
    _EMBEDDING_MATRIX = embeddings


def _clear_cache() -> None:
    global _VECTOR_CACHE, _VECTOR_MTIME, _FAISS_INDEX, _EMBEDDING_MATRIX
    _VECTOR_CACHE = []
    _VECTOR_MTIME = None
    _FAISS_INDEX = None
    _EMBEDDING_MATRIX = None


def _linear_search(
    query_vector: np.ndarray,
    vectors: List[Dict[str, object]],
    *,
    top_k: int,
    min_sim: float,
) -> List[Dict[str, object]]:
    """Fallback cosine similarity search when FAISS is unavailable."""
    global _FAISS_UNAVAILABLE_WARNED
    if not _FAISS_UNAVAILABLE_WARNED:
        LOGGER.warning(
            "faiss-cpu not available; using linear scan fallback. Install the dependency for better RAG performance."
        )
        _FAISS_UNAVAILABLE_WARNED = True

    if not vectors:
        return []

    embeddings = _EMBEDDING_MATRIX
    if embeddings is None:
        embeddings = np.vstack([item["embedding"] for item in vectors]).astype(np.float32)
    query = np.asarray(query_vector, dtype=np.float32)
    norm = np.linalg.norm(query)
    if norm > 0:
        query = query / norm

    scores = embeddings @ query
    top_indices = np.argsort(scores)[::-1]

    results: List[Dict[str, object]] = []
    for idx in top_indices:
        score = float(scores[idx])
        if score < min_sim:
            continue
        item = vectors[int(idx)]
        results.append(
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "score": score,
                "meta": item.get("meta", {}),
            }
        )
        if len(results) >= top_k:
            break

    return results
