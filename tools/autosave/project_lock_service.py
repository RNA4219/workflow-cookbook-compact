from __future__ import annotations

"""AutoSave のプロジェクトロック協調サービス."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping, MutableMapping, Protocol

from .config import AutosaveFlags


class TelemetryEmitter(Protocol):
    def __call__(self, event: str, payload: Mapping[str, object]) -> None:
        ...


class AuditLogger(Protocol):
    def __call__(self, *, action: str, details: Mapping[str, object]) -> None:
        ...


LockReleaseCallback = Callable[[str, int], None]


class ProjectLockError(RuntimeError):
    """AutoSave プロジェクトロック関連の基底例外."""


class MissingLockTokenError(ProjectLockError):
    """`docs/AUTOSAVE-DESIGN-IMPL.md` の I/O 契約違反."""


@dataclass(frozen=True)
class AutosaveCommitResult:
    status: str
    applied_snapshot_id: int | None
    next_retry_at: datetime | None = None


class ProjectLockCoordinator:
    """AutoSave のスナップショット確定とロック解放を仲介する."""

    def __init__(
        self,
        *,
        project_id: str,
        flags: AutosaveFlags,
        telemetry: TelemetryEmitter,
        audit_log: AuditLogger,
        lock_release: LockReleaseCallback,
    ) -> None:
        self._project_id = project_id
        self._flags = flags
        self._telemetry = telemetry
        self._audit_log = audit_log
        self._lock_release = lock_release
        self._last_snapshot_id: int | None = None

    def commit_snapshot(
        self,
        *,
        snapshot_id: int,
        lock_token: str,
        timestamp: datetime,
    ) -> AutosaveCommitResult:
        if not lock_token:
            raise MissingLockTokenError("lock_token is required by AutoSave contract")

        if not self._flags.project_lock_enabled:
            self._audit_log(
                action="autosave.skip",
                details=self._details(
                    lock_token=lock_token,
                    snapshot_id=self._last_snapshot_id,
                    timestamp=timestamp,
                    reason="project_lock_disabled",
                ),
            )
            self._lock_release(lock_token, self._last_snapshot_id or snapshot_id)
            return AutosaveCommitResult(status="skipped", applied_snapshot_id=self._last_snapshot_id)

        if self._last_snapshot_id is not None and snapshot_id <= self._last_snapshot_id:
            self._telemetry(
                "autosave.rollback.triggered",
                self._telemetry_payload(
                    lock_token=lock_token,
                    snapshot_id=self._last_snapshot_id,
                    reason="non_monotonic_snapshot",
                ),
            )
            self._audit_log(
                action="autosave.rollback",
                details=self._details(
                    lock_token=lock_token,
                    snapshot_id=self._last_snapshot_id,
                    timestamp=timestamp,
                    reason="non_monotonic_snapshot",
                ),
            )
            self._lock_release(lock_token, self._last_snapshot_id)
            return AutosaveCommitResult(
                status="rolled_back",
                applied_snapshot_id=self._last_snapshot_id,
            )

        self._last_snapshot_id = snapshot_id
        self._telemetry(
            "autosave.snapshot.commit",
            self._telemetry_payload(
                lock_token=lock_token,
                snapshot_id=snapshot_id,
                reason="commit",
            ),
        )
        self._audit_log(
            action="autosave.commit",
            details=self._details(
                lock_token=lock_token,
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                reason="commit",
            ),
        )
        self._lock_release(lock_token, snapshot_id)
        return AutosaveCommitResult(status="ok", applied_snapshot_id=snapshot_id)

    def _telemetry_payload(
        self,
        *,
        lock_token: str,
        snapshot_id: int | None,
        reason: str,
    ) -> MutableMapping[str, object]:
        payload: MutableMapping[str, object] = {
            "project_id": self._project_id,
            "lock_token": lock_token,
            "snapshot_id": snapshot_id,
            "reason": reason,
        }
        payload.update(self._flags.as_payload())
        return payload

    def _details(
        self,
        *,
        lock_token: str,
        snapshot_id: int | None,
        timestamp: datetime,
        reason: str,
    ) -> Mapping[str, object]:
        return {
            "project_id": self._project_id,
            "lock_token": lock_token,
            "snapshot_id": snapshot_id,
            "timestamp": timestamp.isoformat(),
            "reason": reason,
            **self._flags.as_payload(),
        }


__all__ = [
    "AuditLogger",
    "AutosaveCommitResult",
    "LockReleaseCallback",
    "MissingLockTokenError",
    "ProjectLockCoordinator",
    "ProjectLockError",
    "TelemetryEmitter",
]
