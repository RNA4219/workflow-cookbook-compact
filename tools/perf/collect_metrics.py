# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 RNA4219

from __future__ import annotations

import argparse
import functools
import json
import logging
import os
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, MutableMapping, Protocol, Sequence

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal env
    class _MiniYamlModule:
        @staticmethod
        def safe_load(content: str) -> dict[str, str]:
            result: dict[str, str] = {}
            for line in content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                key, _, value = stripped.partition(":")
                result[key.strip()] = value.strip()
            return result

    yaml = _MiniYamlModule()  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)
_METRICS_PATH_ENV = "GOVERNANCE_METRICS_PATH"
_DEFAULT_METRICS_PATH = Path(__file__).resolve().parents[2] / "governance/metrics.yaml"

_TRIM_COMPRESS_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_compress_ratio", 1.0),
    ("context_compression_ratio", 1.0),
)

_TRIM_SEMANTIC_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_semantic_retention", 1.0),
    ("context_semantic_retention", 1.0),
)

REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("trim_review_latency_seconds", 3600.0),
    ("trim_review_latency_minutes", 60.0),
    ("review_latency_seconds", 3600.0),
    ("review_latency_minutes", 60.0),
    ("trim_review_latency_hours", 1.0),
    ("review_latency_hours", 1.0),
)

WORKFLOW_REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("workflow_review_latency_seconds", 3600.0),
    ("workflow_review_latency_minutes", 60.0),
    ("workflow_review_latency_hours", 1.0),
)

_LEGACY_REVIEW_LATENCY_PREFIXES: Sequence[tuple[str, float]] = (
    ("legacy_review_latency_seconds", 3600.0),
    ("legacy_review_latency_minutes", 60.0),
    ("legacy_review_latency_hours", 1.0),
)

# Prefer the workflow_review_* prefixed aggregates; keep legacy_* as a
# compatibility fallback so existing exporters continue to work.
_REVIEW_LATENCY_AGGREGATE_PREFIXES: tuple[tuple[str, float], ...] = (
    *WORKFLOW_REVIEW_LATENCY_PREFIXES,
    *REVIEW_LATENCY_PREFIXES,
    *_LEGACY_REVIEW_LATENCY_PREFIXES,
)

