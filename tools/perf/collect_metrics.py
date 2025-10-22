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

PERCENTAGE_KEYS: tuple[str, ...] = (
    "compress_ratio",
    "semantic_retention",
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


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _capture(source: Mapping[str, object], target: MutableMapping[str, float]) -> None:
    for key in METRIC_KEYS:
        if key in target:
            continue
        value = source.get(key)
        coerced = _coerce_float(value)
        if coerced is not None:
            target[key] = coerced


def _capture_spec_metrics(source: Mapping[str, object], target: MutableMapping[str, float]) -> None:
    if "spec_completeness" in target:
        return
    spec_raw = source.get("spec_completeness")
    if isinstance(spec_raw, Mapping):
        numerator = None
        denominator = None
        for candidate in ("with_spec", "complete", "numerator", "count", "ready"):
            numerator = _coerce_float(spec_raw.get(candidate))
            if numerator is not None:
                break
        for candidate in ("total", "denominator", "all", "overall"):
            denominator = _coerce_float(spec_raw.get(candidate))
            if denominator is not None and denominator != 0:
                break
        if numerator is not None and denominator is not None and denominator != 0:
            target["spec_completeness"] = numerator / denominator
            return
        ratio = _coerce_float(spec_raw.get("ratio"))
        if ratio is not None:
            target["spec_completeness"] = ratio


def _derive_review_latency(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("review_latency")
    if direct is not None:
        return direct
    candidates: Sequence[tuple[str, float]] = (
        ("katamari_review_latency_seconds", 3600.0),
        ("review_latency_seconds", 3600.0),
        ("katamari_review_latency_hours", 1.0),
        ("review_latency_hours", 1.0),
    )
    for prefix, scale in candidates:
        sum_key = f"{prefix}_sum"
        count_key = f"{prefix}_count"
        total = raw.get(sum_key)
        count = raw.get(count_key)
        if total is None or count in (None, 0.0):
            continue
        return (total / count) / scale
    return None


def _derive_reopen_rate(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("reopen_rate")
    if direct is not None:
        return direct
    suffix_pairs: Sequence[tuple[str, Sequence[str]]] = (
        ("_reopened_total", ("_total", "_count")),
        ("_reopened_count", ("_count", "_total")),
        ("_reopen_total", ("_total", "_count")),
        ("_reopen_count", ("_count", "_total")),
    )
    for numerator_suffix, denominator_suffixes in suffix_pairs:
        for name, value in raw.items():
            if not name.endswith(numerator_suffix):
                continue
            numerator = value
            base = name[: -len(numerator_suffix)]
            for suffix in denominator_suffixes:
                denominator_key = f"{base}{suffix}"
                denominator = raw.get(denominator_key)
                if denominator in (None, 0.0):
                    continue
                return numerator / denominator
    return None


def _parse_prometheus(text: str) -> dict[str, float]:
    raw: dict[str, float] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        name_token = parts[0]
        raw_value = parts[-1]
        metric_name = name_token.split("{", 1)[0]
        value = _coerce_float(raw_value)
        if value is None:
            continue
        if metric_name in raw:
            raw[metric_name] += value
        else:
            raw[metric_name] = value

    metrics: dict[str, float] = {}
    _capture(raw, metrics)

    review_latency = _derive_review_latency(raw)
    if review_latency is not None and "review_latency" not in metrics:
        metrics["review_latency"] = review_latency

    reopen_rate = _derive_reopen_rate(raw)
    if reopen_rate is not None and "reopen_rate" not in metrics:
        metrics["reopen_rate"] = reopen_rate

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
            _capture_spec_metrics(parsed, metrics)
            nested = parsed.get("metrics")
            if isinstance(nested, Mapping):
                _capture(nested, metrics)
                _capture_spec_metrics(nested, metrics)
    return metrics


def _merge(sources: Iterable[Mapping[str, float]]) -> dict[str, float]:
    combined: dict[str, float] = {}
    for mapping in sources:
        _capture(mapping, combined)
    missing = [key for key in METRIC_KEYS if key not in combined]
    if missing:
        raise MetricsCollectionError("Missing metrics: " + ", ".join(missing))
    result = {key: combined[key] for key in METRIC_KEYS}
    for key in PERCENTAGE_KEYS:
        result[key] = result[key] * 100.0
    return result


def _format_pushgateway_payload(metrics: Mapping[str, float]) -> bytes:
    lines = [f"{key} {format(metrics[key], 'g')}" for key in METRIC_KEYS]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _push_to_gateway(pushgateway_url: str, metrics: Mapping[str, float]) -> None:
    payload = _format_pushgateway_payload(metrics)
    request = urllib.request.Request(pushgateway_url, data=payload, method="PUT")
    request.add_header("Content-Type", "text/plain; version=0.0.4")
    try:
        with urllib.request.urlopen(request) as response:  # type: ignore[arg-type]
            response.read()
    except OSError as exc:
        raise MetricsCollectionError(
            f"Failed to push metrics to PushGateway at {pushgateway_url}: {exc}"
        ) from exc


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
    parser.add_argument("--pushgateway-url", help="Prometheus PushGateway endpoint URL")
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
        if args.pushgateway_url:
            _push_to_gateway(args.pushgateway_url, metrics)
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
