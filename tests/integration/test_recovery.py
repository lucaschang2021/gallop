import json
from dataclasses import replace

import pytest

from gallop.adapters.mock import DemoPracticeEngine
from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.sync import GallopPipeline


def pipeline(vault):
    return GallopPipeline(ObsidianAdapter(vault), DemoPracticeEngine())


def test_replay_is_noop_and_conflicting_id_rejected(tmp_path, result):
    first = pipeline(tmp_path).import_result(result)
    second = pipeline(tmp_path).import_result(result)
    assert first == second
    with pytest.raises(ValueError, match="different content"):
        pipeline(tmp_path).import_result(replace(result, hints_used=2))
    state = json.loads((tmp_path / ".gallop/mastery.json").read_text())
    assert len(next(iter(state["topics"]["integration_tests"].values()))["history"]) == 1


def test_new_manifest_for_same_topic_keeps_canonical_mastery(tmp_path, result):
    pipeline(tmp_path).import_result(result)
    following = replace(result, practice_id="second", manifest_id="another-manifest",
                        mastery_before=0, completed_at="2026-01-02T12:00:00Z")
    updated = pipeline(tmp_path).import_result(following)
    assert updated["mastery_before"] == 2


def test_claimed_repetition_cannot_award_level_five(tmp_path, result):
    perfect = replace(result, mastery_before=4, hints_used=0, questions_correct=7,
                      metadata={"independent": True, "delayed_recall": True,
                                "transfer_success": True, "oral_explanation": True,
                                "repeated_successes": 999})
    assert pipeline(tmp_path).import_result(perfect)["mastery_after"] == 4


def test_write_failure_preserves_input_and_retry_applies_once(tmp_path, result, monkeypatch):
    import gallop.adapters.obsidian.adapter as module
    original = module.atomic_json
    def broken(path, value):
        raise OSError("simulated-write-failure")
    monkeypatch.setattr(module, "atomic_json", broken)
    with pytest.raises(OSError):
        pipeline(tmp_path).import_result(result)
    pending = tmp_path / ".gallop/pending/integration_tests" / f"{result.practice_id}.json"
    assert pending.exists()
    monkeypatch.setattr(module, "atomic_json", original)
    assert pipeline(tmp_path).import_result(result)["mastery_after"] == 2
    assert not pending.exists()


def test_out_of_order_rejected(tmp_path, result):
    pipeline(tmp_path).import_result(result)
    with pytest.raises(ValueError, match="Out-of-order"):
        pipeline(tmp_path).import_result(replace(result, practice_id="older"))


def test_independence_is_not_inferred_from_zero_hints(tmp_path, result):
    unobserved = replace(result, mastery_before=3, hints_used=0, questions_correct=7, metadata={})
    assert pipeline(tmp_path).import_result(unobserved)["mastery_after"] == 3


def test_synthetic_actor_cannot_write_learner_state(tmp_path, result):
    with pytest.raises(ValueError, match="Synthetic"):
        pipeline(tmp_path).import_result(replace(result, integration_test=False))


def test_boolean_strings_rejected(tmp_path, result):
    with pytest.raises(ValueError, match="booleans"):
        pipeline(tmp_path).import_result(replace(result, metadata={"independent": "false"}))
