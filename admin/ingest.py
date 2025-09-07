"""Minimal ingestion script to build FAISS index from files in admin/kb."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import faiss
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
import numpy as np

from app.rag import EMBED_DIM, embed_text
from app.config import settings


KB_DIR = Path(__file__).parent / "kb"


def load_files() -> List[dict]:
    chunks = []
    for path in KB_DIR.glob("**/*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            chunks.append({"text": text.strip(), "source": path.name})
    return chunks


def ingest() -> None:
    chunks = load_files()
    if not chunks:
        raise RuntimeError("No files found in admin/kb")
    embeddings = [embed_text(c["text"]) for c in chunks]
    matrix = np.stack(embeddings).astype("float32")
    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(matrix)
    faiss.write_index(index, settings.kb_index_path)
    with open(settings.kb_chunks_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")


if __name__ == "__main__":
    ingest()
