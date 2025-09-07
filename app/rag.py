"""Simple Retrieval-Augmented Generation utilities."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
import requests

from .config import settings


EMBED_DIM = 768


def _hash_embedding(text: str) -> np.ndarray:
    """Deterministic fallback embedding using SHA256 hash."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat hash to fill dimension and convert to float32
    repeated = (h * ((EMBED_DIM // len(h)) + 1))[:EMBED_DIM]
    vec = np.frombuffer(repeated, dtype=np.uint8).astype("float32")
    return vec / np.linalg.norm(vec)


def embed_text(text: str) -> np.ndarray:
    """Embed text using Ollama; fall back to deterministic hash embedding."""
    url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        response = requests.post(
            f"{url}/api/embeddings",
            json={"model": settings.ollama_embed_model, "prompt": text},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return np.array(data["embedding"], dtype="float32")
    except Exception:
        return _hash_embedding(text)


def load_chunks(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class RAGEngine:
    """Lightweight RAG engine with FAISS index and local LLM."""

    def __init__(self) -> None:
        self.index: faiss.Index | None = None
        self.chunks: List[dict] = []
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        index_path = Path(settings.kb_index_path)
        chunks_path = Path(settings.kb_chunks_path)
        if index_path.exists() and chunks_path.exists():
            self.index = faiss.read_index(str(index_path))
            self.chunks = load_chunks(str(chunks_path))

    def search(self, query: str, k: int | None = None) -> List[dict]:
        if not self.index:
            return []
        k = k or settings.top_k
        q_emb = embed_text(query).astype("float32")[None, :]
        scores, idxs = self.index.search(q_emb, k)
        return [self.chunks[i] for i in idxs[0] if i < len(self.chunks)]

    def compose_prompt(self, question: str, chunks: List[dict]) -> str:
        context = "\n\n".join(chunk["text"] for chunk in chunks)
        prompt = (
            "You are a concise assistant that answers ONLY using the provided context.\n"
            'If the answer is not in the context, respond exactly:\n"I don\'t know based on the current knowledge base."\n'
            "Never fabricate or infer beyond the context. Keep answers short and actionable.\n"
            "Context:\n"
            f"{context}\n\n"
            f"User question: {question}\n\nAnswer:"
        )
        return prompt

    def generate(self, prompt: str) -> str:
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        try:
            response = requests.post(
                f"{url}/api/generate",
                json={"model": settings.ollama_llm_model, "prompt": prompt},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception:
            return "I don't know based on the current knowledge base."

    def answer(self, question: str, k: int | None = None) -> Tuple[str, List[str]]:
        chunks = self.search(question, k)
        if not chunks:
            return ("I don't know based on the current knowledge base.", [])
        prompt = self.compose_prompt(question, chunks[: settings.top_m])
        result = self.generate(prompt)
        sources = [c["source"] for c in chunks[: settings.top_m]]
        return result, sources


rag_engine = RAGEngine()
