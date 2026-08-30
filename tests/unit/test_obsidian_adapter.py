import json

import pytest

from gallop.adapters.obsidian import ObsidianAdapter


def result_payload(integration_test=True):
    return {
        "practice_id": "practice-test",
        "manifest_id": "manifest-test",
        "subject": "mathematics",
        "topic": "fictional topic",
        "questions_attempted": 7,
        "questions_correct": 5,
        "hints_used": 1,
        "mastery_before": 1,
        "mastery_after": 2,
        "mastery_reason": "guided successful performance",
        "completed_at": "2026-01-01T00:00:00Z",
        "integration_test": integration_test,
    }


def test_integration_writeback_is_isolated(tmp_path):
    adapter = ObsidianAdapter(tmp_path)
    path = adapter.write_result(result_payload(), namespace="integration_tests")
    state = json.loads((tmp_path / ".gallop" / "mastery.json").read_text(encoding="utf-8"))
    assert "integration_tests" in state["topics"]
    assert "learner" not in state["topics"]
    assert "not learner evidence" in open(path, encoding="utf-8").read()


def test_unknown_namespace_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unsupported mastery namespace"):
        ObsidianAdapter(tmp_path).write_result(result_payload(), namespace="private")

