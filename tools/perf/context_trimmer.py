# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 RNA4219

"""Context trimming utilities for workflow messages."""

from __future__ import annotations

from math import sqrt
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Sequence

_Message = Mapping[str, Any]
_MutableMessage = MutableMapping[str, Any]

_Embedder = Callable[[Sequence[str]], Sequence[Sequence[float]]]


class _TokenCounter:
    """Resolve token counting using tiktoken when available."""

    _MODEL_ALIASES = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
    }

    def __init__(self, model: str) -> None:
        self.model = model
        self._encoder = None
        self._encoding_name: str | None = None
        self._uses_tiktoken = False
        self._load_encoder()

    def _load_encoder(self) -> None:
        resolved = self._MODEL_ALIASES.get(self.model, self.model)
        try:
            import tiktoken  # type: ignore
        except ModuleNotFoundError:
            return
        except Exception:
            return
        try:
            self._encoder = tiktoken.encoding_for_model(resolved)
        except Exception:
            try:
                self._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self._encoder = None
        if self._encoder is not None:
            self._encoding_name = getattr(self._encoder, "name", None)
            self._uses_tiktoken = True

    def count_message(self, message: _Message) -> int:
        content = str(message.get("content", ""))
        base_tokens = 4
        if self._encoder is not None:
            tokens = len(self._encoder.encode(content))
        else:
            tokens = max(1, len(content) // 4 + 1)
        return base_tokens + tokens

    def meta(self) -> Dict[str, Any]:
        strategy = "tiktoken" if self._encoder is not None else "heuristic"
        return {
            "model": self.model,
            "encoding": self._encoding_name,
            "uses_tiktoken": self._uses_tiktoken,
            "strategy": strategy,
        }


def _normalise_messages(messages: Sequence[_Message]) -> List[_MutableMessage]:
    return [dict(message) for message in messages]


def _first_system_message(messages: Iterable[_MutableMessage]) -> tuple[_MutableMessage | None, List[_MutableMessage]]:
    system_message: _MutableMessage | None = None
    remainder: List[_MutableMessage] = []
    for message in messages:
        if message.get("role") == "system" and system_message is None:
            system_message = message
        else:
            remainder.append(message)
    return system_message, remainder


def _join_message_contents(messages: Iterable[_Message]) -> str:
    return " ".join(str(message.get("content", "")) for message in messages).strip()


def _cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float | None:
    if len(vector_a) != len(vector_b) or not vector_a:
        return None
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sqrt(sum(a * a for a in vector_a))
    norm_b = sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return None
    return dot / (norm_a * norm_b)


def _openai_embedder(options: Mapping[str, Any]) -> _Embedder | None:
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None

    client_options = dict(options.get("client_options", {}))
    client = OpenAI(**client_options)
    model = options.get("model") or "text-embedding-3-small"

    def _embed(texts: Sequence[str]) -> List[List[float]]:
        response = client.embeddings.create(model=model, input=list(texts))
        data = getattr(response, "data", [])
        embeddings: List[List[float]] = []
        for item in data:
            embedding = getattr(item, "embedding", None)
            if embedding is None and isinstance(item, Mapping):
                embedding = item.get("embedding")
            if embedding is None:
                continue
            embeddings.append([float(value) for value in embedding])
        return embeddings

    return _embed


def _resolve_embedder(options: Mapping[str, Any]) -> _Embedder | None:
    embedder = options.get("embedder")
    if callable(embedder):
        return embedder
    provider = options.get("provider")
    if provider == "openai":
        return _openai_embedder(options)
    return None


def _semantic_retention(
    original_messages: Sequence[_Message],
    trimmed_messages: Sequence[_Message],
    options: Mapping[str, Any],
) -> float | None:
    if not options:
        return None
    embedder = _resolve_embedder(options)
    if embedder is None:
        return None
    original_text = _join_message_contents(original_messages)
    trimmed_text = _join_message_contents(trimmed_messages)
    if not original_text or not trimmed_text:
        return None
    try:
        embeddings_raw = embedder([original_text, trimmed_text])
    except Exception:
        return None
    embeddings = [list(map(float, vector)) for vector in list(embeddings_raw)[:2]]
    if len(embeddings) < 2:
        return None
    similarity = _cosine_similarity(embeddings[0], embeddings[1])
    return similarity


def trim_messages(
    messages: Sequence[_Message],
    *,
    max_context_tokens: int,
    model: str,
    token_counter: _TokenCounter | None = None,
    semantic_options: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    """Trim messages to satisfy a maximum context token budget."""

    counter = token_counter or _TokenCounter(model)
    mutable_messages = _normalise_messages(messages)
    system_message, remainder = _first_system_message(mutable_messages)
    total_input_tokens = sum(counter.count_message(message) for message in mutable_messages)

    trimmed: List[_MutableMessage] = []
    running_tokens = 0
    if system_message is not None:
        trimmed.append(system_message)
        running_tokens += counter.count_message(system_message)

    kept: List[_MutableMessage] = []
    for message in reversed(remainder):
        tokens = counter.count_message(message)
        if running_tokens + tokens <= max_context_tokens or not kept:
            kept.append(message)
            running_tokens += tokens
    kept.reverse()
    trimmed.extend(kept)

    output_tokens = sum(counter.count_message(message) for message in trimmed)
    compression_ratio = 1.0 if total_input_tokens == 0 else output_tokens / total_input_tokens

    statistics: Dict[str, Any] = {
        "compression_ratio": compression_ratio,
        "input_tokens": total_input_tokens,
        "output_tokens": output_tokens,
    }

    semantic_retention = _semantic_retention(mutable_messages, trimmed, semantic_options or {})
    if semantic_options is not None:
        statistics["semantic_retention"] = semantic_retention

    return {
        "messages": trimmed,
        "statistics": statistics,
        "token_counter": counter.meta(),
        "semantic_options": dict(semantic_options or {}),
    }
