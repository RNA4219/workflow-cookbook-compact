from __future__ import annotations

"""AutoSave フラグ設定と CLI エントリポイント."""

import argparse
import json
from dataclasses import dataclass
from typing import Literal, Sequence

PrecisionMode = Literal["baseline", "strict"]


@dataclass(frozen=True)
class AutosaveFlags:
    """AutoSave と Merge の連携に利用するフラグ値."""

    project_lock_enabled: bool
    merge_precision_mode: PrecisionMode

    def enforce_project_lock(self) -> bool:
        """`strict` モードかつフラグ有効時のみロックを強制する."""

        return self.project_lock_enabled and self.merge_precision_mode == "strict"

    def as_payload(self) -> dict[str, object]:
        """監査ログ向けのシリアライズ済み表現."""

        return {
            "autosave.project_lock": self.project_lock_enabled,
            "merge.precision_mode": self.merge_precision_mode,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or override AutoSave rollout flags.",
    )
    parser.add_argument(
        "--project-lock",
        choices=("on", "off"),
        default="off",
        help="Enable (on) or disable (off) autosave.project_lock flag (default: off).",
    )
    parser.add_argument(
        "--precision-mode",
        choices=("baseline", "strict"),
        default="baseline",
        help="Set merge.precision_mode flag (default: baseline).",
    )
    return parser


def parse_flags(argv: Sequence[str] | None = None) -> AutosaveFlags:
    """CLI から `AutosaveFlags` を生成する."""

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return AutosaveFlags(
        project_lock_enabled=args.project_lock == "on",
        merge_precision_mode=args.precision_mode,
    )


def cli(argv: Sequence[str] | None = None) -> int:
    """簡易 CLI: フラグ状態を JSON で出力する."""

    flags = parse_flags(argv)
    print(json.dumps(flags.as_payload(), ensure_ascii=False, indent=2))
    return 0


__all__ = ["AutosaveFlags", "PrecisionMode", "cli", "parse_flags"]
