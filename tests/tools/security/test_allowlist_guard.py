import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from types import SimpleNamespace

import pytest

from tools.security import allowlist_guard
from tools.security.allowlist_guard import detect_violations


def test_cli_returns_error_on_unapproved_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowlist_path = tmp_path / "allowlist.yaml"
    base_content = "allowlist:\n  - domain: 'allowed.example.com'\n"
    allowlist_path.write_text(
        base_content
        + "  - domain: 'evil.example.com'\n"
        + "    owner: 'Unknown'\n"
    )

    monkeypatch.setattr(allowlist_guard, "_git_show", lambda ref: base_content)
    monkeypatch.setattr(
        allowlist_guard,
        "_parse_args",
        lambda argv: SimpleNamespace(base_ref="origin/main", allowlist_path=allowlist_path),
    )

    exit_code = allowlist_guard.main([])

    assert exit_code == 1
def test_detects_unapproved_domain_addition() -> None:
    allowlist_path = REPO_ROOT / "network" / "allowlist.yaml"
    base_content = allowlist_path.read_text()
    malicious_entry = (
        "\n"
        "  - domain: \"evil.example.com\"\n"
        "    owner: \"Unknown\"\n"
        "    purposes:\n"
        "      - id: \"ci\"\n"
        "        description: \"Unapproved access\"\n"
        "        runtime: [\"ci\"]\n"
    )
    current_content = base_content.rstrip() + malicious_entry

    violations = detect_violations(
        base_content=base_content, current_content=current_content
    )

    assert any("evil.example.com" in message for message in violations)


def test_detects_unapproved_deletions() -> None:
    base_content = (
        "allowlist:\n"
        "  - domain: 'kept.example.com'\n"
        "    purposes:\n"
        "      - id: 'ci'\n"
        "  - domain: 'removed.example.com'\n"
        "    purposes:\n"
        "      - id: 'deploy'\n"
    )
    current_without_domain = (
        "allowlist:\n"
        "  - domain: 'kept.example.com'\n"
        "    purposes:\n"
        "      - id: 'ci'\n"
    )
    domain_violations = detect_violations(
        base_content=base_content, current_content=current_without_domain
    )
    assert any(
        "removed.example.com" in message and "removed" in message
        for message in domain_violations
    )

    current_without_purpose = (
        "allowlist:\n"
        "  - domain: 'kept.example.com'\n"
        "    purposes:\n"
        "      - id: 'ci'\n"
        "  - domain: 'removed.example.com'\n"
        "    purposes:\n"
    )
    purpose_violations = detect_violations(
        base_content=base_content, current_content=current_without_purpose
    )
    assert any(
        "removed.example.com" in message and "purpose 'deploy'" in message
        for message in purpose_violations
    )
