"""AI integration helpers for embedding generation."""

from .embedding import (
    EmbeddingError,
    embed_documents,
    embed_query,
)

__all__ = [
    "EmbeddingError",
    "embed_documents",
    "embed_query",
]
