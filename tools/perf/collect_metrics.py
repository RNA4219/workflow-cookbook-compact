# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 RNA4219

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

METRIC_KEYS: tuple[str, ...] = (
    "compress_ratio",
    "semantic_retention",
    "review_latency",
    "reopen_rate",
    "spec_completeness",
)


@dataclass(frozen=True)
class SuiteConfig:
    metrics_url: str | None = None
    log_path: str | None = None
    output: str | None = None


SUITES: dict[str, SuiteConfig] = {
    "qa": SuiteConfig(output=".ga/qa-metrics.json"),
}


class MetricsCollectionError(RuntimeError):
    """Raised when metrics could not be collected."""


def _capture(source: Mapping[str, object], target: MutableMapping[str, float]) -> None:
    for key in METRIC_KEYS:
        if key in target:
            continue
        value = source.get(key)
        if isinstance(value, (int, float)):
            target[key] = float(value)


def _parse_prometheus(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        name, raw_value = parts[0], parts[1]
        if name in METRIC_KEYS:
            try:
                metrics[name] = float(raw_value)
            except ValueError:
                continue
    return metrics


def _load_prometheus(metrics_url: str) -> Mapping[str, float]:
    try:
        with urllib.request.urlopen(metrics_url) as response:  # type: ignore[arg-type]
            payload = response.read()
    except OSError as exc:  # urllib.request raises URLError, an OSError subclass
        raise MetricsCollectionError(f"Failed to read metrics from {metrics_url}: {exc}") from exc
    return _parse_prometheus(payload.decode("utf-8"))


def _load_chainlit_log(path: Path) -> Mapping[str, float]:
    if not path.exists():
        raise MetricsCollectionError(f"Chainlit log not found: {path}")
    metrics: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, Mapping):
            _capture(parsed, metrics)
            nested = parsed.get("metrics")
            if isinstance(nested, Mapping):
                _capture(nested, metrics)
    return metrics


def _merge(sources: Iterable[Mapping[str, float]]) -> dict[str, float]:
    combined: dict[str, float] = {}
    for mapping in sources:
        _capture(mapping, combined)
    missing = [key for key in METRIC_KEYS if key not in combined]
    if missing:
        raise MetricsCollectionError("Missing metrics: " + ", ".join(missing))
    return {key: combined[key] for key in METRIC_KEYS}


def collect_metrics(metrics_url: str | None, log_path: Path | None) -> dict[str, float]:
    sources: list[Mapping[str, float]] = []
    if metrics_url:
        sources.append(_load_prometheus(metrics_url))
    if log_path:
        sources.append(_load_chainlit_log(log_path))
    if not sources:
        raise MetricsCollectionError("At least one of --metrics-url or --log-path is required")
    return _merge(sources)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect performance metrics for post-processing")
    parser.add_argument("--suite", choices=sorted(SUITES), help="Preset input/output configuration")
    parser.add_argument("--metrics-url", help="Prometheus metrics endpoint URL")
    parser.add_argument("--log-path", type=Path, help="Path to Chainlit log file")
    parser.add_argument("--output", type=Path, help="File path to write collected metrics JSON")
    args = parser.parse_args(argv)

    suite = SUITES.get(args.suite) if args.suite else None

    metrics_url = args.metrics_url or (suite.metrics_url if suite else None)
    log_path = args.log_path if args.log_path is not None else (
        Path(suite.log_path) if suite and suite.log_path else None
    )
    output_path = args.output or (Path(suite.output) if suite and suite.output else None)

    if not metrics_url and log_path is None:
        parser.error("At least one of --metrics-url or --log-path must be provided")

    try:
        metrics = collect_metrics(metrics_url, log_path)
    except MetricsCollectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = json.dumps(metrics, ensure_ascii=False)
    sys.stdout.write(payload + "\n")
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
