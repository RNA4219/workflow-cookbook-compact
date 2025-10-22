"""tests for tools.perf.context_trimmer"""

from __future__ import annotations

from math import sqrt
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
import importlib
import sys

import pytest


def _reload_context_trimmer(fake_tiktoken: Any | None) -> Any:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    for name in list(sys.modules):
        if name.startswith("tools.perf.context_trimmer"):
            sys.modules.pop(name)
    if fake_tiktoken is None:
        sys.modules.pop("tiktoken", None)
    else:
        sys.modules["tiktoken"] = fake_tiktoken
    return importlib.import_module("tools.perf.context_trimmer")


def _messages() -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": "stay concise"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
        {"role": "user", "content": "tell me more"},
    ]


def test_trim_messages_preserves_first_system(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)
    messages = [
        {"role": "system", "content": "original"},
        {"role": "user", "content": "question"},
        {"role": "system", "content": "should drop"},
        {"role": "assistant", "content": "answer"},
    ]
    result = module.trim_messages(messages, max_context_tokens=12, model="fake")
    trimmed = result["messages"]
    assert trimmed[0]["role"] == "system"
    assert trimmed[0]["content"] == "original"
    assert sum(1 for m in trimmed if m["role"] == "system") == 1


def test_trim_messages_counts_tokens_with_tiktoken() -> None:
    fake_encoding = SimpleNamespace(
        name="fake-encoding",
        encode=lambda text: [1] * len(text.split()),
    )
    fake_tiktoken = SimpleNamespace(
        encoding_for_model=lambda model: fake_encoding,
        get_encoding=lambda name: fake_encoding,
    )
    module = _reload_context_trimmer(fake_tiktoken=fake_tiktoken)
    result = module.trim_messages(_messages(), max_context_tokens=100, model="test-model")
    stats = result["statistics"]
    assert stats["input_tokens"] == stats["output_tokens"] == 4 * len(_messages()) + sum(
        len(message["content"].split()) for message in _messages()
    )
    assert result["token_counter"]["uses_tiktoken"] is True
    assert result["token_counter"]["encoding"] == "fake-encoding"


def test_trim_messages_counts_tokens_without_tiktoken() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)
    result = module.trim_messages(_messages(), max_context_tokens=100, model="test-model")
    stats = result["statistics"]
    assert stats["input_tokens"] == stats["output_tokens"]
    expected = sum(max(1, len(m["content"]) // 4 + 1) + 4 for m in _messages())
    assert stats["output_tokens"] == expected
    assert result["token_counter"]["uses_tiktoken"] is False


def test_trim_messages_computes_semantic_retention_with_embedder() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)

    def embedder(texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            tokens = text.split()
            vowels = sum(1 for ch in text.lower() if ch in "aeiou")
            consonants = sum(1 for ch in text.lower() if ch in "bcdfghjklmnpqrstvwxyz")
            vectors.append([float(len(tokens)), float(vowels), float(consonants)])
        return vectors

    messages = [
        {"role": "system", "content": "retain guidance"},
        {"role": "user", "content": "alpha beta gamma delta"},
        {"role": "assistant", "content": "epsilon zeta eta theta"},
    ]
    result = module.trim_messages(
        messages,
        max_context_tokens=18,
        model="test-model",
        semantic_options={"embedder": embedder},
    )

    stats = result["statistics"]
    assert "semantic_retention" in stats
    original_text = " ".join(message["content"] for message in messages)
    trimmed_text = " ".join(message["content"] for message in result["messages"])

    expected_vectors = embedder([original_text, trimmed_text])
    numerator = sum(a * b for a, b in zip(expected_vectors[0], expected_vectors[1]))
    denominator = sqrt(sum(a * a for a in expected_vectors[0])) * sqrt(
        sum(b * b for b in expected_vectors[1])
    )
    expected_similarity = numerator / denominator

    assert stats["semantic_retention"] == pytest.approx(expected_similarity)
    assert result["semantic_options"]["embedder"] is embedder
