import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.rag import RAGEngine


def test_compose_prompt():
    engine = RAGEngine()
    chunks = [{"text": "hello world", "source": "a.txt"}]
    prompt = engine.compose_prompt("What?", chunks)
    assert "Context:" in prompt
    assert "hello world" in prompt
    assert "User question" in prompt


def test_answer_without_index_returns_fallback():
    engine = RAGEngine()
    answer, sources = engine.answer("What is up?")
    assert answer == "I don't know based on the current knowledge base."
    assert sources == []
