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
        "# HELP trim_compress_ratio_avg Ratio\n"
        "# TYPE trim_compress_ratio_avg gauge\n"
        "trim_compress_ratio_avg 0.82\n"
        "workflow_review_latency_seconds_sum 21600\n"
        "workflow_review_latency_seconds_count 12\n"
        "task_seed_cycle_time_seconds_sum 3600\n"
        "task_seed_cycle_time_seconds_count 12\n"
        "birdseye_refresh_delay_minutes_sum 200\n"
        "birdseye_refresh_delay_minutes_count 5\n"
        "workflow_review_latency_reopened_total 3\n"
        "workflow_review_latency_total 60\n",
        encoding="utf-8",
    )

    structured = tmp_path / "docops.log"
    structured.write_text(
        "\n".join(
            (
                '{"metrics": {"checklist_compliance_rate": {"compliant": 48, "total": 50}}}',
                '{"metrics": {"task_seed_cycle_time_minutes": 25.0}}',
                '{"metrics": {"birdseye_refresh_delay_minutes": 150.0}}',
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
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 40.0,
    }


def test_collects_average_metrics_from_prometheus(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_seconds_sum 3600\n"
        "task_seed_cycle_time_seconds_count 12\n"
        "birdseye_refresh_delay_seconds_sum 7200\n"
        "birdseye_refresh_delay_seconds_count 120\n",
        encoding="utf-8",
    )

    result = _run_cli("--metrics-url", prometheus.as_uri())

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "checklist_compliance_rate": 96.0,
        "task_seed_cycle_time_minutes": 5.0,
        "birdseye_refresh_delay_minutes": 1.0,
    }


def test_pushgateway_receives_metrics_payload(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_minutes 12.0\n"
        "birdseye_refresh_delay_minutes 18.0\n",
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
    )
    assert captured["method"] == "PUT"
    assert captured["path"] == "/metrics"


def test_pushgateway_failure_causes_non_zero_exit(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "checklist_compliance_rate 0.96\n"
        "task_seed_cycle_time_minutes 12.0\n"
        "birdseye_refresh_delay_minutes 18.0\n",
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
        "task_seed_cycle_time_minutes 5.5\n"
        "birdseye_refresh_delay_minutes 16.0\n",
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
        "task_seed_cycle_time_minutes": 5.5,
        "birdseye_refresh_delay_minutes": 16.0,
    }


def test_exits_non_zero_when_metrics_missing(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text("up 1\n", encoding="utf-8")

    structured = tmp_path / "docops.log"
    structured.write_text("{}\n", encoding="utf-8")

    result = _run_cli("--metrics-url", prometheus.as_uri(), "--log-path", str(structured))

    assert result.returncode != 0
    assert "checklist_compliance_rate" in result.stderr
    assert "task_seed_cycle_time_minutes" in result.stderr
    assert "birdseye_refresh_delay_minutes" in result.stderr


