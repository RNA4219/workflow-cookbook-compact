from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.codemap import update


def test_ensure_python_version_exits(monkeypatch, capsys):
    monkeypatch.setattr(update, "sys", SimpleNamespace(version_info=(3, 10, 0)))

    with pytest.raises(SystemExit) as excinfo:
        update.ensure_python_version()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Python 3.11 or newer is required" in captured.out


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _caps_payload(cap_id: str, *, deps_out=None, deps_in=None) -> dict[str, object]:
    return {
        "id": cap_id,
        "role": "doc",
        "public_api": [],
        "summary": cap_id,
        "deps_out": list(deps_out or []),
        "deps_in": list(deps_in or []),
        "risks": [],
        "tests": [],
    }


def _prepare_birdseye(tmp_path, *, edges, caps_payloads, hot_entries, root=None):
    root = Path(root) if root is not None else tmp_path / "birdseye"
    caps_dir = root / "caps"
    caps_dir.mkdir(parents=True)
    nodes = {
        cap_id: {"role": payload.get("role", "doc"), "caps": f"docs/birdseye/caps/{cap_id}.json"}
        for cap_id, payload in caps_payloads.items()
    }
    index_path = root / "index.json"
    _write_json(
        index_path,
        {"generated_at": "2024-01-01T00:00:00Z", "nodes": nodes, "edges": edges},
    )
    cap_paths = {}
    for cap_id, payload in caps_payloads.items():
        cap_path = caps_dir / f"{cap_id}.json"
        cap_paths[cap_id] = cap_path
        _write_json(cap_path, payload)
    hot_path = root / "hot.json"
    _write_json(hot_path, {"generated_at": "2024-01-01T00:00:00Z", "entries": hot_entries})
    return root, index_path, hot_path, cap_paths


