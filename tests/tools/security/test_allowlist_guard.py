import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from tools.security.allowlist_guard import detect_violations


@pytest.fixture
def allowlist_samples(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "base.yaml"
    current = tmp_path / "current.yaml"
    base.write_text(
        textwrap.dedent(
            """
            version: 1
            allowlist:
              - domain: api.github.com
                owner: GitHub
                purposes:
                  - id: ci
                    description: Release automation
                    runtime: [ci]
            """
        ).strip()
    )
    current.write_text(
        textwrap.dedent(
            """
            version: 1
            allowlist:
              - domain: api.github.com
                owner: GitHub
                purposes:
                  - id: ci
                    description: Release automation
                    runtime: [ci, developer]
              - domain: evil.example.com
                owner: Unknown
                purposes:
                  - id: ci
                    description: Unknown access
                    runtime: [ci]
            """
        ).strip()
    )
    return base, current


def test_detects_unapproved_changes(allowlist_samples: tuple[Path, Path]) -> None:
    base_path, current_path = allowlist_samples

    violations = detect_violations(
        base_content=base_path.read_text(), current_content=current_path.read_text()
    )

    assert any("evil.example.com" in message for message in violations)
    assert any("runtime" in message for message in violations)
