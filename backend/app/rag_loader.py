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

LOGGER = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_VECTOR_PATH = _REPO_ROOT / "docs" / "rag_vectors" / "corpus.parquet"

_VECTOR_CACHE: List[Dict[str, object]] = []
_VECTOR_MTIME: float | None = None
_VECTOR_LOCK = threading.Lock()
_VECTOR_MISSING_WARNED = False


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
                    _VECTOR_MTIME = mtime
                    _VECTOR_MISSING_WARNED = False
                    LOGGER.info("Loaded %s RAG chunks from %s", len(_VECTOR_CACHE), resolved_path)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.error("Failed to load RAG vectors from %s: %s", resolved_path, exc)
                    _VECTOR_CACHE = []
                    _VECTOR_MTIME = None
            return _VECTOR_CACHE

        # File missing; attempt to pull from Git LFS once.
        if not _VECTOR_MISSING_WARNED:
            _attempt_git_lfs_pull()
            if resolved_path.exists():
                try:
                    _VECTOR_CACHE = load_vectors(resolved_path)
                    _VECTOR_MTIME = resolved_path.stat().st_mtime
                    _VECTOR_MISSING_WARNED = False
                    LOGGER.info("Loaded %s RAG chunks from %s", len(_VECTOR_CACHE), resolved_path)
                except Exception as exc:  # pragma: no cover - defensive logging
                    LOGGER.error("Failed to load RAG vectors from %s after git lfs pull: %s", resolved_path, exc)
                    _VECTOR_CACHE = []
                    _VECTOR_MTIME = None
            if not resolved_path.exists():
                LOGGER.warning("RAG vectors missing – fallback to no-context mode")
                _VECTOR_MISSING_WARNED = True
        return _VECTOR_CACHE


def rag_query(query: str, top_k: int = 5, min_sim: float = 0.75) -> List[Dict[str, object]]:
    """Return the top matching chunks for the provided query string."""
    if not query:
        return []

    vectors = ensure_vectors()
    if not vectors:
        return []

    try:
        query_vector = embed_query(query)
    except EmbeddingError as exc:
        LOGGER.warning("Failed to embed query for RAG lookup: %s", exc)
        return []

    scores: List[Dict[str, object]] = []
    for item in vectors:
        vector = item["embedding"]
        score = float(np.dot(query_vector, vector))
        if score < min_sim:
            continue
        scores.append(
            {
                "text": item["text"],
                "doc": item["doc"],
                "idx": item["idx"],
                "score": score,
                "meta": item.get("meta", {}),
            }
        )

    scores.sort(key=lambda chunk: chunk["score"], reverse=True)
    return scores[:top_k]


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
        commands = (["git", "lfs", "install"], ["git", "lfs", "pull"])
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
                LOGGER.warning("Command '%s' failed with code %s: %s", " ".join(cmd_args), result.returncode, stderr)
    except FileNotFoundError:  # pragma: no cover - git not available in some envs
        LOGGER.warning("git or git-lfs not available; cannot pull RAG vectors")
