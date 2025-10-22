# SPDX-License-Identifier: Apache-2.0

"""Katamari-style registry for trimming metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping

_MetricKey = tuple[str, tuple[tuple[str, str], ...]]

_SERIES_SUFFIXES: tuple[str, ...] = ("count", "sum", "avg", "min", "max")

_METRIC_HELP: Mapping[str, str] = {
    "katamari_trim_compress_ratio": "Compression ratio observed after trimming.",
    "katamari_trim_semantic_retention": "Semantic retention reported after trimming.",
}


@dataclass(slots=True)
class _Stats:
    """Aggregate statistics for a single metric series."""

    count: int = 0
    sum: float = 0.0
    min: float | None = None
    max: float | None = None

    def observe(self, value: float) -> None:
        if self.count == 0:
            self.min = value
            self.max = value
        else:
            assert self.min is not None
            assert self.max is not None
            self.min = min(self.min, value)
            self.max = max(self.max, value)
        self.count += 1
        self.sum += value

    def snapshot(self) -> dict[str, float | int]:
        if self.count == 0 or self.min is None or self.max is None:
            raise RuntimeError("Cannot snapshot statistics with no observations")
        average = self.sum / self.count
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": average,
            "min": self.min,
            "max": self.max,
        }


def _escape_label_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace('"', '\\"')
    )


class MetricsRegistry:
    """Collect trimming metrics and export them in Prometheus text format."""

    __slots__ = ("_default_labels", "_series")

    def __init__(self, *, default_labels: Mapping[str, str] | None = None) -> None:
        self._default_labels: Mapping[str, str] = dict(default_labels or {})
        self._series: Dict[_MetricKey, _Stats] = {}

    def observe_trim(
        self,
        *,
        compress_ratio: float,
        semantic_retention: float | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        if not 0.0 <= compress_ratio <= 1.0:
            raise ValueError("compress_ratio must be between 0.0 and 1.0")
        if semantic_retention is not None and not 0.0 <= semantic_retention <= 1.0:
            raise ValueError("semantic_retention must be between 0.0 and 1.0")

        normalized_labels = self._normalize_labels(labels)
        self._record("katamari_trim_compress_ratio", compress_ratio, normalized_labels)
        if semantic_retention is not None:
            self._record(
                "katamari_trim_semantic_retention",
                semantic_retention,
                normalized_labels,
            )

    def snapshot(self) -> dict[str, list[dict[str, object]]]:
        aggregated: MutableMapping[str, list[tuple[tuple[tuple[str, str], ...], dict[str, float | int]]]] = {}
        for (metric_name, label_items), stats in self._series.items():
            aggregated.setdefault(metric_name, []).append((label_items, stats.snapshot()))

        result: dict[str, list[dict[str, object]]] = {}
        for metric_name, entries in aggregated.items():
            ordered = sorted(entries, key=lambda item: item[0])
            payload: list[dict[str, object]] = []
            for label_items, values in ordered:
                record = dict(values)
                record["labels"] = dict(label_items)
                payload.append(record)
            result[metric_name] = payload
        return result

    def export_prometheus(self) -> str:
        snapshot = self.snapshot()
        lines: list[str] = []
        emitted: set[str] = set()
        for metric_name in sorted(snapshot):
            help_text = _METRIC_HELP.get(metric_name, metric_name)
            for entry in snapshot[metric_name]:
                labels = entry.get("labels")
                if not isinstance(labels, dict):
                    raise RuntimeError("Snapshot entry is missing labels mapping")
                label_items = tuple(sorted(labels.items()))
                label_text = self._format_labels(label_items)
                for suffix in _SERIES_SUFFIXES:
                    series_name = f"{metric_name}_{suffix}"
                    if series_name not in emitted:
                        lines.append(f"# HELP {series_name} {help_text} ({suffix}).")
                        lines.append(f"# TYPE {series_name} gauge")
                        emitted.add(series_name)
                    value = entry[suffix]
                    lines.append(f"{series_name}{label_text} {format(float(value), 'g')}")
        return "\n".join(lines) + ("\n" if lines else "")

    def _record(
        self,
        metric_name: str,
        value: float,
        labels: tuple[tuple[str, str], ...],
    ) -> None:
        key: _MetricKey = (metric_name, labels)
        stats = self._series.get(key)
        if stats is None:
            stats = _Stats()
            self._series[key] = stats
        stats.observe(value)

    def _normalize_labels(
        self, labels: Mapping[str, str] | None
    ) -> tuple[tuple[str, str], ...]:
        combined: Dict[str, str] = dict(self._default_labels)
        if labels:
            combined.update(labels)
        return tuple(sorted(combined.items()))

    @staticmethod
    def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        joined = ",".join(f"{key}=\"{_escape_label_value(value)}\"" for key, value in labels)
        return f"{{{joined}}}"
