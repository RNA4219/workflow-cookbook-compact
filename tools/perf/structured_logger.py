"""Structured logging helpers for inference metrics."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

JsonValue = Any


def _normalise_value(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {str(key): _normalise_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise_value(item) for item in value]
    return value


@dataclass(slots=True)
class InferenceLogRecord:
    """Represents a single Katamari-compatible inference log entry."""

    session_id: str | None = None
    project: str | None = None
    metrics: Mapping[str, JsonValue] | None = None
    metadata: Mapping[str, JsonValue] | None = None
    tags: Mapping[str, JsonValue] | None = None
    extra: Mapping[str, JsonValue] | None = None

    def as_json(self) -> dict[str, JsonValue]:
        payload: dict[str, JsonValue] = {}
        if self.session_id is not None:
            payload["session_id"] = self.session_id
        if self.project is not None:
            payload["project"] = self.project
        if self.metrics:
            payload["metrics"] = {
                str(key): _normalise_value(value) for key, value in self.metrics.items()
            }
        if self.metadata:
            payload["metadata"] = {
                str(key): _normalise_value(value) for key, value in self.metadata.items()
            }
        if self.tags:
            payload["tags"] = {
                str(key): _normalise_value(value) for key, value in self.tags.items()
            }
        if self.extra:
            payload.update({str(key): _normalise_value(value) for key, value in self.extra.items()})
        return payload


class StructuredLogger:
    """Katamari-compatible structured logger that writes JSON Lines."""

    def __init__(self, log_path: Path | str) -> None:
        self._path = Path(log_path)
        self._lock = threading.Lock()
        if self._path.parent != self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def log_inference(self, record: InferenceLogRecord) -> None:
        payload = record.as_json()
        self._write_line(payload)

    def log(self, record: InferenceLogRecord) -> None:
        self.log_inference(record)

    def _write_line(self, payload: Mapping[str, JsonValue]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.write("\n")
