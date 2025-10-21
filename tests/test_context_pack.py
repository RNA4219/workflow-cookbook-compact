from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from tools.context.pack import DEFAULT_CONFIG, pack_graph, load_config


def _recent(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


@pytest.fixture()
def sample_graph(tmp_path: Path) -> Path:
    graph = {
        "nodes": [
            {
                "id": "docs/a.md#root",
                "path": "docs/a.md",
                "heading": "Root Overview",
                "depth": 1,
                "mtime": _recent(5),
                "token_estimate": 180,
                "role": "spec",
            },
            {
                "id": "docs/a.md#impl",
                "path": "docs/a.md",
                "heading": "Implementation Notes",
                "depth": 2,
                "mtime": _recent(10),
                "token_estimate": 220,
                "role": "impl",
            },
            {
                "id": "docs/b.md#ops",
                "path": "docs/b.md",
                "heading": "Operational Guide",
                "depth": 2,
                "mtime": _recent(2),
                "token_estimate": 200,
                "role": "ops",
            },
        ],
        "edges": [
            {"src": "docs/a.md#root", "dst": "docs/a.md#impl", "type": "parent"},
            {"src": "docs/a.md#impl", "dst": "docs/b.md#ops", "type": "link"},
        ],
        "meta": {"generated_at": "now", "version": "1"},
    }
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph))
    return path


def test_pack_graph_prioritises_ppr(sample_graph: Path) -> None:
    result = pack_graph(
        graph_path=sample_graph,
        intent="INT-9 implement rollout",
        budget_tokens=400,
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )

    assert result["intent"] == "INT-9 implement rollout"
    sections = result["sections"]
    assert sections, "sections should not be empty"
    assert sections[0]["id"] == "docs/b.md#ops"
    assert result["metrics"]["token_in"] <= 400
    pprs = [section["why"]["ppr"] for section in sections]
    assert pprs[0] >= max(pprs[1:]) if len(pprs) > 1 else pprs[0] > 0


def test_load_config_overrides_defaults(tmp_path: Path, sample_graph: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
pagerank:
  lambda: 0.70
  theta: 0.5
weights:
  intent: 0.5
limits:
  ncand: 10
        """.strip()
    )

    loaded = load_config(config_path)
    assert loaded["pagerank"]["lambda"] == 0.70
    assert loaded["weights"]["intent"] == 0.5
    assert loaded["limits"]["ncand"] == 10

    result = pack_graph(
        graph_path=sample_graph,
        intent="INT-42 ops",
        budget_tokens=600,
        diff_paths=[],
        config=loaded,
    )

    assert result["metrics"]["token_src"] >= result["metrics"]["token_in"]