_OVERWRITE_KEYS: frozenset[str] = frozenset(
    {
        "checklist_compliance_rate",
        "review_latency",
        "compress_ratio",
        "semantic_retention",
        "reopen_rate",
        "spec_completeness",
    }
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


class StructuredRule(Protocol):
    overwrite: bool

    def extract(self, metric_key: str, source: Mapping[str, object]) -> float | None:
        ...


class NumericRule(Protocol):
    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        ...


@dataclass(frozen=True)
class DirectValueRule:
    keys: tuple[str, ...] | None = None
    overwrite: bool = False

    def extract(self, metric_key: str, source: Mapping[str, object]) -> float | None:
        candidates = self.keys or (metric_key,)
        for key in candidates:
            value = _coerce_float(source.get(key))
            if value is not None:
                return value
        return None


@dataclass(frozen=True)
class MappingRatioRule:
    numerator_keys: tuple[str, ...]
    denominator_keys: tuple[str, ...]
    ratio_keys: tuple[str, ...] = ("ratio",)
    overwrite: bool = True

    def extract(self, metric_key: str, source: Mapping[str, object]) -> float | None:
        raw = source.get(metric_key)
        if not isinstance(raw, Mapping):
            return None
        numerator = None
        denominator = None
        for candidate in self.numerator_keys:
            numerator = _coerce_float(raw.get(candidate))
            if numerator is not None:
                break
        for candidate in self.denominator_keys:
            denominator = _coerce_float(raw.get(candidate))
            if denominator is not None and denominator != 0:
                break
        if numerator is not None and denominator is not None and denominator != 0:
            return numerator / denominator
        for candidate in self.ratio_keys:
            ratio = _coerce_float(raw.get(candidate))
            if ratio is not None:
                return ratio
        return None


@dataclass(frozen=True)
class StructuredAverageRule:
    prefixes: tuple[tuple[str, float], ...]
    overwrite: bool = False

    def extract(self, metric_key: str, source: Mapping[str, object]) -> float | None:
        numeric = _coerce_numeric_mapping(source)
        if not numeric:
            return None
        return _derive_average(numeric, self.prefixes)


@dataclass(frozen=True)
class DirectNumericRule:
    keys: tuple[str, ...] | None = None

    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        candidates = self.keys or (metric_key,)
        for key in candidates:
            value = source.get(key)
            if value is not None:
                return value
        return None


@dataclass(frozen=True)
class NumericAverageRule:
    prefixes: tuple[tuple[str, float], ...]

    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        return _derive_average(source, self.prefixes)


@dataclass(frozen=True)
class SuffixRatioNumericRule:
    numerator_suffixes: tuple[str, ...]
    denominator_suffixes: tuple[str, ...]

    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        return _derive_ratio_by_suffixes(source, self.numerator_suffixes, self.denominator_suffixes)


@dataclass(frozen=True)
class NumericCallableRule:
    function: Callable[[Mapping[str, float]], float | None]

    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        return self.function(source)


@dataclass(frozen=True)
class PrecisionModeStructuredRule:
    source_key: str
    mode: str
    nested_keys: tuple[str, ...] = ("rate", "modes")
    overwrite: bool = False

    def extract(self, metric_key: str, source: Mapping[str, object]) -> float | None:
        raw = source.get(self.source_key)
        if not isinstance(raw, Mapping):
            return None
        value = _extract_precision_mode_mapping(raw, self.mode, self.nested_keys)
        if value is not None:
            return value
        return None


@dataclass(frozen=True)
class PrecisionModeNumericRule:
    metric_name: str
    mode: str
    fallback_keys: tuple[str, ...] = ()

    def extract(self, metric_key: str, source: Mapping[str, float]) -> float | None:
        label_key = _precision_mode_label_key(self.metric_name, self.mode)
        value = source.get(label_key)
        if value is not None:
            return value
        for key in self.fallback_keys:
            fallback = source.get(key)
            if fallback is not None:
                return fallback
        return None


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    structured_rules: tuple[StructuredRule, ...]
    numeric_rules: tuple[NumericRule, ...]
    required: bool = True


class MetricExtractor:
    def __init__(
        self,
        definitions: Sequence[MetricDefinition],
        *,
        percentage_keys: Sequence[str],
    ) -> None:
        self._definitions = {definition.key: definition for definition in definitions}
        self._ordered_keys = tuple(definition.key for definition in definitions)
        self._ordered_definitions = tuple(definitions)
        self._percentage_keys = tuple(percentage_keys)
        self._key_set = frozenset(self._ordered_keys)

    def capture_structured(
        self,
        source: Mapping[str, object],
        target: MutableMapping[str, float],
        *,
        overwrite: bool = False,
    ) -> None:
        for definition in self._ordered_definitions:
            existing = definition.key in target
            for rule in definition.structured_rules:
                if existing and not (overwrite or rule.overwrite):
                    continue
                value = rule.extract(definition.key, source)
                if value is not None:
                    target[definition.key] = value
                    existing = True
                    break

    def capture_numeric(
        self,
        source: Mapping[str, float],
        target: MutableMapping[str, float],
    ) -> None:
        for definition in self._ordered_definitions:
            if definition.key in target:
                continue
            for rule in definition.numeric_rules:
                value = rule.extract(definition.key, source)
                if value is not None:
                    target[definition.key] = value
                    break

    def merge(self, sources: Iterable[Mapping[str, float]]) -> dict[str, float]:
        combined: dict[str, float] = {}
        reported_unexpected: set[str] = set()
        for mapping in sources:
            unexpected = [
                key for key in mapping if key not in self._key_set and key not in reported_unexpected
            ]
            if unexpected:
                reported_unexpected.update(unexpected)
                LOGGER.warning(
                    "Ignoring metrics not defined in governance/metrics.yaml: %s",
                    ", ".join(sorted(unexpected)),
                )
            for definition in self._ordered_definitions:
                key = definition.key
                if key in mapping and key not in combined:
                    combined[key] = mapping[key]
            for key in _OVERWRITE_KEYS:
                if key in mapping:
                    combined[key] = mapping[key]
        missing_required = [
            definition.key
            for definition in self._ordered_definitions
            if definition.required and definition.key not in combined
        ]
        if missing_required:
            raise MetricsCollectionError("Missing metrics: " + ", ".join(missing_required))
        metrics = {
            definition.key: combined[definition.key]
            for definition in self._ordered_definitions
            if definition.key in combined
        }
        for key in self._percentage_keys:
            if key in metrics:
                metrics[key] *= 100.0
        return metrics

    def percentage_keys(self) -> tuple[str, ...]:
        return self._percentage_keys


def _coerce_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _coerce_numeric_mapping(source: Mapping[str, object]) -> dict[str, float]:
    numeric: dict[str, float] = {}
    for key, value in source.items():
        if isinstance(value, Mapping):
            continue
        coerced = _coerce_float(value)
        if coerced is not None:
            numeric[key] = coerced
    return numeric


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


def _extract_precision_mode_mapping(
    raw: Mapping[str, object], mode: str, nested_keys: Sequence[str]
) -> float | None:
    direct = _coerce_float(raw.get(mode))
    if direct is not None:
        return direct
    for nested_key in nested_keys:
        nested = raw.get(nested_key)
        if isinstance(nested, Mapping):
            nested_value = _coerce_float(nested.get(mode))
            if nested_value is not None:
                return nested_value
    return None


def _precision_mode_label_key(metric_name: str, mode: str) -> str:
    return f"{metric_name}|precision_mode={mode}"


def _parse_metric_name_and_labels(name_token: str) -> tuple[str, dict[str, str]]:
    if "{" not in name_token:
        return name_token, {}
    base, _, remainder = name_token.partition("{")
    labels: dict[str, str] = {}
    for chunk in remainder.rstrip("}").split(","):
        stripped = chunk.strip()
        if not stripped:
            continue
        key, _, raw_value = stripped.partition("=")
        if not raw_value:
            continue
        value = raw_value.strip().strip('"')
        labels[key.strip()] = value
    return base, labels


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


_BASE_METRIC_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        key="checklist_compliance_rate",
        structured_rules=(
            DirectValueRule(),
            MappingRatioRule(
                numerator_keys=("compliant", "checked", "passing", "numerator"),
                denominator_keys=("total", "denominator", "all", "overall"),
            ),
        ),
        numeric_rules=(
            DirectNumericRule(),
            NumericCallableRule(_derive_checklist_compliance),
        ),
    ),
    MetricDefinition(
        key="task_seed_cycle_time_minutes",
        structured_rules=(
            DirectValueRule(),
        ),
        numeric_rules=(
            DirectNumericRule(),
            NumericCallableRule(_derive_task_seed_cycle_time_minutes),
        ),
    ),
    MetricDefinition(
        key="birdseye_refresh_delay_minutes",
        structured_rules=(
            DirectValueRule(),
        ),
        numeric_rules=(
            DirectNumericRule(),
            NumericCallableRule(_derive_birdseye_refresh_delay_minutes),
        ),
    ),
    MetricDefinition(
        key="review_latency",
        structured_rules=(
            DirectValueRule(keys=("workflow_review_latency", "review_latency")),
            StructuredAverageRule(
                prefixes=tuple(_REVIEW_LATENCY_AGGREGATE_PREFIXES),
                overwrite=True,
            ),
        ),
        numeric_rules=(
            DirectNumericRule(),
            NumericCallableRule(_derive_review_latency),
        ),
    ),
    MetricDefinition(
        key="compress_ratio",
        structured_rules=(
            DirectValueRule(
                keys=(
                    "trim_compress_ratio_avg",
                    "trim_compress_ratio",
                    "compress_ratio",
                    "compression_ratio",
                )
            ),
            StructuredAverageRule(
                prefixes=tuple(_TRIM_COMPRESS_PREFIXES),
                overwrite=True,
            ),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("trim_compress_ratio_avg", "trim_compress_ratio", "compress_ratio"),
            ),
            NumericAverageRule(prefixes=tuple(_TRIM_COMPRESS_PREFIXES)),
        ),
    ),
    MetricDefinition(
        key="semantic_retention",
        structured_rules=(
            DirectValueRule(
                keys=(
                    "trim_semantic_retention_avg",
                    "trim_semantic_retention",
                    "semantic_retention",
                )
            ),
            StructuredAverageRule(
                prefixes=tuple(_TRIM_SEMANTIC_PREFIXES),
                overwrite=True,
            ),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=(
                    "trim_semantic_retention_avg",
                    "trim_semantic_retention",
                    "semantic_retention",
                ),
            ),
            NumericAverageRule(prefixes=tuple(_TRIM_SEMANTIC_PREFIXES)),
        ),
    ),
    MetricDefinition(
        key="reopen_rate",
        structured_rules=(
            DirectValueRule(
                keys=(
                    "workflow_reopen_rate_avg",
                    "workflow_reopen_rate",
                    "docops_reopen_rate",
                    "reopen_rate",
                )
            ),
            MappingRatioRule(
                numerator_keys=("reopened", "reopens", "numerator"),
                denominator_keys=("total", "resolved", "all", "denominator"),
            ),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=(
                    "workflow_reopen_rate_avg",
                    "workflow_reopen_rate",
                    "docops_reopen_rate",
                    "reopen_rate",
                ),
            ),
            SuffixRatioNumericRule(
                numerator_suffixes=("_reopened", "_reopen"),
                denominator_suffixes=("_total", "_count", "_closed", "_all"),
            ),
            NumericAverageRule(
                prefixes=(
                    ("workflow_reopen_rate", 1.0),
                    ("workflow_reopen_rate_avg", 1.0),
                    ("docops_reopen_rate", 1.0),
                    ("reopen_rate", 1.0),
                )
            ),
        ),
    ),
    MetricDefinition(
        key="spec_completeness",
        structured_rules=(
            DirectValueRule(
                keys=(
                    "workflow_spec_completeness_ratio_avg",
                    "workflow_spec_completeness_avg",
                    "workflow_spec_completeness_ratio",
                    "workflow_spec_completeness",
                    "spec_completeness_ratio",
                    "spec_completeness",
                )
            ),
            MappingRatioRule(
                numerator_keys=("with_spec", "with_specs", "completed", "numerator"),
                denominator_keys=("total", "all", "denominator"),
            ),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=(
                    "workflow_spec_completeness_ratio_avg",
                    "workflow_spec_completeness_avg",
                    "workflow_spec_completeness_ratio",
                    "workflow_spec_completeness",
                    "spec_completeness_ratio",
                    "spec_completeness",
                ),
            ),
            SuffixRatioNumericRule(
                numerator_suffixes=("_with_spec", "_with_specs", "_completed"),
                denominator_suffixes=("_total", "_count", "_all"),
            ),
            NumericAverageRule(
                prefixes=(
                    ("workflow_spec_completeness_ratio", 1.0),
                    ("workflow_spec_completeness_ratio_avg", 1.0),
                    ("workflow_spec_completeness", 1.0),
                    ("spec_completeness_ratio", 1.0),
                    ("spec_completeness", 1.0),
                )
            ),
        ),
    ),
    MetricDefinition(
        key="merge_success_rate_baseline",
        structured_rules=(
            DirectValueRule(
                keys=("merge_success_rate_baseline", "merge.success.rate.baseline"),
            ),
            PrecisionModeStructuredRule(source_key="merge.success.rate", mode="baseline"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_success_rate_baseline", "merge.success.rate.baseline"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.success.rate",
                mode="baseline",
                fallback_keys=("merge.success.rate.baseline",),
            ),
        ),
        required=False,
    ),
    MetricDefinition(
        key="merge_success_rate_strict",
        structured_rules=(
            DirectValueRule(
                keys=("merge_success_rate_strict", "merge.success.rate.strict"),
            ),
            PrecisionModeStructuredRule(source_key="merge.success.rate", mode="strict"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_success_rate_strict", "merge.success.rate.strict"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.success.rate",
                mode="strict",
                fallback_keys=("merge.success.rate.strict",),
            ),
        ),
        required=False,
    ),
    MetricDefinition(
        key="merge_conflict_rate_baseline",
        structured_rules=(
            DirectValueRule(
                keys=("merge_conflict_rate_baseline", "merge.conflict.rate.baseline"),
            ),
            PrecisionModeStructuredRule(source_key="merge.conflict.rate", mode="baseline"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_conflict_rate_baseline", "merge.conflict.rate.baseline"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.conflict.rate",
                mode="baseline",
                fallback_keys=("merge.conflict.rate.baseline",),
            ),
        ),
        required=False,
    ),
    MetricDefinition(
        key="merge_conflict_rate_strict",
        structured_rules=(
            DirectValueRule(
                keys=("merge_conflict_rate_strict", "merge.conflict.rate.strict"),
            ),
            PrecisionModeStructuredRule(source_key="merge.conflict.rate", mode="strict"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_conflict_rate_strict", "merge.conflict.rate.strict"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.conflict.rate",
                mode="strict",
                fallback_keys=("merge.conflict.rate.strict",),
            ),
        ),
        required=False,
    ),
    MetricDefinition(
        key="merge_autosave_lag_ms_baseline",
        structured_rules=(
            DirectValueRule(
                keys=("merge_autosave_lag_ms_baseline", "merge.autosave.lag_ms.baseline"),
            ),
            PrecisionModeStructuredRule(source_key="merge.autosave.lag_ms", mode="baseline"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_autosave_lag_ms_baseline", "merge.autosave.lag_ms.baseline"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.autosave.lag_ms",
                mode="baseline",
                fallback_keys=("merge.autosave.lag_ms.baseline",),
            ),
        ),
        required=False,
    ),
    MetricDefinition(
        key="merge_autosave_lag_ms_strict",
        structured_rules=(
            DirectValueRule(
                keys=("merge_autosave_lag_ms_strict", "merge.autosave.lag_ms.strict"),
            ),
            PrecisionModeStructuredRule(source_key="merge.autosave.lag_ms", mode="strict"),
        ),
        numeric_rules=(
            DirectNumericRule(
                keys=("merge_autosave_lag_ms_strict", "merge.autosave.lag_ms.strict"),
            ),
            PrecisionModeNumericRule(
                metric_name="merge.autosave.lag_ms",
                mode="strict",
                fallback_keys=("merge.autosave.lag_ms.strict",),
            ),
        ),
        required=False,
    ),
)

