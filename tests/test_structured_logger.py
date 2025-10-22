from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.perf.structured_logger import InferenceLogRecord, StructuredLogger


@pytest.mark.usefixtures("tmp_path")
def test_structured_logger_writes_json_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "chainlit.log"
    logger = StructuredLogger(log_path)

    logger.log_inference(
        InferenceLogRecord(
            session_id="session-1",
            metrics={
                "semantic_retention": 0.74,
                "spec_completeness": {"with_spec": 91, "total": 100},
            },
            metadata={"reviewer": "alice"},
        )
    )
    logger.log_inference(
        InferenceLogRecord(
            session_id="session-1",
            metrics={"review_latency": 0.5},
        )
    )

    contents = log_path.read_text(encoding="utf-8").splitlines()
    assert len(contents) == 2

    first = json.loads(contents[0])
    second = json.loads(contents[1])

    assert first["session_id"] == "session-1"
    assert first["metrics"]["semantic_retention"] == pytest.approx(0.74)
    assert first["metrics"]["spec_completeness"] == {"with_spec": 91, "total": 100}
    assert first["metadata"] == {"reviewer": "alice"}

    assert second["metrics"]["review_latency"] == pytest.approx(0.5)
    assert second.get("metadata") is None
