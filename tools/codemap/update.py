"""Birdseye再生成ツール。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class UpdateOptions:
    targets: tuple[Path, ...]
    emit: str
    dry_run: bool = False


@dataclass(frozen=True)
class UpdateReport:
    generated_at: str
    planned_writes: tuple[Path, ...]
    performed_writes: tuple[Path, ...]


def parse_args(argv: Iterable[str] | None = None) -> UpdateOptions:
    parser = argparse.ArgumentParser(
        description="Regenerate Birdseye index and capsules.",
    )
    parser.add_argument(
        "--targets",
        type=str,
        required=True,
        help="Comma-separated list of Birdseye resources to analyse.",
    )
    parser.add_argument(
        "--emit",
        type=str,
        choices=("index", "caps", "index+caps"),
        default="index+caps",
        help="Select which artefacts to write.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute updates without writing to disk.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    target_paths = tuple(Path(value.strip()) for value in args.targets.split(",") if value.strip())
    if not target_paths:
        parser.error("--targets must contain at least one path")
    return UpdateOptions(targets=target_paths, emit=args.emit, dry_run=args.dry_run)


def ensure_python_version() -> None:
    if sys.version_info < (3, 11):
        print("[ERROR] Python 3.11 or newer is required.")
        raise SystemExit(1)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(moment: datetime) -> str:
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_root(target: Path) -> Path:
    if target.is_dir():
        return target
    if target.parent.name == "caps":
        return target.parent.parent
    return target.parent


def _load_json(path: Path) -> tuple[Any, str]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw), raw


def _dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _sorted_unique(items: Sequence[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


def _maybe_write(
    path: Path,
    data: Any,
    original: str,
    *,
    planned: set[Path],
    performed: set[Path],
    dry_run: bool,
) -> None:
    serialized = _dump_json(data)
    if serialized == original:
        return
    planned.add(path)
    if dry_run:
        return
    path.write_text(serialized, encoding="utf-8")
    performed.add(path)


def _finalise(paths: set[Path]) -> tuple[Path, ...]:
    return tuple(sorted(paths, key=lambda candidate: candidate.as_posix()))


def run_update(options: UpdateOptions) -> UpdateReport:
    emit_index = options.emit in {"index", "index+caps"}
    emit_caps = options.emit in {"caps", "index+caps"}
    planned: set[Path] = set()
    performed: set[Path] = set()
    timestamp = _format_timestamp(utc_now())

    for target in options.targets:
        root = _resolve_root(target)
        index_path = root / "index.json"
        caps_dir = root / "caps"
        hot_path = root / "hot.json"

        if not index_path.is_file():
            raise FileNotFoundError(index_path)
        if emit_caps and not caps_dir.is_dir():
            raise FileNotFoundError(caps_dir)

        index_data, index_original = _load_json(index_path)
        raw_nodes = index_data.get("nodes", {})
        if not isinstance(raw_nodes, dict):
            raw_nodes = {}
        graph_out: dict[str, list[str]] = {node: [] for node in raw_nodes}
        graph_in: dict[str, list[str]] = {node: [] for node in raw_nodes}
        for raw_edge in index_data.get("edges", []):
            if not isinstance(raw_edge, Sequence) or len(raw_edge) != 2:
                continue
            source, destination = raw_edge
            if not isinstance(source, str) or not isinstance(destination, str):
                continue
            graph_out.setdefault(source, []).append(destination)
            graph_in.setdefault(destination, []).append(source)
            graph_out.setdefault(destination, graph_out.get(destination, []))
            graph_in.setdefault(source, graph_in.get(source, []))

        for values in graph_out.values():
            values.sort()
        for values in graph_in.values():
            values.sort()

        if emit_index:
            if index_data.get("generated_at") != timestamp:
                index_data["generated_at"] = timestamp
            _maybe_write(
                index_path,
                index_data,
                index_original,
                planned=planned,
                performed=performed,
                dry_run=options.dry_run,
            )

            if hot_path.exists():
                hot_data, hot_original = _load_json(hot_path)
                if isinstance(hot_data, dict):
                    if hot_data.get("generated_at") != timestamp:
                        hot_data["generated_at"] = timestamp
                    _maybe_write(
                        hot_path,
                        hot_data,
                        hot_original,
                        planned=planned,
                        performed=performed,
                        dry_run=options.dry_run,
                    )

        if emit_caps:
            for cap_path in sorted(caps_dir.glob("*.json")):
                if not cap_path.is_file():
                    continue
                cap_data, cap_original = _load_json(cap_path)
                if not isinstance(cap_data, dict):
                    continue
                cap_id = cap_data.get("id")
                if not isinstance(cap_id, str):
                    continue
                expected_out = _sorted_unique(graph_out.get(cap_id, []))
                expected_in = _sorted_unique(graph_in.get(cap_id, []))
                updated = False
                if cap_data.get("deps_out") != expected_out:
                    cap_data["deps_out"] = expected_out
                    updated = True
                if cap_data.get("deps_in") != expected_in:
                    cap_data["deps_in"] = expected_in
                    updated = True
                if updated:
                    _maybe_write(
                        cap_path,
                        cap_data,
                        cap_original,
                        planned=planned,
                        performed=performed,
                        dry_run=options.dry_run,
                    )

    return UpdateReport(
        generated_at=timestamp,
        planned_writes=_finalise(planned),
        performed_writes=_finalise(performed),
    )


def main(argv: Iterable[str] | None = None) -> int:
    ensure_python_version()
    options = parse_args(argv)
    run_update(options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
