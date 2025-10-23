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
    "checklist_compliance_rate",
    "task_seed_cycle_time_minutes",
    "birdseye_refresh_delay_minutes",
    "review_latency",
    "compress_ratio",
    "semantic_retention",
    "reopen_rate",
    "spec_completeness",
)

PERCENTAGE_KEYS: tuple[str, ...] = (
    "checklist_compliance_rate",
    "reopen_rate",
    "spec_completeness",
)

_TRIM_COMPRESS_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_compress_ratio", 1.0),
    ("context_compression_ratio", 1.0),
)

_TRIM_SEMANTIC_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_semantic_retention", 1.0),
    ("context_semantic_retention", 1.0),
)

_METRIC_SOURCE_PREFERENCES: Mapping[str, tuple[str, ...]] = {
    "compress_ratio": (
        "trim_compress_ratio_avg",
        "trim_compress_ratio",
        "compress_ratio",
    ),
    "semantic_retention": (
        "trim_semantic_retention_avg",
        "trim_semantic_retention",
        "semantic_retention",
    ),
    "reopen_rate": (
        "workflow_reopen_rate_avg",
        "workflow_reopen_rate",
        "docops_reopen_rate",
        "reopen_rate",
    ),
    "spec_completeness": (
        "workflow_spec_completeness_ratio_avg",
        "workflow_spec_completeness_avg",
        "workflow_spec_completeness_ratio",
        "workflow_spec_completeness",
        "spec_completeness_ratio",
        "spec_completeness",
    ),
}

REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_review_latency_seconds", 3600.0),
    ("review_latency_seconds", 3600.0),
    ("trim_review_latency_hours", 1.0),
    ("review_latency_hours", 1.0),
)

WORKFLOW_REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("workflow_review_latency_seconds", 3600.0),
    ("workflow_review_latency_hours", 1.0),
)

_LEGACY_REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("legacy_review_latency_seconds", 3600.0),
    ("legacy_review_latency_hours", 1.0),
)

# Prefer the workflow_review_* prefixed aggregates; keep legacy_* as a
# compatibility fallback so existing exporters continue to work.
_REVIEW_LATENCY_AGGREGATE_PREFIXES: tuple[tuple[str, float], ...] = (
    *WORKFLOW_REVIEW_LATENCY_PREFIXES,
    *REVIEW_LATENCY_PREFIXES,
    *_LEGACY_REVIEW_LATENCY_PREFIXES,
)

_RATIO_CAPTURE_ENTRIES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "reopen_rate",
        ("reopened", "reopens", "numerator"),
        ("total", "resolved", "all", "denominator"),
    ),
    (
        "spec_completeness",
        ("with_spec", "with_specs", "completed", "numerator"),
        ("total", "all", "denominator"),
    ),
)

_RATIO_PROMETHEUS_CONFIG: Mapping[str, tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[str, float], ...]]] = {
    "reopen_rate": (
        ("_reopened", "_reopen"),
        ("_total", "_count", "_closed", "_all"),
        (("workflow_reopen_rate", 1.0), ("docops_reopen_rate", 1.0), ("reopen_rate", 1.0)),
    ),
    "spec_completeness": (
        ("_with_spec", "_with_specs", "_completed"),
        ("_total", "_count", "_all"),
        (
            ("workflow_spec_completeness_ratio", 1.0),
            ("workflow_spec_completeness", 1.0),
            ("spec_completeness_ratio", 1.0),
            ("spec_completeness", 1.0),
        ),
    ),
}


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


def _capture(
    source: Mapping[str, object],
    target: MutableMapping[str, float],
    *,
    overwrite: bool = False,
) -> None:
    for key in METRIC_KEYS:
        if not overwrite and key in target:
            continue
        preferences = _METRIC_SOURCE_PREFERENCES.get(key, (key,))
        for candidate in preferences:
            value = source.get(candidate)
            if value is None:
                continue
            coerced = _coerce_float(value)
            if coerced is not None:
                target[key] = coerced
                break


