# SPDX-License-Identifier: Apache-2.0
"""Metrics helpers for context trimming flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, MutableMapping, Tuple

LabelTuple = Tuple[Tuple[str, str], ...]


@dataclass
class _Summary:
    """Track aggregates for a metric value."""

    count: int = 0
    sum: float = 0.0
    min: float | None = None
    max: float | None = None

    def observe(self, value: float) -> None:
        self.count += 1
        self.sum += value
        self.min = value if self.min is None else min(self.min, value)
        self.max = value if self.max is None else max(self.max, value)

    def snapshot(self) -> dict[str, float | int]:
        average = self.sum / self.count if self.count else 0.0
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": average,
            "min": self.min if self.min is not None else 0.0,
            "max": self.max if self.max is not None else 0.0,
        }


@dataclass
class MetricsRegistry:
    """Collects Katamari-style metrics for context trimming."""

    namespace: str = "katamari_trim"
    default_labels: Mapping[str, str] | None = None
    _metrics: Dict[Tuple[str, LabelTuple], _Summary] = field(default_factory=dict)
    _help: MutableMapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._default_labels = dict(self.default_labels or {})
        self._help.setdefault(
            f"{self.namespace}_compress_ratio",
            "Compression ratio observed after trimming messages.",
        )
        self._help.setdefault(
            f"{self.namespace}_semantic_retention",
            "Semantic retention ratio reported by evaluation runs.",
        )

    def observe_trim(
        self,
        *,
        compress_ratio: float | None = None,
        semantic_retention: float | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        if compress_ratio is None and semantic_retention is None:
            raise ValueError("At least one metric must be provided.")
        combined_labels = dict(self._default_labels)
        if labels:
            combined_labels.update(labels)
        if compress_ratio is not None:
            self._observe(
                f"{self.namespace}_compress_ratio",
                compress_ratio,
                combined_labels,
            )
        if semantic_retention is not None:
            self._observe(
                f"{self.namespace}_semantic_retention",
                semantic_retention,
                combined_labels,
            )

    def snapshot(self) -> dict[str, list[dict[str, object]]]:
        data: dict[str, list[dict[str, object]]] = {}
        for (metric_name, label_tuple), summary in self._metrics.items():
            entry = {
                "labels": dict(label_tuple),
                "summary": summary.snapshot(),
            }
            data.setdefault(metric_name, []).append(entry)
        return data

    def export_prometheus(self) -> str:
        lines: list[str] = []
        metrics_by_name: dict[str, list[tuple[LabelTuple, _Summary]]] = {}
        for (metric_name, label_tuple), summary in self._metrics.items():
            metrics_by_name.setdefault(metric_name, []).append((label_tuple, summary))
        for metric_name in sorted(metrics_by_name):
            help_text = self._help.get(metric_name, "Recorded metric.")
            lines.append(f"# HELP {metric_name} {help_text}")
            lines.append(f"# TYPE {metric_name} summary")
            for label_tuple, summary in sorted(
                metrics_by_name[metric_name], key=lambda item: item[0]
            ):
                label_text = self._format_labels(label_tuple)
                snapshot = summary.snapshot()
                lines.append(f"{metric_name}_count{label_text} {snapshot['count']}")
                lines.append(f"{metric_name}_sum{label_text} {snapshot['sum']}")
                lines.append(f"{metric_name}_avg{label_text} {snapshot['avg']}")
                lines.append(f"{metric_name}_min{label_text} {snapshot['min']}")
                lines.append(f"{metric_name}_max{label_text} {snapshot['max']}")
        return "\n".join(lines) + ("\n" if lines else "")

    def _observe(
        self,
        metric_name: str,
        value: float,
        labels: Mapping[str, str],
    ) -> None:
        label_tuple = self._normalise_labels(labels)
        key = (metric_name, label_tuple)
        summary = self._metrics.get(key)
        if summary is None:
            summary = _Summary()
            self._metrics[key] = summary
        summary.observe(value)

    @staticmethod
    def _normalise_labels(labels: Mapping[str, str]) -> LabelTuple:
        return tuple(sorted(labels.items()))

    @staticmethod
    def _format_labels(label_tuple: LabelTuple) -> str:
        if not label_tuple:
            return ""
        parts = [f'{key}="{value}"' for key, value in label_tuple]
        return "{" + ",".join(parts) + "}"
