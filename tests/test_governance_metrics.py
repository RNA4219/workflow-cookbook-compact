"""governance.metrics.yaml の内容を検証するテスト。"""

import sys
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from tools.perf.collect_metrics import METRIC_KEYS

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
    for key in METRIC_KEYS:
        assert key in metrics_data, f"Missing metric: {key}"
