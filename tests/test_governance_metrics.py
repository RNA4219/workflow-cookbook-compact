"""governance.metrics.yaml の内容を検証するテスト。"""

import sys
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from tools.perf.collect_metrics import METRIC_KEYS, PERCENTAGE_KEYS

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal env
    class _MiniYamlModule:
        @staticmethod
        def safe_load(content: str) -> Dict[str, str]:
            result: Dict[str, str] = {}
            for line in content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                key, _, value = stripped.partition(":")
                result[key.strip()] = value.strip()
            return result

    yaml = _MiniYamlModule()  # type: ignore[assignment]


def test_governance_metrics_contains_required_keys() -> None:
    metrics_path = Path("governance/metrics.yaml")
    metrics_data = yaml.safe_load(metrics_path.read_text(encoding="utf-8"))

    assert isinstance(metrics_data, dict)

    expected_keys = set(METRIC_KEYS)
    actual_keys = set(metrics_data)

    missing_keys = expected_keys - actual_keys
    assert not missing_keys, "Missing metrics: " + ", ".join(sorted(missing_keys))


def test_governance_scale_annotations_match_percentage_keys() -> None:
    metrics_path = Path("governance/metrics.yaml")
    metrics_data = yaml.safe_load(metrics_path.read_text(encoding="utf-8"))

    assert isinstance(metrics_data, dict)

    annotated_percent = {
        key for key, description in metrics_data.items() if "(%)" in str(description)
    }
    annotated_zero_to_one = {
        key for key, description in metrics_data.items() if "(0-1)" in str(description)
    }

    percentage_keys = set(PERCENTAGE_KEYS)

    assert annotated_percent <= percentage_keys
    assert annotated_zero_to_one.isdisjoint(annotated_percent)
    for key in percentage_keys:
        assert key in annotated_percent or key in annotated_zero_to_one
