from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any, Sequence

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal env
    yaml = None  # type: ignore[assignment]


def _strip_quotes(value: str) -> str:
    if (value.startswith("\"") and value.endswith("\"")) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_inline_list(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("[") and stripped.endswith("]"):
        body = stripped[1:-1].strip()
        if not body:
            return []
        return [
            _strip_quotes(part.strip())
            for part in body.split(",")
            if part.strip()
        ]
    return [_strip_quotes(stripped)]


def _fallback_safe_load(content: str) -> dict[str, Any]:
    version: int | None = None
    allowlist: list[dict[str, Any]] = []
    current_entry: dict[str, Any] | None = None
    current_purpose: dict[str, Any] | None = None
    for raw in content.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent == 0:
            key, _, rest = line.partition(":")
            key = key.strip()
            value = rest.strip()
            if key == "version" and value:
                version = int(value)
            continue
        if indent == 2:
            if line.strip().startswith("- "):
                key, _, rest = line.strip()[2:].partition(":")
                if key.strip() != "domain":
                    raise ValueError("expected domain entry")
                current_entry = {"domain": _strip_quotes(rest.strip()), "purposes": []}
                allowlist.append(current_entry)
                current_purpose = None
                continue
        if indent == 4 and current_entry is not None:
            key, _, rest = line.partition(":")
            key = key.strip()
            value = rest.strip()
            if key == "owner":
                current_entry["owner"] = _strip_quotes(value)
            elif key == "purposes":
                continue
            else:
                current_entry[key] = _strip_quotes(value)
            continue
        if indent == 6 and current_entry is not None:
            if line.strip().startswith("- "):
                key, _, rest = line.strip()[2:].partition(":")
                if key.strip() != "id":
                    raise ValueError("expected purpose id")
                current_purpose = {"id": _strip_quotes(rest.strip())}
                current_entry.setdefault("purposes", []).append(current_purpose)
                continue
            key, _, rest = line.partition(":")
            if current_purpose is None:
                continue
            key = key.strip()
            value = rest.strip()
            current_purpose[key] = _strip_quotes(value)
            continue
        if indent == 8 and current_purpose is not None:
            key, _, rest = line.partition(":")
            key = key.strip()
            value = rest.strip()
            if key == "runtime":
                current_purpose[key] = _parse_inline_list(value)
            else:
                current_purpose[key] = _strip_quotes(value)
    result: dict[str, Any] = {"allowlist": allowlist}
    if version is not None:
        result["version"] = version
    return result


def _safe_load(content: str) -> dict[str, Any]:
    if yaml is not None:
        loaded = yaml.safe_load(content)  # type: ignore[attr-defined]
        if isinstance(loaded, dict):
            return loaded
        return {}
    return _fallback_safe_load(content)


def _load_allowlist(content: str) -> list[dict[str, Any]]:
    data = _safe_load(content) or {}
    allowlist = data.get("allowlist", [])
    if not isinstance(allowlist, list):
        raise ValueError("allowlist must be a list")
    normalized: list[dict[str, Any]] = []
    for entry in allowlist:
        if not isinstance(entry, dict):
            raise ValueError("allowlist entries must be mappings")
        if "domain" not in entry:
            raise ValueError("allowlist entry missing domain")
        normalized.append(entry)
    return normalized


def _index_purposes(entry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    purposes = entry.get("purposes", [])
    if not isinstance(purposes, list):
        raise ValueError("purposes must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in purposes:
        if not isinstance(item, dict):
            raise ValueError("purposes entries must be mappings")
        identifier = item.get("id")
        if not isinstance(identifier, str):
            raise ValueError("purpose id must be a string")
        indexed[identifier] = item
    return indexed


def detect_violations(*, base_content: str, current_content: str) -> list[str]:
    violations: list[str] = []
    base_entries = {entry["domain"]: entry for entry in _load_allowlist(base_content)}
    current_entries = {entry["domain"]: entry for entry in _load_allowlist(current_content)}

    for domain, entry in current_entries.items():
        if domain not in base_entries:
            violations.append(f"domain '{domain}' added without approval")
            continue
        base_entry = base_entries[domain]
        base_purposes = _index_purposes(base_entry)
        current_purposes = _index_purposes(entry)
        for identifier, purpose in current_purposes.items():
            if identifier not in base_purposes:
                violations.append(
                    f"domain '{domain}' purpose '{identifier}' added without approval"
                )
                continue
            base_purpose = base_purposes[identifier]
            if base_purpose != purpose:
                fields = sorted(
                    key
                    for key in set(base_purpose) | set(purpose)
                    if base_purpose.get(key) != purpose.get(key)
                )
                detail = ", ".join(fields)
                violations.append(
                    f"domain '{domain}' purpose '{identifier}' changed fields: {detail}"
                )
    return violations


def _git_show(ref: str) -> str:
    result = subprocess.run(
        ["git", "show", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"failed to read {ref}")
    return result.stdout


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate network allowlist changes")
    parser.add_argument("--base-ref", required=True)
    parser.add_argument(
        "--allowlist-path",
        default=Path("network/allowlist.yaml"),
        type=Path,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    allowlist_path = args.allowlist_path
    base_spec = f"{args.base_ref}:{allowlist_path.as_posix()}"
    base_content = _git_show(base_spec)
    current_content = allowlist_path.read_text()
    violations = detect_violations(base_content=base_content, current_content=current_content)
    for violation in violations:
        print(f"allowlist-guard: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
