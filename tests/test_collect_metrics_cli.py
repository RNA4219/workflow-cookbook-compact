from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.perf.collect_metrics", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_collects_metrics_from_prometheus_and_chainlit(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "# HELP compress_ratio Ratio\n"
        "# TYPE compress_ratio gauge\n"
        "compress_ratio 0.82\n"
        "katamari_review_latency_seconds_sum 21600\n"
        "katamari_review_latency_seconds_count 12\n"
        "katamari_reviews_reopened_total 3\n"
        "katamari_reviews_total 60\n",
        encoding="utf-8",
    )

    chainlit = tmp_path / "chainlit.log"
    chainlit.write_text(
        "\n".join(
            (
                '{"metrics": {"semantic_retention": 0.74}}',
                '{"metrics": {"spec_completeness": {"with_spec": 91, "total": 100}}}',
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(chainlit))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "compress_ratio": 0.82,
        "semantic_retention": 0.74,
        "review_latency": 0.5,
        "reopen_rate": 0.05,
        "spec_completeness": 0.91,
    }


def test_exits_non_zero_when_metrics_missing(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text("up 1\n", encoding="utf-8")

    chainlit = tmp_path / "chainlit.log"
    chainlit.write_text("{}\n", encoding="utf-8")

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(chainlit))

    assert result.returncode != 0
    assert "compress_ratio" in result.stderr
    assert "semantic_retention" in result.stderr
    assert "review_latency" in result.stderr
    assert "reopen_rate" in result.stderr
    assert "spec_completeness" in result.stderr


def test_exits_non_zero_when_additional_metrics_missing(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "compress_ratio 0.8\nsemantic_retention 0.9\n",
        encoding="utf-8",
    )

    chainlit = tmp_path / "chainlit.log"
    chainlit.write_text("{}\n", encoding="utf-8")

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(chainlit))

    assert result.returncode != 0
    assert "review_latency" in result.stderr
    assert "reopen_rate" in result.stderr
    assert "spec_completeness" in result.stderr
