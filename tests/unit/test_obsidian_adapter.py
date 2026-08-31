import json
from pathlib import Path

import pytest

from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.validation import validate_protocol


def result_payload():
    path = Path(__file__).parents[2] / "examples/mathematics/practice-result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_integration_writeback_is_isolated(tmp_path):
    adapter = ObsidianAdapter(tmp_path)
    path = adapter.write_result(result_payload(), namespace="integration_tests")
    state = json.loads((tmp_path / ".gallop/mastery.json").read_text(encoding="utf-8"))
    assert "learner" not in state["topics"]
    topic = next(iter(state["topics"]["integration_tests"].values()))
    validate_protocol("mastery.schema.json", topic)
    assert topic["confidence"] is None
    assert "not learner evidence" in Path(path).read_text(encoding="utf-8")
    assert "T+30" in Path(path).read_text(encoding="utf-8")


def test_unknown_namespace_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="unsupported mastery namespace"):
        ObsidianAdapter(tmp_path).write_result(result_payload(), namespace="private")


def test_test_result_cannot_enter_learner_namespace(tmp_path):
    with pytest.raises(ValueError, match="namespace mismatch"):
        ObsidianAdapter(tmp_path).write_result(result_payload(), namespace="learner")


def test_path_traversal_rejected(tmp_path):
    result = result_payload()
    result["practice_id"] = "../../escape"
    with pytest.raises(ValueError):
        ObsidianAdapter(tmp_path).write_result(result, namespace="integration_tests")
    assert not (tmp_path / "escape.md").exists()


def test_external_state_path_rejected(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        ObsidianAdapter(tmp_path / "vault", state_path=tmp_path / "outside.json")


def test_store_lock_prevents_concurrent_writer(tmp_path):
    first, second = ObsidianAdapter(tmp_path), ObsidianAdapter(tmp_path)
    with first.transaction():
        with pytest.raises(RuntimeError, match="busy"):
            with second.transaction():
                pass