def _capture_trim_metrics(
    source: Mapping[str, object],
    target: MutableMapping[str, float],
    *,
    overwrite: bool = False,
) -> None:
    numeric = _coerce_numeric_mapping(source)
    if not numeric:
        return
    if overwrite or "compress_ratio" not in target:
        derived_compress = _derive_average(numeric, _TRIM_COMPRESS_PREFIXES)
        if derived_compress is not None:
            target["compress_ratio"] = derived_compress
    if overwrite or "semantic_retention" not in target:
        derived_semantic = _derive_average(numeric, _TRIM_SEMANTIC_PREFIXES)
        if derived_semantic is not None:
            target["semantic_retention"] = derived_semantic


def _coerce_numeric_mapping(source: Mapping[str, object]) -> dict[str, float]:
    numeric: dict[str, float] = {}
    for key, value in source.items():
        if isinstance(value, Mapping):
            continue
        coerced = _coerce_float(value)
        if coerced is not None:
            numeric[key] = coerced
    return numeric


def _capture_review_latency(
    source: Mapping[str, object],
    target: MutableMapping[str, float],
    *,
    overwrite: bool = False,
) -> None:
    if not overwrite and "review_latency" in target:
        return
    numeric = _coerce_numeric_mapping(source)
    if not numeric:
        return
    derived = _derive_review_latency(numeric)
    if derived is not None:
        target["review_latency"] = derived


def _capture_compliance(
    source: Mapping[str, object],
    target: MutableMapping[str, float],
    *,
    overwrite: bool = False,
) -> None:
    if not overwrite and "checklist_compliance_rate" in target:
        return
    compliance_raw = source.get("checklist_compliance_rate")
    if isinstance(compliance_raw, Mapping):
        numerator = None
        denominator = None
        for candidate in ("compliant", "checked", "passing", "numerator"):
            numerator = _coerce_float(compliance_raw.get(candidate))
            if numerator is not None:
                break
        for candidate in ("total", "denominator", "all", "overall"):
            denominator = _coerce_float(compliance_raw.get(candidate))
            if denominator is not None and denominator != 0:
                break
        if numerator is not None and denominator is not None and denominator != 0:
            target["checklist_compliance_rate"] = numerator / denominator
            return
        ratio = _coerce_float(compliance_raw.get("ratio"))
        if ratio is not None:
            target["checklist_compliance_rate"] = ratio


def _capture_ratio_metric(
    source: Mapping[str, object],
    target: MutableMapping[str, float],
    metric_key: str,
    numerator_keys: Sequence[str],
    denominator_keys: Sequence[str],
    *,
    overwrite: bool = False,
) -> None:
    if not overwrite and metric_key in target:
        return
    raw = source.get(metric_key)
    if not isinstance(raw, Mapping):
        return
    numerator = None
    denominator = None
    for candidate in numerator_keys:
        numerator = _coerce_float(raw.get(candidate))
        if numerator is not None:
            break
    for candidate in denominator_keys:
        denominator = _coerce_float(raw.get(candidate))
        if denominator is not None and denominator != 0:
            break
    if numerator is not None and denominator is not None and denominator != 0:
        target[metric_key] = numerator / denominator
        return
    ratio = _coerce_float(raw.get("ratio"))
    if ratio is not None:
        target[metric_key] = ratio


