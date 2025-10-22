from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.perf.metrics_registry import MetricsRegistry


def test_export_prometheus_contains_trim_metrics() -> None:
    registry = MetricsRegistry(default_labels={"service": "trim"})

    registry.observe_trim(
        compress_ratio=0.5,
        semantic_retention=0.8,
        labels={"model": "gpt-4o"},
    )
    registry.observe_trim(compress_ratio=0.25, semantic_retention=0.6)

    snapshot = registry.snapshot()

    compress_entries = snapshot["katamari_trim_compress_ratio"]
    compress_total = {
        key: sum(entry["summary"][key] for entry in compress_entries)
        for key in ("count", "sum")
    }
    assert compress_total["count"] == 2
    assert compress_total["sum"] == pytest.approx(0.75)

    semantic_entries = snapshot["katamari_trim_semantic_retention"]
    semantic_total = {
        key: sum(entry["summary"][key] for entry in semantic_entries)
        for key in ("count", "sum")
    }
    assert semantic_total["count"] == 2
    assert semantic_total["sum"] == pytest.approx(1.4)

    text = registry.export_prometheus()
    assert "# TYPE katamari_trim_compress_ratio summary" in text
    assert "katamari_trim_compress_ratio_count" in text
    assert "katamari_trim_semantic_retention_sum" in text
    assert 'model="gpt-4o"' in text
    assert 'service="trim"' in text
