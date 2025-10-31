from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest

from tools.context.pack import (
    DEFAULT_CONFIG,
    assemble_sections,
    build_graph_view,
    ContextPackPlanner,
    load_config,
    pack_graph,
    score_candidates,
)
from tools.context.pack import _recency_score


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


def test_context_pack_plan_candidates_and_budget(sample_graph: Path) -> None:
    planner = ContextPackPlanner()
    plan = planner.build_plan(
        graph_path=sample_graph,
        intent="INT-9 implement rollout",
        budget_tokens=400,
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )

    assert plan.target_candidates[:3] == [
        "docs/b.md#ops",
        "docs/a.md#impl",
        "docs/a.md#root",
    ]
    assert plan.budget_remaining == 20


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


def test_build_graph_view_base_signals(sample_graph: Path) -> None:
    graph = json.loads(sample_graph.read_text())
    view = build_graph_view(
        graph=graph,
        intent="INT-9 implement rollout",
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )

    signals_ops = view.base_signals["docs/b.md#ops"]
    signals_root = view.base_signals["docs/a.md#root"]
    signals_impl = view.base_signals["docs/a.md#impl"]

    assert signals_ops.diff == pytest.approx(1.0)
    assert signals_root.diff == pytest.approx(0.7)
    assert signals_impl.diff == pytest.approx(0.7)
    expected_recency_ops = _recency_score(
        graph["nodes"][2]["mtime"], view.intent_profile.halflife
    )
    assert signals_ops.recency == pytest.approx(expected_recency_ops, rel=1e-6)
    assert signals_root.hub == pytest.approx(1.0)
    assert signals_ops.hub == pytest.approx(0.0)
    assert signals_ops.role == pytest.approx(0.4)


def test_score_candidates_respects_existing_ordering(sample_graph: Path) -> None:
    graph = json.loads(sample_graph.read_text())
    view = build_graph_view(
        graph=graph,
        intent="INT-9 implement rollout",
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )

    ranking = score_candidates(view=view, config=DEFAULT_CONFIG)

    candidate_ids = [node["id"] for node in ranking.candidate_nodes]
    assert candidate_ids == [
        "docs/a.md#root",
        "docs/a.md#impl",
        "docs/b.md#ops",
    ]
    assert ranking.ppr_scores["docs/b.md#ops"] >= ranking.ppr_scores["docs/a.md#root"]


def test_assemble_sections_matches_pack_graph(sample_graph: Path) -> None:
    graph = json.loads(sample_graph.read_text())
    view = build_graph_view(
        graph=graph,
        intent="INT-9 implement rollout",
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )
    ranking = score_candidates(view=view, config=DEFAULT_CONFIG)
    assembly = assemble_sections(
        view=view,
        ranking=ranking,
        budget_tokens=400,
        config=DEFAULT_CONFIG,
    )

    result = pack_graph(
        graph_path=sample_graph,
        intent="INT-9 implement rollout",
        budget_tokens=400,
        diff_paths=["docs/b.md"],
        config=DEFAULT_CONFIG,
    )

    for helper_section, packed_section in zip(assembly.sections, result["sections"]):
        assert helper_section["id"] == packed_section["id"]
        assert helper_section["tok"] == packed_section["tok"]
        assert helper_section["filters"] == packed_section["filters"]
        for key in ["intent", "diff", "recency", "hub", "role", "ppr", "score"]:
            assert helper_section["why"][key] == pytest.approx(
                packed_section["why"][key], rel=1e-6, abs=1e-9
            )
    for key, value in assembly.metrics.items():
        assert value == pytest.approx(result["metrics"][key], rel=1e-6, abs=1e-9)


def test_cli_main_emits_pack_output(
    tmp_path: Path, sample_graph: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    diff_path = tmp_path / "diff.txt"
    diff_path.write_text("docs/b.md\n")
    output_path = tmp_path / "pack.json"

    expected = pack_graph(
        graph_path=sample_graph,
        intent="INT-9 implement rollout",
        budget_tokens=400,
        diff_paths=["docs/b.md"],
        config=None,
    )

    args = [
        "context-pack",
        "--graph",
        str(sample_graph),
        "--intent",
        "INT-9 implement rollout",
        "--budget",
        "400",
        "--diff",
        str(diff_path),
        "--output",
        str(output_path),
    ]
    monkeypatch.setattr(sys, "argv", args)

    from tools.context import pack as pack_module

    pack_module.main()

    result = json.loads(output_path.read_text())

    assert result["intent"] == expected["intent"]
    assert result["budget"] == expected["budget"]
    assert len(result["sections"]) == len(expected["sections"])
    for res_section, exp_section in zip(result["sections"], expected["sections"]):
        assert res_section["id"] == exp_section["id"]
        assert res_section["tok"] == exp_section["tok"]
        assert res_section["filters"] == exp_section["filters"]
        for key in ["intent", "diff", "recency", "hub", "role", "ppr", "score"]:
            assert res_section["why"][key] == pytest.approx(
                exp_section["why"][key], rel=1e-6, abs=1e-9
            )
    for key, value in result["metrics"].items():
        assert value == pytest.approx(expected["metrics"][key], rel=1e-6, abs=1e-9)
