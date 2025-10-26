import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if (repo_root := str(REPO_ROOT)) not in sys.path:
    sys.path.insert(0, repo_root)

from tools.security.allowlist_guard import detect_violations


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
