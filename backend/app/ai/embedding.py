"""Utilities for generating Gemini embeddings used by RAG flows."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
import requests
from requests.adapters import HTTPAdapter

EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
EMBEDDING_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/{EMBEDDING_MODEL}:batchEmbedContents"
)
DOCUMENT_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"
BATCH_SIZE = 32

_SESSION: requests.Session | None = None
_SESSION_LOCK = threading.Lock()


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails."""


@dataclass(frozen=True)
class _EmbeddingRequest:
    text: str
    task_type: str


def _resolve_api_key(explicit_key: str | None = None) -> str:
    api_key = explicit_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "your-gemini-api-key":
        raise EmbeddingError(
            "GOOGLE_API_KEY is not configured. Provide a valid key via the environment or request header."
        )
    return api_key


def _normalize_vector(values: Sequence[float]) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


def _batch(items: list[_EmbeddingRequest], size: int) -> Iterable[list[_EmbeddingRequest]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _get_session() -> requests.Session:
    global _SESSION
    with _SESSION_LOCK:
        if _SESSION is None:
            session = requests.Session()
            adapter = HTTPAdapter(pool_maxsize=20)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            _SESSION = session
        return _SESSION


def _perform_embedding_requests(requests_batch: List[_EmbeddingRequest], api_key: str) -> List[np.ndarray]:
    payload = {
        "requests": [
            {
                "model": EMBEDDING_MODEL,
                "content": {"parts": [{"text": item.text}]},
                "taskType": item.task_type,
            }
            for item in requests_batch
        ]
    }

    try:
        session = _get_session()
        response = session.post(
            EMBEDDING_ENDPOINT,
            params={"key": api_key},
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:  # pragma: no cover - network errors handled below
        raise EmbeddingError(f"Failed to call Gemini embedding API: {exc}") from exc

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = response.text
        raise EmbeddingError(f"Embedding API error {response.status_code}: {error_payload}")

    try:
        data = response.json()
    except ValueError as exc:
        raise EmbeddingError("Failed to parse embedding response as JSON") from exc

    embeddings = data.get("embeddings")
    if not embeddings or len(embeddings) != len(requests_batch):
        raise EmbeddingError(
            "Embedding response missing expected vectors."
        )

    vectors: List[np.ndarray] = []
    for emb in embeddings:
        values = emb.get("values") if isinstance(emb, dict) else None
        if values is None:
            raise EmbeddingError("Embedding response contained an empty vector.")
        vectors.append(_normalize_vector(values))
    return vectors


def _embed(texts: Sequence[str], task_type: str, api_key: str | None = None) -> List[np.ndarray]:
    if not texts:
        return []

    resolved_key = _resolve_api_key(api_key)
    requests_list = [_EmbeddingRequest(text=text, task_type=task_type) for text in texts]

    vectors: List[np.ndarray] = []
    for batch_requests in _batch(requests_list, BATCH_SIZE):
        vectors.extend(_perform_embedding_requests(batch_requests, resolved_key))
    return vectors


def embed_documents(texts: Sequence[str], api_key: str | None = None) -> List[np.ndarray]:
    """Embed document chunks for retrieval."""
    return _embed(texts, DOCUMENT_TASK_TYPE, api_key)


def embed_query(text: str, api_key: str | None = None) -> np.ndarray:
    """Embed a single query string."""
    vectors = _embed([text], QUERY_TASK_TYPE, api_key)
    if not vectors:
        raise EmbeddingError("Embedding API returned no vector for the query.")
    return vectors[0]
