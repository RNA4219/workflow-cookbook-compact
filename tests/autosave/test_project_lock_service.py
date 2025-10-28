from __future__ import annotations

"""AutoSave プロジェクトロック協調のテスト.

`docs/AUTOSAVE-DESIGN-IMPL.md` に記載された I/O 契約と
`docs/MERGE-DESIGN-IMPL.md` のロック協調要件を検証する。
"""

import sys
from collections.abc import MutableMapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.autosave.config import AutosaveFlags
from tools.autosave.project_lock_service import (
    AutosaveCommitResult,
    MissingLockTokenError,
    ProjectLockCoordinator,
)


class StubTelemetry:
    def __init__(self) -> None:
        self.events: list[tuple[str, MutableMapping[str, Any]]] = []

    def emit(self, name: str, payload: MutableMapping[str, Any]) -> None:
        self.events.append((name, payload))


class StubAuditLogger:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def record(self, *, action: str, details: dict[str, Any]) -> None:
        self.entries.append({"action": action, **details})


def make_coordinator(
    *,
    flags: AutosaveFlags,
    telemetry: StubTelemetry | None = None,
    audit: StubAuditLogger | None = None,
) -> tuple[ProjectLockCoordinator, StubTelemetry, StubAuditLogger, list[tuple[str, int]]]:
    telemetry_impl = telemetry or StubTelemetry()
    audit_impl = audit or StubAuditLogger()
    releases: list[tuple[str, int]] = []

    def lock_release(lock_token: str, snapshot_id: int) -> None:
        releases.append((lock_token, snapshot_id))

    coordinator = ProjectLockCoordinator(
        project_id="proj-42",
        flags=flags,
        telemetry=telemetry_impl.emit,
        audit_log=audit_impl.record,
        lock_release=lock_release,
    )
    return coordinator, telemetry_impl, audit_impl, releases


def test_commit_requires_lock_token() -> None:
    """`docs/AUTOSAVE-DESIGN-IMPL.md` の I/O 契約どおり lock_token を必須とする。"""

    coordinator, _, _, _ = make_coordinator(
        flags=AutosaveFlags(project_lock_enabled=True, merge_precision_mode="strict"),
    )

    with pytest.raises(MissingLockTokenError):
        coordinator.commit_snapshot(
            snapshot_id=1,
            lock_token="",
            timestamp=datetime.now(timezone.utc),
        )


def test_commit_enforces_monotonic_snapshot_ids() -> None:
    """スナップショット ID が単調増加しない場合にロールバックと監査が行われる。"""

    coordinator, telemetry, audit, releases = make_coordinator(
        flags=AutosaveFlags(project_lock_enabled=True, merge_precision_mode="strict"),
    )

    first = coordinator.commit_snapshot(
        snapshot_id=5,
        lock_token="lock-a",
        timestamp=datetime.now(timezone.utc),
    )
    assert isinstance(first, AutosaveCommitResult)
    assert first.status == "ok"
    assert first.applied_snapshot_id == 5

    second = coordinator.commit_snapshot(
        snapshot_id=3,
        lock_token="lock-b",
        timestamp=datetime.now(timezone.utc),
    )
    assert second.status == "rolled_back"
    assert second.applied_snapshot_id == 5
    assert telemetry.events[-1][0] == "autosave.rollback.triggered"
    assert telemetry.events[-1][1]["lock_token"] == "lock-b"
    assert audit.entries[-1]["action"] == "autosave.rollback"
    assert audit.entries[-1]["lock_token"] == "lock-b"
    assert releases[-1] == ("lock-b", 5)


def test_commit_emits_commit_telemetry_and_releases_lock() -> None:
    """コミット成功時に `autosave.snapshot.commit` と Merge 用 lock_release を発火する。"""

    coordinator, telemetry, audit, releases = make_coordinator(
        flags=AutosaveFlags(project_lock_enabled=True, merge_precision_mode="strict"),
    )

    result = coordinator.commit_snapshot(
        snapshot_id=11,
        lock_token="lock-c",
        timestamp=datetime.now(timezone.utc),
    )

    assert result.status == "ok"
    assert result.applied_snapshot_id == 11
    assert telemetry.events[0][0] == "autosave.snapshot.commit"
    assert telemetry.events[0][1]["snapshot_id"] == 11
    assert audit.entries[0]["lock_token"] == "lock-c"
    assert releases[0] == ("lock-c", 11)
