# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 RNA4219

"""Birdseye再生成ツール。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[2]


_BIRDSEYE_REGENERATE_COMMAND = (
    "python tools/codemap/update.py --targets "
    "docs/birdseye/index.json,docs/birdseye/hot.json --emit index+caps"
)


CapsuleEntry = tuple[Path, dict[str, Any], str]
CapsuleState = dict[str, CapsuleEntry]
Graph = dict[str, list[str]]


class TargetResolutionError(RuntimeError):
    """Raised when Birdseye targets cannot be resolved."""


class DiffResolver(Protocol):
    def resolve(self, reference: str) -> tuple[Path, ...]:
        ...


@dataclass(frozen=True)
class UpdateOptions:
    targets: tuple[Path, ...]
    emit: str
    dry_run: bool = False
    since: str | None = None
    diff_resolver: DiffResolver | None = None

    def resolve_targets(self) -> tuple[Path, ...]:
        resolved = [_normalise_target(path) for path in self.targets]
        if self.since:
            if self.diff_resolver is None:
                raise TargetResolutionError("Diff resolver is required when --since is used")
            try:
                derived = self.diff_resolver.resolve(self.since)
            except subprocess.CalledProcessError as exc:
                raise TargetResolutionError(
                    f"Failed to resolve git diff for --since: {exc}"
                ) from exc
            resolved.extend(_normalise_target(path) for path in derived)
        if not resolved:
            resolved.extend(_default_birdseye_targets())
        unique_targets = tuple(dict.fromkeys(resolved))
        if not unique_targets:
            raise TargetResolutionError("Specify --targets, --since, or both")
        return unique_targets


@dataclass(frozen=True)
class UpdateReport:
    generated_at: str
    planned_writes: tuple[Path, ...]
    performed_writes: tuple[Path, ...]


class GitDiffResolver:
    def resolve(self, reference: str) -> tuple[Path, ...]:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--find-renames",
                "--find-copies",
                f"{reference}...HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=_REPO_ROOT,
        )
        diff_entries: list[str] = []
        for raw_line in result.stdout.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            columns = [segment.strip() for segment in stripped.split("\t")]
            if not columns:
                continue
            status = columns[0]
            if not status:
                continue
            kind = status[0].upper()
            payloads: list[str]
            if kind in {"R", "C"} and len(columns) >= 3:
                payloads = columns[1:3]
            elif kind in {"A", "M", "D", "T"} and len(columns) >= 2:
                payloads = [columns[1]]
            else:
                continue
            for value in payloads:
                candidate = value.replace("\\", "/").strip()
                if not candidate:
                    continue
                diff_entries.append(candidate)
        derived = _derive_targets_from_since(diff_entries)
        return tuple(
            path
            for path in derived
            if len(path.parts) >= 2 and path.parts[0] == "docs" and path.parts[1] == "birdseye"
        )


def _derive_targets_from_since(
    diff_paths: Iterable[str | Path], *, repo_root: Path | None = None
) -> tuple[Path, ...]:
    base_root = repo_root or _REPO_ROOT
    derived: list[Path] = []
    seen: set[Path] = set()

    def _add(path: Path) -> None:
        if path not in seen:
            seen.add(path)
            derived.append(path)

    for path in diff_paths:
        if isinstance(path, Path):
            raw_entry = path.as_posix()
        else:
            raw_entry = path
        raw_entry = raw_entry.replace("\\", "/").strip()
        if not raw_entry:
            continue
        segments: list[str] = []
        for marker in (" -> ", " => "):
            if marker in raw_entry:
                left, right = raw_entry.split(marker, 1)
                segments.extend([left.strip(), right.strip()])
                break
        if not segments:
            segments.append(raw_entry)
        for segment in segments:
            candidate = segment
            if not candidate:
                continue
            while candidate.startswith("./"):
                candidate = candidate[2:]
            candidate = candidate.rstrip("/")
            if not candidate:
                continue
            normalised = Path(candidate)
            if normalised.is_absolute():
                try:
                    normalised = normalised.relative_to(base_root)
                except ValueError:
                    continue
            if normalised.parts[:2] == ("docs", "birdseye"):
                _add(normalised)
                continue
            candidate_slug = normalised.as_posix() if normalised.parts else candidate
            capsule_slug = candidate_slug.replace("/", ".")
            capsule_path = Path("docs/birdseye/caps") / f"{capsule_slug}.json"
            if (base_root / capsule_path).is_file():
                _add(capsule_path)
    return tuple(derived)


def _default_birdseye_targets() -> tuple[Path, ...]:
    birdseye_root = _REPO_ROOT / "docs" / "birdseye"
    candidates = (
        birdseye_root / "index.json",
        birdseye_root / "hot.json",
        birdseye_root / "caps",
    )
    fallback: list[Path] = []
    for candidate in candidates:
        if candidate.is_file() or candidate.is_dir():
            fallback.append(candidate.resolve())
    return tuple(fallback)


def _normalise_target(target: Path) -> Path:
    if target.is_absolute():
        return target.resolve()
    return (_REPO_ROOT / target).resolve()


def parse_args(argv: Iterable[str] | None = None) -> UpdateOptions:
    parser = argparse.ArgumentParser(
        description="Regenerate Birdseye index and capsules.",
    )
    parser.add_argument(
        "--targets",
        type=str,
        help="Comma-separated list of Birdseye resources to analyse.",
    )
    parser.add_argument(
        "--since",
        type=str,
        nargs="?",
        const="main",
        help="Derive targets from git diff since the given reference (default: main).",
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
    target_paths: list[Path] = []
    if args.targets:
        target_paths.extend(
            Path(value.strip()) for value in args.targets.split(",") if value.strip()
        )
    if not target_paths and not args.since:
        parser.error("Specify --targets, --since, or both")
    normalised_targets = tuple(
        dict.fromkeys(_normalise_target(path) for path in target_paths)
    )
    return UpdateOptions(
        targets=normalised_targets,
        emit=args.emit,
        dry_run=args.dry_run,
        since=args.since,
    )


def ensure_python_version() -> None:
    if sys.version_info < (3, 11):
        print("[ERROR] Python 3.11 or newer is required.")
        raise SystemExit(1)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(moment: datetime) -> str:
    return moment.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_root(target: Path) -> Path:
    resolved = target.resolve()
    if resolved.is_dir():
        if resolved.name == "caps":
            return resolved.parent.resolve()
        return resolved
    parent = resolved.parent
    if parent.name == "caps":
        return parent.parent.resolve()
    return parent.resolve()


def _load_json(path: Path) -> tuple[Any, str]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw), raw


def _dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _sorted_unique(items: Sequence[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


_SERIAL_PATTERN = re.compile(r"\d{5}")


def _coerce_serial(candidate: Any) -> int | None:
    if isinstance(candidate, str) and _SERIAL_PATTERN.fullmatch(candidate):
        return int(candidate)
    return None


class _SerialAllocator:
    __slots__ = ("max_serial", "_next_serial")

    def __init__(self) -> None:
        self.max_serial = 0
        self._next_serial: int | None = None

    def observe(self, candidate: Any) -> None:
        value = _coerce_serial(candidate)
        if value is not None and value > self.max_serial:
            self.max_serial = value

    def allocate(self, existing: Any) -> str:
        candidate = _coerce_serial(existing)
        if candidate is not None and candidate > self.max_serial:
            self.max_serial = candidate
        if self._next_serial is None:
            self._next_serial = self.max_serial + 1 if self.max_serial else 1
        target = self._next_serial
        if target > self.max_serial:
            self.max_serial = target
        return f"{target:05d}"


def _next_generated_at(existing: Any, fallback: str, *, allocator: _SerialAllocator) -> str:
    del fallback
    return allocator.allocate(existing)


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


def _group_targets(targets: Iterable[Path]) -> dict[Path, list[Path]]:
    grouped: dict[Path, list[Path]] = {}
    for target in targets:
        normalised = _normalise_target(target)
        root = _resolve_root(normalised)
        grouped.setdefault(root, []).append(normalised)
    return grouped


def _build_graph(index_data: Mapping[str, Any]) -> tuple[Graph, Graph]:
    raw_nodes = index_data.get("nodes", {})
    if not isinstance(raw_nodes, Mapping):
        raw_nodes = {}
    graph_out: Graph = {node: [] for node in raw_nodes if isinstance(node, str)}
    graph_in: Graph = {node: [] for node in raw_nodes if isinstance(node, str)}
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
    return graph_out, graph_in


def _resolve_focus_nodes(
    root_targets: Iterable[Path],
    root: Path,
    graph_out: Mapping[str, Sequence[str]],
    graph_in: Mapping[str, Sequence[str]],
    caps_state: CapsuleState,
    cap_path_lookup: Mapping[Path, str],
) -> set[str]:
    if not caps_state:
        return set()
    focus_nodes: set[str] = set()
    root_resolved = root.resolve()
    index_resolved = (root / "index.json").resolve()
    caps_dir_resolved = (root / "caps").resolve()
    hot_resolved = (root / "hot.json").resolve()
    special_roots = {root_resolved, index_resolved, caps_dir_resolved, hot_resolved}
    for candidate in root_targets:
        resolved = candidate.resolve()
        if resolved in special_roots:
            return set(caps_state)
        cap_id = cap_path_lookup.get(resolved)
        if cap_id:
            focus_nodes.add(cap_id)
    if not focus_nodes:
        focus_nodes = set(caps_state)
    seen: set[str] = set()
    queue: deque[tuple[str, int]] = deque((node, 0) for node in focus_nodes)
    while queue:
        node, distance = queue.popleft()
        if node in seen or distance > 2:
            continue
        seen.add(node)
        if distance == 2:
            continue
        for neighbour in graph_out.get(node, ()): 
            if neighbour not in seen:
                queue.append((neighbour, distance + 1))
        for neighbour in graph_in.get(node, ()): 
            if neighbour not in seen:
                queue.append((neighbour, distance + 1))
    return {node for node in seen if node in caps_state}


def _refresh_index(
    index_path: Path,
    index_data: dict[str, Any],
    index_original: str,
    *,
    timestamp: str,
    dry_run: bool,
    planned: set[Path],
    performed: set[Path],
    remember_generated: Callable[[str], None],
    allocator: _SerialAllocator,
) -> None:
    new_generated = _next_generated_at(
        index_data.get("generated_at"),
        timestamp,
        allocator=allocator,
    )
    if index_data.get("generated_at") != new_generated:
        index_data["generated_at"] = new_generated
        remember_generated(new_generated)
    _maybe_write(
        index_path,
        index_data,
        index_original,
        planned=planned,
        performed=performed,
        dry_run=dry_run,
    )


def _refresh_hot(
    hot_path: Path,
    hot_data: dict[str, Any] | None,
    hot_original: str | None,
    *,
    timestamp: str,
    dry_run: bool,
    planned: set[Path],
    performed: set[Path],
    remember_generated: Callable[[str], None],
    allocator: _SerialAllocator,
) -> None:
    if hot_data is None or hot_original is None:
        return
    new_generated = _next_generated_at(
        hot_data.get("generated_at"),
        timestamp,
        allocator=allocator,
    )
    if hot_data.get("generated_at") != new_generated:
        hot_data["generated_at"] = new_generated
        remember_generated(new_generated)
    _maybe_write(
        hot_path,
        hot_data,
        hot_original,
        planned=planned,
        performed=performed,
        dry_run=dry_run,
    )


def _refresh_capsule(
    cap_id: str,
    capsule: CapsuleEntry,
    graph_out: Mapping[str, Sequence[str]],
    graph_in: Mapping[str, Sequence[str]],
    timestamp: str,
    *,
    dry_run: bool,
    planned: set[Path],
    performed: set[Path],
    remember_generated: Callable[[str], None],
    allocator: _SerialAllocator,
) -> None:
    cap_path, cap_data, cap_original = capsule
    expected_out = _sorted_unique(graph_out.get(cap_id, []))
    expected_in = _sorted_unique(graph_in.get(cap_id, []))
    updated = False
    if cap_data.get("deps_out") != expected_out:
        cap_data["deps_out"] = expected_out
        updated = True
    if cap_data.get("deps_in") != expected_in:
        cap_data["deps_in"] = expected_in
        updated = True
    new_generated = _next_generated_at(
        cap_data.get("generated_at"),
        timestamp,
        allocator=allocator,
    )
    if cap_data.get("generated_at") != new_generated:
        cap_data["generated_at"] = new_generated
        updated = True
        remember_generated(new_generated)
    if updated:
        _maybe_write(
            cap_path,
            cap_data,
            cap_original,
            planned=planned,
            performed=performed,
            dry_run=dry_run,
        )

def run_update(options: UpdateOptions) -> UpdateReport:
    emit_index = options.emit in {"index", "index+caps"}
    emit_caps = options.emit in {"caps", "index+caps"}
    planned: set[Path] = set()
    performed: set[Path] = set()
    timestamp = _format_timestamp(utc_now())
    applied_generated_at: str | None = None
    serial_allocator = _SerialAllocator()

    def remember_generated(value: str) -> None:
        nonlocal applied_generated_at
        if applied_generated_at is None:
            applied_generated_at = value

    resolved_targets = options.resolve_targets()
    grouped = _group_targets(resolved_targets)

    for root, root_targets in grouped.items():
        index_path = root / "index.json"
        caps_dir = root / "caps"
        hot_path = root / "hot.json"

        if not index_path.is_file():
            raise FileNotFoundError(index_path)
        if emit_index and not hot_path.exists():
            raise FileNotFoundError(
                f"{hot_path} is missing. Regenerate via: {_BIRDSEYE_REGENERATE_COMMAND}"
            )
        if emit_caps and not caps_dir.is_dir():
            raise FileNotFoundError(caps_dir)

        loaded_index, index_original = _load_json(index_path)
        index_data = loaded_index if isinstance(loaded_index, dict) else {}
        serial_allocator.observe(index_data.get("generated_at"))
        graph_out, graph_in = _build_graph(index_data)

        hot_data: dict[str, Any] | None = None
        hot_original: str | None = None
        if hot_path.exists():
            loaded_hot, loaded_hot_original = _load_json(hot_path)
            if isinstance(loaded_hot, dict):
                hot_data = loaded_hot
                hot_original = loaded_hot_original
                serial_allocator.observe(hot_data.get("generated_at"))

        caps_state: CapsuleState = {}
        cap_path_lookup: dict[Path, str] = {}
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
                caps_state[cap_id] = (cap_path, cap_data, cap_original)
                cap_path_lookup[cap_path.resolve()] = cap_id
                serial_allocator.observe(cap_data.get("generated_at"))

        if emit_index:
            _refresh_index(
                index_path,
                index_data,
                index_original,
                timestamp=timestamp,
                dry_run=options.dry_run,
                planned=planned,
                performed=performed,
                remember_generated=remember_generated,
                allocator=serial_allocator,
            )
            _refresh_hot(
                hot_path,
                hot_data,
                hot_original,
                timestamp=timestamp,
                dry_run=options.dry_run,
                planned=planned,
                performed=performed,
                remember_generated=remember_generated,
                allocator=serial_allocator,
            )

        if emit_caps and caps_state:
            focus_nodes = _resolve_focus_nodes(
                root_targets,
                root,
                graph_out,
                graph_in,
                caps_state,
                cap_path_lookup,
            )
            for cap_id in sorted(focus_nodes):
                _refresh_capsule(
                    cap_id,
                    caps_state[cap_id],
                    graph_out,
                    graph_in,
                    timestamp,
                    dry_run=options.dry_run,
                    planned=planned,
                    performed=performed,
                    remember_generated=remember_generated,
                    allocator=serial_allocator,
                )

    return UpdateReport(
        generated_at=applied_generated_at or timestamp,
        planned_writes=_finalise(planned),
        performed_writes=_finalise(performed),
    )


def main(argv: Iterable[str] | None = None) -> int:
    ensure_python_version()
    options = parse_args(argv)
    options = replace(options, diff_resolver=GitDiffResolver())
    try:
        run_update(options)
    except TargetResolutionError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
