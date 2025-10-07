"""Shared helpers for preparing Retrieval-Augmented Generation inputs."""
from __future__ import annotations

from pathlib import Path
from typing import List

SUPPORTED_EXTENSIONS = {".md", ".txt"}
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100


def iter_source_files(source_dir: Path) -> List[Path]:
    """Return all supported files under the given directory, sorted by path."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    files = [
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def read_text(file_path: Path) -> str:
    """Read a supported text document as UTF-8."""
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported extension: {file_path.suffix}."
            " TODO: add PDF support without blocking generation."
        )
    return file_path.read_text(encoding="utf-8")


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split text into overlapping windows of roughly ``chunk_size`` characters."""
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    length = len(text)
    step = max(chunk_size - overlap, 1)

    while start < length:
        end = min(length, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