def _derive_review_latency(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("review_latency")
    if direct is not None:
        return direct
    # Prefer the workflow_review_* prefixed aggregates; keep legacy_* as a
    # compatibility fallback so existing exporters continue to work.
    return _derive_average(raw, _REVIEW_LATENCY_AGGREGATE_PREFIXES)


def _derive_ratio_by_suffixes(
    raw: Mapping[str, float],
    numerator_suffixes: Sequence[str],
    denominator_suffixes: Sequence[str],
) -> float | None:
    for numerator_suffix in numerator_suffixes:
        for name, value in raw.items():
            if not name.endswith(numerator_suffix):
                continue
            base = name[: -len(numerator_suffix)]
            numerator = value
            for suffix in denominator_suffixes:
                denominator_key = f"{base}{suffix}"
                denominator = raw.get(denominator_key)
                if denominator in (None, 0.0):
                    continue
                return numerator / denominator
    return None


def _derive_ratio_metric(
    raw: Mapping[str, float],
    metric_key: str,
    *,
    numerator_suffixes: Sequence[str],
    denominator_suffixes: Sequence[str],
    prefixes: Sequence[tuple[str, float]] = (),
) -> float | None:
    direct = raw.get(metric_key)
    if direct is not None:
        return direct
    ratio = _derive_ratio_by_suffixes(raw, numerator_suffixes, denominator_suffixes)
    if ratio is not None:
        return ratio
    if prefixes:
        return _derive_average(raw, prefixes)
    return None


def _derive_checklist_compliance(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("checklist_compliance_rate")
    if direct is not None:
        return direct
    suffix_pairs: Sequence[tuple[str, Sequence[str]]] = (
        ("_compliant_total", ("_total", "_count")),
        ("_compliant_count", ("_count", "_total")),
        ("_checked_total", ("_total", "_count")),
    )
    for numerator_suffix, denominator_suffixes in suffix_pairs:
        for name, value in raw.items():
            if not name.endswith(numerator_suffix):
                continue
            base = name[: -len(numerator_suffix)]
            numerator = value
            for suffix in denominator_suffixes:
                denominator_key = f"{base}{suffix}"
                denominator = raw.get(denominator_key)
                if denominator in (None, 0.0):
                    continue
                return numerator / denominator
    ratio = _derive_ratio_by_suffixes(
        raw,
        ("_compliant",),
        ("_total", "_count", "_all"),
    )
    if ratio is not None:
        return ratio
    return None


def _derive_average(
    raw: Mapping[str, float], prefixes: Sequence[tuple[str, float]]
) -> float | None:
    for prefix, scale in prefixes:
        sum_key = f"{prefix}_sum"
        count_key = f"{prefix}_count"
        total = raw.get(sum_key)
        count = raw.get(count_key)
        if total is None or count in (None, 0.0):
            continue
        return (total / count) / scale
    return None


def _derive_task_seed_cycle_time_minutes(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("task_seed_cycle_time_minutes")
    if direct is not None:
        return direct
    prefixes: Sequence[tuple[str, float]] = (
        ("task_seed_cycle_time_seconds", 60.0),
        ("docops_task_seed_cycle_time_seconds", 60.0),
        ("task_seed_cycle_time_minutes", 1.0),
    )
    return _derive_average(raw, prefixes)


def _derive_birdseye_refresh_delay_minutes(raw: Mapping[str, float]) -> float | None:
    direct = raw.get("birdseye_refresh_delay_minutes")
    if direct is not None:
        return direct
    prefixes: Sequence[tuple[str, float]] = (
        ("birdseye_refresh_delay_seconds", 60.0),
        ("docops_birdseye_refresh_delay_seconds", 60.0),
        ("birdseye_refresh_delay_minutes", 1.0),
    )
    return _derive_average(raw, prefixes)


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
    _capture_trim_metrics(raw, metrics)

    _capture_review_latency(raw, metrics)

    compliance = _derive_checklist_compliance(raw)
    if compliance is not None and "checklist_compliance_rate" not in metrics:
        metrics["checklist_compliance_rate"] = compliance

    task_seed_cycle_time = _derive_task_seed_cycle_time_minutes(raw)
    if (
        task_seed_cycle_time is not None
        and "task_seed_cycle_time_minutes" not in metrics
    ):
        metrics["task_seed_cycle_time_minutes"] = task_seed_cycle_time

    birdseye_delay = _derive_birdseye_refresh_delay_minutes(raw)
    if (
        birdseye_delay is not None
        and "birdseye_refresh_delay_minutes" not in metrics
    ):
        metrics["birdseye_refresh_delay_minutes"] = birdseye_delay

    for metric_key, (numerator_suffixes, denominator_suffixes, prefixes) in _RATIO_PROMETHEUS_CONFIG.items():
        if metric_key in metrics:
            continue
        derived = _derive_ratio_metric(
            raw,
            metric_key,
            numerator_suffixes=numerator_suffixes,
            denominator_suffixes=denominator_suffixes,
            prefixes=prefixes,
        )
        if derived is not None:
            metrics[metric_key] = derived

    return metrics


def _load_prometheus(metrics_url: str) -> Mapping[str, float]:
    try:
        with urllib.request.urlopen(metrics_url) as response:  # type: ignore[arg-type]
            payload = response.read()
    except OSError as exc:  # urllib.request raises URLError, an OSError subclass
        raise MetricsCollectionError(f"Failed to read metrics from {metrics_url}: {exc}") from exc
    return _parse_prometheus(payload.decode("utf-8"))


def _load_structured_log(path: Path) -> Mapping[str, float]:
    if not path.exists():
        raise MetricsCollectionError(f"Structured log not found: {path}")
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
            _capture_trim_metrics(parsed, metrics)
            _capture_review_latency(parsed, metrics, overwrite=True)
            _capture_compliance(parsed, metrics, overwrite=True)
            for metric_key, numerator_keys, denominator_keys in _RATIO_CAPTURE_ENTRIES:
                _capture_ratio_metric(
                    parsed,
                    metrics,
                    metric_key,
                    numerator_keys,
                    denominator_keys,
                    overwrite=True,
                )
            nested = parsed.get("metrics")
            if isinstance(nested, Mapping):
                _capture(nested, metrics)
                _capture_trim_metrics(nested, metrics, overwrite=True)
                _capture_review_latency(nested, metrics, overwrite=True)
                _capture_compliance(nested, metrics, overwrite=True)
                for metric_key, numerator_keys, denominator_keys in _RATIO_CAPTURE_ENTRIES:
                    _capture_ratio_metric(
                        nested,
                        metrics,
                        metric_key,
                        numerator_keys,
                        denominator_keys,
                        overwrite=True,
                    )
    return metrics


def _merge(sources: Iterable[Mapping[str, float]]) -> dict[str, float]:
    combined: dict[str, float] = {}
    for mapping in sources:
        _capture(mapping, combined)
        if "checklist_compliance_rate" in mapping:
            combined["checklist_compliance_rate"] = mapping["checklist_compliance_rate"]
        if "review_latency" in mapping:
            combined["review_latency"] = mapping["review_latency"]
        if "compress_ratio" in mapping:
            combined["compress_ratio"] = mapping["compress_ratio"]
        if "semantic_retention" in mapping:
            combined["semantic_retention"] = mapping["semantic_retention"]
        if "reopen_rate" in mapping:
            combined["reopen_rate"] = mapping["reopen_rate"]
        if "spec_completeness" in mapping:
            combined["spec_completeness"] = mapping["spec_completeness"]
    missing = [key for key in METRIC_KEYS if key not in combined]
    if missing:
        raise MetricsCollectionError("Missing metrics: " + ", ".join(missing))
    metrics = {key: combined[key] for key in METRIC_KEYS}
    for key in PERCENTAGE_KEYS:
        metrics[key] *= 100.0
    return metrics


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
        sources.append(_load_structured_log(log_path))
    if not sources:
        raise MetricsCollectionError("At least one of --metrics-url or --log-path is required")
    return _merge(sources)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect performance metrics for post-processing")
    parser.add_argument("--suite", choices=sorted(SUITES), help="Preset input/output configuration")
    parser.add_argument("--metrics-url", help="Prometheus metrics endpoint URL")
    parser.add_argument(
        "--log-path",
        type=Path,
        help="Path to structured operations log",
    )
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
