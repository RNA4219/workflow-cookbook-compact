"""tests for tools.perf.context_trimmer"""

from __future__ import annotations

import importlib
import sys
from itertools import zip_longest
from math import sqrt
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List

import pytest


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _reload_context_trimmer(fake_tiktoken: Any | None) -> Any:
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


def _messages_text(messages: Iterable[Dict[str, Any]]) -> str:
    return "\n".join(str(message.get("content", "")) for message in messages)


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
    assert "compress_ratio" in stats
    assert stats["compress_ratio"] == pytest.approx(stats["compression_ratio"])
    assert stats["input_tokens"] == stats["output_tokens"] == 4 * len(_messages()) + sum(
        len(message["content"].split()) for message in _messages()
    )
    assert stats["compress_ratio"] == pytest.approx(stats["compression_ratio"])
    assert result["token_counter"]["uses_tiktoken"] is True
    assert result["token_counter"]["encoding"] == "fake-encoding"


def test_trim_messages_counts_tokens_without_tiktoken() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)
    result = module.trim_messages(_messages(), max_context_tokens=100, model="test-model")
    stats = result["statistics"]
    assert "compress_ratio" in stats
    assert stats["input_tokens"] == stats["output_tokens"]
    expected = sum(max(1, len(m["content"]) // 4 + 1) + 4 for m in _messages())
    assert stats["output_tokens"] == expected
    assert stats["compress_ratio"] == pytest.approx(stats["compression_ratio"])
    assert result["token_counter"]["uses_tiktoken"] is False


def test_trim_messages_reports_legacy_compression_ratio_key() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)
    messages = _messages()
    result = module.trim_messages(messages, max_context_tokens=100, model="test-model")
    stats = result["statistics"]

    assert list(stats)[:4] == [
        "compress_ratio",
        "compression_ratio",
        "input_tokens",
        "output_tokens",
    ]

    expected_tokens = sum(max(1, len(m["content"]) // 4 + 1) + 4 for m in messages)
    assert stats["input_tokens"] == expected_tokens
    assert stats["output_tokens"] == expected_tokens
    assert stats["compress_ratio"] == pytest.approx(1.0)
    assert stats["compression_ratio"] == pytest.approx(stats["compress_ratio"])


def test_trim_messages_records_semantic_retention() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)

    def embedder(text: str) -> List[float]:
        return [float(len(text)) or 1.0]

    result = module.trim_messages(
        _messages(),
        max_context_tokens=12,
        model="test-model",
        semantic_options={"embedder": embedder},
    )

    retention = result["statistics"]["semantic_retention"]
    assert 0.0 <= retention <= 1.0


def test_trim_messages_semantic_retention_matches_cosine_similarity() -> None:
    module = _reload_context_trimmer(fake_tiktoken=None)

    def embedder(text: str) -> List[float]:
        return [float(len(text)), float(len(text) % 3 + 1)]

    messages = _messages()
    result = module.trim_messages(
        messages,
        max_context_tokens=12,
        model="test-model",
        semantic_options={"embedder": embedder},
    )

    trimmed_messages = result["messages"]
    retention = result["statistics"]["semantic_retention"]
    assert isinstance(retention, float)
    assert 0.0 <= retention <= 1.0

    original_vector = [float(value) for value in embedder(_messages_text(messages))]
    trimmed_vector = [float(value) for value in embedder(_messages_text(trimmed_messages))]

    dot_product = sum(x * y for x, y in zip_longest(original_vector, trimmed_vector, fillvalue=0.0))
    norm_original = sqrt(sum(x * x for x in original_vector))
    norm_trimmed = sqrt(sum(y * y for y in trimmed_vector))

    if norm_original == 0.0 and norm_trimmed == 0.0:
        expected = 1.0
    elif norm_original == 0.0 or norm_trimmed == 0.0:
        expected = 0.0
    else:
        expected = dot_product / (norm_original * norm_trimmed)

    expected = max(0.0, min(1.0, expected))
    assert retention == pytest.approx(expected)
