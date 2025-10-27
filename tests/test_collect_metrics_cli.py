from __future__ import annotations

import http.server
import json
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.perf.collect_metrics", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


@contextmanager
def _mock_pushgateway(status_code: int = 202) -> Iterator[tuple[str, dict[str, object]]]:
    captured: dict[str, object] = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_PUT(self) -> None:  # noqa: N802 - http.server API
            length = int(self.headers.get("Content-Length", "0"))
            captured["body"] = self.rfile.read(length)
            captured["path"] = self.path
            captured["method"] = "PUT"
            captured["headers"] = dict(self.headers)
            self.send_response(status_code)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - external API
            return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()

    server = http.server.HTTPServer((host, port), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}/metrics", captured
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_collects_metrics_from_prometheus_and_logs(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "# HELP trim_compress_ratio_sum Ratio\n"
        "# TYPE trim_compress_ratio_sum gauge\n"
        "trim_compress_ratio_sum 8.2\n"
        "trim_compress_ratio_count 10\n"
        "trim_semantic_retention_sum 9.1\n"
        "trim_semantic_retention_count 10\n"
        "workflow_review_latency_seconds_sum 21600\n"
        "workflow_review_latency_seconds_count 12\n"
        "task_seed_cycle_time_seconds_sum 3600\n"
        "task_seed_cycle_time_seconds_count 12\n"
        "birdseye_refresh_delay_minutes_sum 200\n"
        "birdseye_refresh_delay_minutes_count 5\n"
        "workflow_reopen_rate 0.12\n"
        "workflow_spec_completeness_ratio 0.88\n",
        encoding="utf-8",
    )

    structured = tmp_path / "docops.log"
    structured.write_text(
        "\n".join(
            (
                '{"statistics": {"compress_ratio": 0.85}, "metrics": {"semantic_retention": 0.92}}',
                '{"metrics": {"checklist_compliance_rate": {"compliant": 48, "total": 50}}}',
                '{"metrics": {"task_seed_cycle_time_minutes": 25.0}}',
                '{"metrics": {"birdseye_refresh_delay_minutes": 150.0}}',
                '{"metrics": {"reopen_rate": {"reopened": 3, "total": 12}}}',
                '{"metrics": {"spec_completeness": {"with_spec": 91, "total": 100}}}',
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(structured))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 96.0,
        "compress_ratio": pytest.approx(0.85),
        "semantic_retention": pytest.approx(0.92),
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 40.0,
        "review_latency": 0.5,
        "reopen_rate": 25.0,
        "spec_completeness": 91.0,
    }


def test_collects_average_metrics_from_prometheus(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "trim_compress_ratio_sum 8.2\n"
        "trim_compress_ratio_count 10\n"
        "trim_semantic_retention_sum 9.1\n"
        "trim_semantic_retention_count 10\n"
        "review_latency 0.5\n"
        "task_seed_cycle_time_seconds_sum 3600\n"
        "task_seed_cycle_time_seconds_count 12\n"
        "birdseye_refresh_delay_seconds_sum 7200\n"
        "birdseye_refresh_delay_seconds_count 120\n"
        "workflow_reopen_rate 0.2\n"
        "workflow_spec_completeness_ratio 0.95\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri())

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 96.0,
        "compress_ratio": pytest.approx(0.82),
        "semantic_retention": pytest.approx(0.91),
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 1.0,
        "review_latency": 0.5,
        "reopen_rate": 20.0,
        "spec_completeness": 95.0,
    }


def test_collects_review_latency_from_workflow_aggregates(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_minutes 5.0\n"
        "birdseye_refresh_delay_minutes 1.0\n"
        "workflow_review_latency_seconds_sum 21600\n"
        "workflow_review_latency_seconds_count 12\n"
        "compress_ratio 0.82\n"
        "semantic_retention 0.91\n"
        "workflow_reopen_rate 0.2\n"
        "workflow_spec_completeness_ratio 0.95\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri())

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 96.0,
        "compress_ratio": pytest.approx(0.82),
        "semantic_retention": pytest.approx(0.91),
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 1.0,
        "review_latency": pytest.approx(0.5),
        "reopen_rate": 20.0,
        "spec_completeness": 95.0,
    }


def test_collects_review_latency_from_minute_aggregates(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_minutes 5.0\n"
        "birdseye_refresh_delay_minutes 1.0\n"
        "workflow_review_latency_minutes_sum 360\n"
        "workflow_review_latency_minutes_count 12\n"
        "compress_ratio 0.82\n"
        "semantic_retention 0.91\n"
        "workflow_reopen_rate 0.2\n"
        "workflow_spec_completeness_ratio 0.95\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri())

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 96.0,
        "compress_ratio": pytest.approx(0.82),
        "semantic_retention": pytest.approx(0.91),
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 1.0,
        "review_latency": pytest.approx(0.5),
        "reopen_rate": 20.0,
        "spec_completeness": 95.0,
    }


def test_structured_log_overrides_prometheus_with_latest_scale(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.40\n"
        "compress_ratio 0.62\n"
        "semantic_retention 0.73\n"
        "task_seed_cycle_time_minutes 15.0\n"
        "birdseye_refresh_delay_minutes 3.0\n"
        "review_latency 1.0\n"
        "workflow_reopen_rate 0.10\n"
        "workflow_spec_completeness_ratio 0.55\n",
        encoding="utf-8",
    )

    structured = tmp_path / "docops.log"
    structured.write_text(
        "\n".join(
            (
                '{"metrics": {"checklist_compliance_rate": {"compliant": 18, "total": 20}}}',
                '{"metrics": {"compress_ratio": 0.88}}',
                '{"metrics": {"semantic_retention": 0.96}}',
                '{"metrics": {"task_seed_cycle_time_minutes": 6.0}}',
                '{"metrics": {"birdseye_refresh_delay_minutes": 1.5}}',
                '{"metrics": {"review_latency": 0.25}}',
                '{"metrics": {"reopen_rate": {"reopened": 3, "total": 12}}}',
                '{"metrics": {"spec_completeness": {"with_spec": 91, "total": 100}}}',
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(structured))

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 90.0,
        "compress_ratio": pytest.approx(0.88),
        "semantic_retention": pytest.approx(0.96),
        "task_seed_cycle_time_minutes": 15.0,
        "birdseye_refresh_delay_minutes": 3.0,
        "review_latency": 0.25,
        "reopen_rate": 25.0,
        "spec_completeness": 91.0,
    }


def test_cli_uses_yaml_scale_annotations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    metrics_yaml = tmp_path / "metrics.yaml"
    metrics_yaml.write_text(
        "\n".join(
            (
                "checklist_compliance_rate: チェックリスト準拠率(%)",
                "task_seed_cycle_time_minutes: Task Seed 処理時間(分)",
                "birdseye_refresh_delay_minutes: Birdseye 更新遅延(分)",
                "review_latency: レビュー待機時間(時間)",
                "compress_ratio: トリミング後のコンテキスト圧縮率(0-1)",
                "semantic_retention: トリミング後に保持された意味情報の割合(0-1)",
                "reopen_rate: 再オープン率(0-1)",
                "spec_completeness: スペック充足率(%)",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_minutes 5.0\n"
        "birdseye_refresh_delay_minutes 1.0\n"
        "review_latency 0.5\n"
        "compress_ratio 0.82\n"
        "semantic_retention 0.91\n"
        "workflow_reopen_rate 0.2\n"
        "workflow_spec_completeness_ratio 0.95\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("GOVERNANCE_METRICS_PATH", str(metrics_yaml))

    result = _run_cli("--metrics-url", prometheus.as_uri())

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert list(payload) == [
        "checklist_compliance_rate",
        "task_seed_cycle_time_minutes",
        "birdseye_refresh_delay_minutes",
        "review_latency",
        "compress_ratio",
        "semantic_retention",
        "reopen_rate",
        "spec_completeness",
    ]
    assert payload["checklist_compliance_rate"] == pytest.approx(96.0)
    assert payload["reopen_rate"] == pytest.approx(0.2)
    assert payload["spec_completeness"] == pytest.approx(95.0)


def test_pushgateway_receives_metrics_payload(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "trim_compress_ratio_avg 0.82\n"
        "trim_semantic_retention_avg 0.91\n"
        "task_seed_cycle_time_minutes 12.0\n"
        "birdseye_refresh_delay_minutes 18.0\n"
        "review_latency 2.5\n"
        "workflow_reopen_rate 0.1\n"
        "workflow_spec_completeness_ratio 0.87\n",
        encoding="utf-8",
    )

    with _mock_pushgateway() as (url, captured):
        result = _run_cli("--metrics-url", prometheus.as_uri(), "--pushgateway-url", url)

    assert result.returncode == 0, result.stderr
    body = captured["body"]
    assert isinstance(body, bytes)
    assert body.decode("utf-8") == (
        "checklist_compliance_rate 96\n"
        "task_seed_cycle_time_minutes 12\n"
        "birdseye_refresh_delay_minutes 18\n"
        "review_latency 2.5\n"
        "compress_ratio 0.82\n"
        "semantic_retention 0.91\n"
        "reopen_rate 10\n"
        "spec_completeness 87\n"
    )
    assert captured["method"] == "PUT"
    assert captured["path"] == "/metrics"


def test_pushgateway_failure_causes_non_zero_exit(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "trim_compress_ratio_avg 0.82\n"
        "trim_semantic_retention_avg 0.91\n"
        "task_seed_cycle_time_minutes 12.0\n"
        "birdseye_refresh_delay_minutes 18.0\n"
        "review_latency 2.5\n"
        "workflow_reopen_rate 0.1\n"
        "workflow_spec_completeness_ratio 0.87\n",
        encoding="utf-8",
    )

    with _mock_pushgateway(status_code=500) as (url, _captured):
        result = _run_cli("--metrics-url", prometheus.as_uri(), "--pushgateway-url", url)

    assert result.returncode != 0
    assert "PushGateway" in result.stderr or "push metrics" in result.stderr


def test_suite_output_generates_file_and_stdout_matches(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "# HELP checklist_compliance_rate Ratio\n"
        "# TYPE checklist_compliance_rate gauge\n"
        "checklist_compliance_rate 0.92\n"
        "trim_compress_ratio_avg 0.78\n"
        "trim_semantic_retention_avg 0.89\n"
        "task_seed_cycle_time_minutes 5.5\n"
        "birdseye_refresh_delay_minutes 16.0\n"
        "review_latency 1.25\n"
        "workflow_reopen_rate 0.08\n"
        "workflow_spec_completeness_ratio 0.83\n",
        encoding="utf-8",
    )

    structured = tmp_path / "docops.log"
    structured.write_text(
        """{"metrics": {"checklist_compliance_rate": {"compliant": 23, "total": 24}}}\n""",
        encoding="utf-8",
    )

    output_path = tmp_path / "out.json"

    result = _run_cli(
        "--suite",
        "qa",
        "--metrics-url",
        prometheus.as_uri(),
        "--log-path",
        str(structured),
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert payload == {
        "checklist_compliance_rate": 95.83333333333334,
        "compress_ratio": 0.78,
        "semantic_retention": 0.89,
        "task_seed_cycle_time_minutes": 5.5,
        "birdseye_refresh_delay_minutes": 16.0,
        "review_latency": 1.25,
        "reopen_rate": 8.0,
        "spec_completeness": 83.0,
    }


def test_exits_non_zero_when_metrics_missing(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text("up 1\n", encoding="utf-8")

    structured = tmp_path / "docops.log"
    structured.write_text("{}\n", encoding="utf-8")

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(structured))

    assert result.returncode != 0
    assert "checklist_compliance_rate" in result.stderr
    assert "compress_ratio" in result.stderr
    assert "semantic_retention" in result.stderr
    assert "task_seed_cycle_time_minutes" in result.stderr
    assert "birdseye_refresh_delay_minutes" in result.stderr
    assert "review_latency" in result.stderr
    assert "reopen_rate" in result.stderr
    assert "spec_completeness" in result.stderr


