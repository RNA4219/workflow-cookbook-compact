from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if (repo_root := str(ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from tools.perf.metrics_registry import MetricsRegistry  # noqa: E402


def test_export_prometheus_after_observing_trim() -> None:
    registry = MetricsRegistry()

    registry.observe_trim(original_tokens=1000, trimmed_tokens=400, semantic_retention=0.92)
    registry.observe_trim(original_tokens=500, trimmed_tokens=250)

    snapshot = registry.snapshot()
    expected_ratio = (400 + 250) / (1000 + 500)
    assert snapshot["compress_ratio"] == pytest.approx(expected_ratio)
    assert snapshot["semantic_retention"] == pytest.approx(0.92)

    prometheus = registry.export_prometheus()
    lines = [line for line in prometheus.splitlines() if line and not line.startswith("#")]
    metrics = {name: float(value) for name, value in (line.split(None, 1) for line in lines)}

    assert metrics["compress_ratio"] == pytest.approx(snapshot["compress_ratio"])
    assert metrics["semantic_retention"] == pytest.approx(snapshot["semantic_retention"])
