import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from types import SimpleNamespace

import pytest

from tools.security import allowlist_guard
from tools.security.allowlist_guard import detect_violations


BASE_ALLOWLIST = textwrap.dedent(
    """
    allowlist:
      - domain: 'kept.example.com'
        purposes:
          - id: 'ci'
      - domain: 'removed.example.com'
        purposes:
          - id: 'deploy'
    """
)


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


@pytest.mark.parametrize(
    ("current_content", "expected_fragment"),
    [
        (
            textwrap.dedent(
                """
                allowlist:
                  - domain: 'kept.example.com'
                    purposes:
                      - id: 'ci'
                """
            ),
            "domain 'removed.example.com' removed without approval",
        ),
        (
            textwrap.dedent(
                """
                allowlist:
                  - domain: 'kept.example.com'
                    purposes:
                      - id: 'ci'
                  - domain: 'removed.example.com'
                    purposes:
                """
            ),
            "domain 'removed.example.com' purpose 'deploy' removed without approval",
        ),
    ],
)
def test_detects_unapproved_deletions(current_content: str, expected_fragment: str) -> None:
    violations = detect_violations(
        base_content=BASE_ALLOWLIST,
        current_content=current_content,
    )

    assert any(expected_fragment in message for message in violations)


def test_cli_returns_error_on_removed_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowlist_path = tmp_path / "allowlist.yaml"
    current_content = textwrap.dedent(
        """
        allowlist:
          - domain: 'kept.example.com'
            purposes:
              - id: 'ci'
        """
    )
    allowlist_path.write_text(current_content)

    monkeypatch.setattr(allowlist_guard, "_git_show", lambda ref: BASE_ALLOWLIST)
    monkeypatch.setattr(
        allowlist_guard,
        "_parse_args",
        lambda argv: SimpleNamespace(base_ref="origin/main", allowlist_path=allowlist_path),
    )

    exit_code = allowlist_guard.main([])

    assert exit_code == 1