@pytest.mark.parametrize("dry_run", [False, True])
def test_run_update_refreshes_metadata_and_dependencies(tmp_path, monkeypatch, dry_run):
    caps_payloads = {
        "alpha.md": _caps_payload("alpha.md", deps_in=["obsolete"]),
        "beta.md": _caps_payload("beta.md", deps_out=["stale"]),
    }
    root, index_path, hot_path, cap_paths = _prepare_birdseye(
        tmp_path,
        edges=[["alpha.md", "beta.md"], ["beta.md", "alpha.md"]],
        caps_payloads=caps_payloads,
        hot_entries=["alpha.md"],
    )

    frozen_now = datetime(2025, 1, 1, 9, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(update, "utc_now", lambda: frozen_now)

    snapshots = None
    if dry_run:
        snapshots = {
            path: path.read_text(encoding="utf-8")
            for path in (index_path, hot_path, *cap_paths.values())
        }

    report = update.run_update(
        update.UpdateOptions(targets=(root,), emit="index+caps", dry_run=dry_run)
    )

    expected_timestamp = "2025-01-01T09:30:00Z"
    assert report.generated_at == expected_timestamp
    assert set(report.planned_writes) == {index_path, hot_path, *cap_paths.values()}

    if dry_run:
        assert report.performed_writes == ()
        assert snapshots is not None
        for path, before in snapshots.items():
            assert path.read_text(encoding="utf-8") == before
        return

    assert set(report.performed_writes) == {index_path, hot_path, *cap_paths.values()}

    refreshed_index = json.loads(index_path.read_text(encoding="utf-8"))
    assert refreshed_index["generated_at"] == expected_timestamp

    refreshed_alpha = json.loads(cap_paths["alpha.md"].read_text(encoding="utf-8"))
    assert refreshed_alpha["deps_out"] == ["beta.md"]
    assert refreshed_alpha["deps_in"] == ["beta.md"]

    refreshed_beta = json.loads(cap_paths["beta.md"].read_text(encoding="utf-8"))
    assert refreshed_beta["deps_out"] == ["alpha.md"]
    assert refreshed_beta["deps_in"] == ["alpha.md"]

    refreshed_hot = json.loads(hot_path.read_text(encoding="utf-8"))
    assert refreshed_hot["generated_at"] == expected_timestamp


def test_run_update_limits_caps_to_two_hop_scope(tmp_path, monkeypatch):
    caps_payloads = {
        cap_id: _caps_payload(cap_id, deps_out=["stale"], deps_in=["old"])
        for cap_id in ("alpha.md", "beta.md", "gamma.md", "delta.md", "epsilon.md")
    }
    root, index_path, hot_path, cap_paths = _prepare_birdseye(
        tmp_path,
        edges=[
            ["alpha.md", "beta.md"],
            ["beta.md", "gamma.md"],
            ["gamma.md", "delta.md"],
            ["delta.md", "epsilon.md"],
        ],
        caps_payloads=caps_payloads,
        hot_entries=[],
    )

    frozen_now = datetime(2025, 1, 2, tzinfo=timezone.utc)
    monkeypatch.setattr(update, "utc_now", lambda: frozen_now)

    report = update.run_update(
        update.UpdateOptions(targets=(cap_paths["beta.md"],), emit="caps", dry_run=False)
    )

    expected_caps = {
        cap_paths[cap_id]
        for cap_id in ("alpha.md", "beta.md", "gamma.md", "delta.md")
    }
    assert set(report.planned_writes) == expected_caps
    assert set(report.performed_writes) == expected_caps

    expected_deps = {
        "alpha.md": (["beta.md"], []),
        "beta.md": (["gamma.md"], ["alpha.md"]),
        "gamma.md": (["delta.md"], ["beta.md"]),
        "delta.md": (["epsilon.md"], ["gamma.md"]),
    }
    for cap_id, (deps_out, deps_in) in expected_deps.items():
        refreshed = json.loads(cap_paths[cap_id].read_text(encoding="utf-8"))
        assert refreshed["deps_out"] == deps_out
        assert refreshed["deps_in"] == deps_in


def test_parse_args_supports_since_and_limits_scope(tmp_path, monkeypatch):
    caps_payloads = {
        cap_id: _caps_payload(cap_id, deps_out=["stale"], deps_in=["old"])
        for cap_id in (
            "alpha.md",
            "beta.md",
            "gamma.md",
            "delta.md",
            "epsilon.md",
            "zeta.md",
        )
    }
    root_base = tmp_path / "docs" / "birdseye"
    root, _, _, cap_paths = _prepare_birdseye(
        tmp_path,
        edges=[
            ["alpha.md", "beta.md"],
            ["beta.md", "gamma.md"],
            ["gamma.md", "delta.md"],
            ["delta.md", "epsilon.md"],
            ["epsilon.md", "zeta.md"],
        ],
        caps_payloads=caps_payloads,
        hot_entries=[],
        root=root_base,
    )

    frozen_now = datetime(2025, 1, 3, tzinfo=timezone.utc)
    monkeypatch.setattr(update, "utc_now", lambda: frozen_now)

    monkeypatch.chdir(tmp_path)

    recorded = {}

    def fake_run(args, *, capture_output, text, check):
        recorded["args"] = args
        return SimpleNamespace(stdout="docs/birdseye/caps/delta.md.json\nREADME.md\n")

    monkeypatch.setattr(update.subprocess, "run", fake_run)

    options = update.parse_args(["--emit", "caps", "--since"])

    assert recorded["args"] == ["git", "diff", "--name-only", "main...HEAD"]
    assert options.targets == (Path("docs/birdseye/caps/delta.md.json"),)

    report = update.run_update(options)

    expected_caps = {
        Path("docs/birdseye/caps/beta.md.json"),
        Path("docs/birdseye/caps/gamma.md.json"),
        Path("docs/birdseye/caps/delta.md.json"),
        Path("docs/birdseye/caps/epsilon.md.json"),
        Path("docs/birdseye/caps/zeta.md.json"),
    }
    assert set(report.planned_writes) == expected_caps
    assert set(report.performed_writes) == expected_caps

    untouched = json.loads(cap_paths["alpha.md"].read_text(encoding="utf-8"))
    assert untouched["deps_out"] == ["stale"]
    assert untouched["deps_in"] == ["old"]