_KNOWN_METRIC_DEFINITIONS: Mapping[str, MetricDefinition] = {
    definition.key: definition for definition in _BASE_METRIC_DEFINITIONS
}


@dataclass(frozen=True)
class _LoadedMetrics:
    extractor: MetricExtractor
    keys: tuple[str, ...]


@functools.lru_cache(maxsize=1)
def _load_metric_config() -> _LoadedMetrics:
    override = os.environ.get(_METRICS_PATH_ENV)
    if override:
        candidate = Path(override)
        path = candidate if candidate.is_absolute() else (_DEFAULT_METRICS_PATH.parent / candidate)
    else:
        path = _DEFAULT_METRICS_PATH
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MetricsCollectionError(f"Metrics definition file not found: {path}") from exc
    try:
        loaded = yaml.safe_load(content)
    except Exception as exc:  # pragma: no cover - PyYAML specific errors
        raise MetricsCollectionError(f"Failed to parse metrics definition from {path}: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, Mapping):
        raise MetricsCollectionError(f"Metrics definition in {path} must be a mapping")
    keys: list[str] = []
    percentage_keys: list[str] = []
    definitions: list[MetricDefinition] = []
    missing: list[str] = []
    for raw_key, raw_description in loaded.items():
        key = str(raw_key)
        keys.append(key)
        description = "" if raw_description is None else str(raw_description)
        if "(%)" in description:
            percentage_keys.append(key)
        definition = _KNOWN_METRIC_DEFINITIONS.get(key)
        if definition is None:
            missing.append(key)
        else:
            definitions.append(definition)
    if missing:
        raise MetricsCollectionError(
            "Missing metric extractor definitions for: " + ", ".join(sorted(missing))
        )
    extractor = MetricExtractor(tuple(definitions), percentage_keys=tuple(percentage_keys))
    return _LoadedMetrics(extractor=extractor, keys=tuple(keys))


def _metrics() -> _LoadedMetrics:
    return _load_metric_config()


def metric_keys() -> tuple[str, ...]:
    return _metrics().keys


def percentage_keys() -> tuple[str, ...]:
    return _metrics().extractor.percentage_keys()


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
        metric_name, labels = _parse_metric_name_and_labels(name_token)
        value = _coerce_float(raw_value)
        if value is None:
            continue
        raw[metric_name] = raw.get(metric_name, 0.0) + value
        precision_mode = labels.get("precision_mode") if labels else None
        if precision_mode:
            label_key = _precision_mode_label_key(metric_name, precision_mode)
            raw[label_key] = raw.get(label_key, 0.0) + value

    metrics: dict[str, float] = {}
    _metrics().extractor.capture_numeric(raw, metrics)
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
            _metrics().extractor.capture_structured(parsed, metrics)
            statistics = parsed.get("statistics")
            if isinstance(statistics, Mapping):
                _metrics().extractor.capture_structured(statistics, metrics)
            nested = parsed.get("metrics")
            if isinstance(nested, Mapping):
                _metrics().extractor.capture_structured(nested, metrics, overwrite=True)
                statistics = nested.get("statistics")
                if isinstance(statistics, Mapping):
                    _metrics().extractor.capture_structured(statistics, metrics, overwrite=True)
    return metrics


def _merge(sources: Iterable[Mapping[str, float]]) -> dict[str, float]:
    return _metrics().extractor.merge(sources)


def _format_pushgateway_payload(metrics: Mapping[str, float]) -> bytes:
    keys = _metrics().keys
    lines = [f"{key} {format(metrics[key], 'g')}" for key in keys if key in metrics]
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
