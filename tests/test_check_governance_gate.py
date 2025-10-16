import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.ci.check_governance_gate import (
    find_forbidden_matches,
    load_forbidden_patterns,
    validate_pr_body,
)


@pytest.mark.parametrize(
    "changed_paths, patterns, expected",
    [
        ("""core/schema/model.yaml\ndocs/guide.md""".splitlines(), ["/core/schema/**"], ["core/schema/model.yaml"]),
        ("""docs/readme.md\nops/runbook.md""".splitlines(), ["/core/schema/**"], []),
        (
            """auth/service.py\ncore/schema/definitions.yml""".splitlines(),
            ["/auth/**", "/core/schema/**"],
            ["auth/service.py", "core/schema/definitions.yml"],
        ),
    ],
)
def test_find_forbidden_matches(changed_paths, patterns, expected):
    normalized = [pattern.lstrip("/") for pattern in patterns]
    assert find_forbidden_matches(changed_paths, normalized) == expected


def test_validate_pr_body_success(capsys):
    body = """
Intent: INT-123
## EVALUATION
Priority Score: 4.5 / 安全性強化
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_segmented_intent(capsys):
    body = """
Intent: INT-2024-001
## EVALUATION
Priority Score: 3
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_accepts_fullwidth_colon(capsys):
    body = """
Intent：INT-456
## EVALUATION
Priority Score: 1
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert captured.err == ""


def test_validate_pr_body_missing_intent(capsys):
    body = """
## EVALUATION
Priority Score: 2
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR body must include 'Intent: INT-xxx'" in captured.err


def test_validate_pr_body_missing_evaluation(capsys):
    body = """
Intent: INT-001
Priority Score: 3
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR must reference EVALUATION" in captured.err


def test_validate_pr_body_requires_evaluation_heading(capsys):
    body = """
Intent: INT-555
Evaluation anchor is explained here without heading.
"""

    assert validate_pr_body(body) is False
    captured = capsys.readouterr()
    assert "PR must reference EVALUATION" in captured.err


def test_validate_pr_body_warns_without_priority_score(capsys):
    body = """
Intent: INT-789
## EVALUATION
"""

    assert validate_pr_body(body) is True
    captured = capsys.readouterr()
    assert "Consider adding 'Priority Score: <number>'" in captured.err


def test_load_forbidden_patterns(tmp_path):
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        """
self_modification:
  forbidden_paths:
    - "/core/schema/**"
    - '/auth/**'
  require_human_approval:
    - "/governance/**"
"""
    )

    assert load_forbidden_patterns(policy) == ["core/schema/**", "auth/**"]
