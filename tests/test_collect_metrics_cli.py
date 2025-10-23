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


def test_collects_metrics_from_prometheus_and_chainlit(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "# HELP trim_compress_ratio_avg Ratio\n"
        "# TYPE trim_compress_ratio_avg gauge\n"
        "trim_compress_ratio_avg 0.82\n"
        "trim_review_latency_seconds_sum 21600\n"
        "trim_review_latency_seconds_count 12\n"
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
        "compress_ratio": 82.0,
        "semantic_retention": 74.0,
        "review_latency": 0.5,
        "reopen_rate": 5.0,
        "spec_completeness": 91.0,
    }


def test_pushgateway_receives_metrics_payload(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "compress_ratio 0.82\n"
        "semantic_retention 0.74\n"
        "review_latency 0.5\n"
        "reopen_rate 0.05\n"
        "spec_completeness 0.91\n",
        encoding="utf-8",
    )

    with _mock_pushgateway() as (url, captured):
        result = _run_cli("--metrics-url", prometheus.as_uri(), "--pushgateway-url", url)

    assert result.returncode == 0, result.stderr
    body = captured["body"]
    assert isinstance(body, bytes)
    assert body.decode("utf-8") == (
        "compress_ratio 82\n"
        "semantic_retention 74\n"
        "review_latency 0.5\n"
        "reopen_rate 5\n"
        "spec_completeness 91\n"
    )
    assert captured["method"] == "PUT"
    assert captured["path"] == "/metrics"


def test_pushgateway_failure_causes_non_zero_exit(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "compress_ratio 0.82\n"
        "semantic_retention 0.74\n"
        "review_latency 0.5\n"
        "reopen_rate 0.05\n"
        "spec_completeness 0.91\n",
        encoding="utf-8",
    )

    with _mock_pushgateway(status_code=500) as (url, _captured):
        result = _run_cli("--metrics-url", prometheus.as_uri(), "--pushgateway-url", url)

    assert result.returncode != 0
    assert "PushGateway" in result.stderr or "push metrics" in result.stderr


def test_suite_output_generates_file_and_stdout_matches(tmp_path: Path) -> None:
    prometheus = tmp_path / "metrics.prom"
    prometheus.write_text(
        "# HELP compress_ratio Ratio\n"
        "# TYPE compress_ratio gauge\n"
        "compress_ratio 0.82\n"
        "review_latency 18.5\n"
        "reopen_rate 0.062\n",
        encoding="utf-8",
    )

    chainlit = tmp_path / "chainlit.log"
    chainlit.write_text(
        """{"metrics": {"semantic_retention": 0.74, "spec_completeness": 0.91}}\n""",
        encoding="utf-8",
    )

    output_path = tmp_path / "out.json"

    result = _run_cli(
        "--suite",
        "qa",
        "--metrics-url",
        prometheus.as_uri(),
        "--log-path",
        str(chainlit),
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert payload == {
        "compress_ratio": 82.0,
        "semantic_retention": 74.0,
        "review_latency": 18.5,
        "reopen_rate": 6.2,
        "spec_completeness": 91.0,
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
