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


def _prepare_birdseye(tmp_path, *, edges, caps_payloads, hot_entries):
    root = tmp_path / "birdseye"
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


def test_run_update_refreshes_metadata_and_dependencies(tmp_path, monkeypatch):
    caps_payloads = {
        "alpha.md": {
            "id": "alpha.md",
            "role": "doc",
            "public_api": [],
            "summary": "alpha",
            "deps_out": [],
            "deps_in": ["obsolete"],
            "risks": [],
            "tests": [],
        },
        "beta.md": {
            "id": "beta.md",
            "role": "doc",
            "public_api": [],
            "summary": "beta",
            "deps_out": ["stale"],
            "deps_in": [],
            "risks": [],
            "tests": [],
        },
    }
    root, index_path, hot_path, cap_paths = _prepare_birdseye(
        tmp_path,
        edges=[["alpha.md", "beta.md"], ["beta.md", "alpha.md"]],
        caps_payloads=caps_payloads,
        hot_entries=["alpha.md"],
    )

    frozen_now = datetime(2025, 1, 1, 9, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(update, "utc_now", lambda: frozen_now)

    report = update.run_update(
        update.UpdateOptions(targets=(root,), emit="index+caps", dry_run=False)
    )

    expected_timestamp = "2025-01-01T09:30:00Z"
    assert report.generated_at == expected_timestamp
    assert set(report.planned_writes) == {index_path, hot_path, *cap_paths.values()}
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


def test_run_update_dry_run_skips_writes(tmp_path, monkeypatch):
    caps_payloads = {
        "alpha.md": {
            "id": "alpha.md",
            "role": "doc",
            "public_api": [],
            "summary": "alpha",
            "deps_out": [],
            "deps_in": [],
            "risks": [],
            "tests": [],
        },
        "beta.md": {
            "id": "beta.md",
            "role": "doc",
            "public_api": [],
            "summary": "beta",
            "deps_out": [],
            "deps_in": [],
            "risks": [],
            "tests": [],
        },
    }
    root, index_path, hot_path, cap_paths = _prepare_birdseye(
        tmp_path,
        edges=[["alpha.md", "beta.md"]],
        caps_payloads=caps_payloads,
        hot_entries=[],
    )

    frozen_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(update, "utc_now", lambda: frozen_now)

    snapshots = {
        path: path.read_text(encoding="utf-8")
        for path in (index_path, hot_path, *cap_paths.values())
    }

    report = update.run_update(
        update.UpdateOptions(targets=(root,), emit="index+caps", dry_run=True)
    )

    assert report.generated_at == "2025-01-01T00:00:00Z"
    assert set(report.planned_writes) == {index_path, hot_path, *cap_paths.values()}
    assert report.performed_writes == ()

    for path, before in snapshots.items():
        assert path.read_text(encoding="utf-8") == before

