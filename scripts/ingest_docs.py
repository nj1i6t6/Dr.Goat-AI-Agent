"""Convert docs/rag_sources/ documents into normalized Gemini embeddings."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.ai import EmbeddingError, embed_documents  # noqa: E402

SOURCE_DIR = REPO_ROOT / "docs" / "rag_sources"
TARGET_PATH = REPO_ROOT / "docs" / "rag_vectors" / "corpus.parquet"
SUPPORTED_EXTENSIONS = {".md", ".txt"}
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def iter_source_files() -> List[Path]:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source directory not found: {SOURCE_DIR}")
    files = [p for p in SOURCE_DIR.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def read_text(file_path: Path) -> str:
    if file_path.suffix.lower() in {".md", ".txt"}:
        return file_path.read_text(encoding='utf-8')
    raise ValueError(f"Unsupported extension: {file_path.suffix}. TODO: add PDF support without blocking generation.")


def chunk_text(text: str) -> List[str]:
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + CHUNK_SIZE)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
        if start < 0:
            break
    return chunks


def build_records(files: List[Path]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for file_path in files:
        rel_path = file_path.relative_to(REPO_ROOT)
        text = read_text(file_path)
        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            records.append(
                {
                    "doc_path": str(rel_path),
                    "chunk_index": idx,
                    "text": chunk,
                    "meta": {"source": str(rel_path)},
                }
            )
    return records


def embed_records(records: List[Dict[str, object]]) -> None:
    texts = [record["text"] for record in records]
    embeddings = embed_documents(texts)
    if len(embeddings) != len(records):
        raise RuntimeError("Mismatch between generated embeddings and records")
    for record, vector in zip(records, embeddings):
        record["embedding"] = vector.astype(float).tolist()


def save_vectors(records: List[Dict[str, object]]) -> None:
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records, columns=["doc_path", "chunk_index", "text", "embedding", "meta"])
    df.to_parquet(TARGET_PATH, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RAG vectors from project documentation.")
    parser.add_argument("--source", type=str, default=str(SOURCE_DIR), help="Directory containing source documents")
    parser.add_argument("--output", type=str, default=str(TARGET_PATH), help="Parquet file path to write")
    args = parser.parse_args()

    source_dir = Path(args.source)
    output_path = Path(args.output)

    global SOURCE_DIR, TARGET_PATH
    SOURCE_DIR = source_dir
    TARGET_PATH = output_path

    try:
        files = iter_source_files()
        if not files:
            print("No source documents found; nothing to embed.")
            return 0
        records = build_records(files)
        embed_records(records)
        save_vectors(records)
        print(f"saved: {TARGET_PATH} ({len(records)} chunks)")
        return 0
    except (EmbeddingError, FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
