# SPDX-License-Identifier: Apache-2.0

"""Utility to aggregate workflow QA metrics for Prometheus exporters."""

from __future__ import annotations


class MetricsRegistry:
    """Collect compression and semantic retention metrics."""

    __slots__ = ("_original_tokens", "_trimmed_tokens", "_semantic_sum", "_semantic_count")

    def __init__(self) -> None:
        self._original_tokens = 0
        self._trimmed_tokens = 0
        self._semantic_sum = 0.0
        self._semantic_count = 0

    def observe_trim(
        self,
        *,
        original_tokens: int,
        trimmed_tokens: int,
        semantic_retention: float | None = None,
    ) -> None:
        if original_tokens < 0:
            raise ValueError("original_tokens must be non-negative")
        if trimmed_tokens < 0:
            raise ValueError("trimmed_tokens must be non-negative")
        if semantic_retention is not None and not 0.0 <= semantic_retention <= 1.0:
            raise ValueError("semantic_retention must be between 0.0 and 1.0")

        self._original_tokens += original_tokens
        self._trimmed_tokens += trimmed_tokens

        if semantic_retention is not None:
            self._semantic_sum += semantic_retention
            self._semantic_count += 1

    def snapshot(self) -> dict[str, float]:
        compress_ratio = 1.0 if self._original_tokens == 0 else self._trimmed_tokens / self._original_tokens
        semantic_retention = 1.0 if self._semantic_count == 0 else self._semantic_sum / self._semantic_count
        return {
            "compress_ratio": compress_ratio,
            "semantic_retention": semantic_retention,
        }

    def export_prometheus(self) -> str:
        metrics = self.snapshot()
        body = [
            "# HELP compress_ratio Ratio of trimmed tokens to original tokens.",
            "# TYPE compress_ratio gauge",
            f"compress_ratio {format(metrics['compress_ratio'], 'g')}",
            "# HELP semantic_retention Average semantic retention score reported by trimmers.",
            "# TYPE semantic_retention gauge",
            f"semantic_retention {format(metrics['semantic_retention'], 'g')}",
        ]
        return "\n".join(body) + "\n"
