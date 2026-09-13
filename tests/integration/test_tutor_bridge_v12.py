from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from gallop.automation.config import AutomationConfig
from gallop.automation.ports import Clock
from gallop.automation.store import JournalConflict
from gallop.tutor import SUBJECT_TUTORS, TutorBridge
from gallop.projections.tutor import concept_path, mistake_path, session_path


ROOT = Path(__file__).parents[2]


class FixedClock(Clock):
    def now(self) -> str:
        return "2026-09-13T11:00:00Z"

    def today(self):
        raise AssertionError("Runtime bridge does not need the current date")


def config(tmp_path: Path) -> AutomationConfig:
    root = tmp_path / "runtime"
    return AutomationConfig.from_dict({
        "namespace": "integration_tests",
        "root": str(root),
        "vault": str(root / "vault"),
        "reader": str(root / "reader" / "Gallop-Reader"),
        "export_state": str(root / "export"),
    })


def tutor_event(
    event_type: str,
    *,
    event_id: str,
    session_id: str = "session.math.001",
    subject: str = "mathematics",
) -> dict:
    payload = {
        "summary": "Synthetic incremental checkpoint.",
        "checkpoint_reason": "Learner submitted a meaningful attempt.",
    }
    if event_type in {"candidate_assessment", "independent_success"}:
        payload.update({
            "concept_id": "concept.synthetic-proof",
            "capability_id": "capability.proof",
            "task_id": "task.math.proof.001",
            "task_type": "PROOF",
            "attempt_id": "attempt.math.proof.001",
            "correctness": "CORRECT",
            "reasoning_quality": "SOLID",
            "evaluator_confidence": "MEDIUM",
            "authority_class": "CANDIDATE_EVIDENCE",
            "evidence_refs": ["response.math.proof.001"],
            "agent_usage": "NONE",
            "independence_class": "INDEPENDENT",
            "assistance_level": 0,
        })
    return {
        "schema_version": "1.2",
        "event_id": event_id,
        "session_id": session_id,
        "tutor_id": SUBJECT_TUTORS[subject],
        "subject": subject,
        "event_type": event_type,
        "occurred_at": "2026-09-13T11:01:00Z",
        "payload": payload,
        "provenance": {
            "actor": "tutor",
            "recorded_by": SUBJECT_TUTORS[subject],
            "source": "synthetic-bridge-test",
            "content_scope": "learning_relevant_only",
            "synthetic": True,
        },
    }


def open_bridge(cfg: AutomationConfig) -> TutorBridge:
    bridge = TutorBridge.open(cfg)
    bridge.automation.clock = FixedClock()
    return bridge


def test_bridge_construction_is_side_effect_free(tmp_path):
    cfg = config(tmp_path)
    from gallop.automation.service import Automation

    TutorBridge(Automation(cfg, clock=FixedClock()))
    assert not cfg.root.exists()


@pytest.mark.parametrize("subject", SUBJECT_TUTORS)
def test_one_runtime_opens_and_resumes_all_four_subjects(tmp_path, subject):
    bridge = open_bridge(config(tmp_path))
    session_id = f"session.{subject}.001"
    first = bridge.open_or_resume_session(subject, session_id)
    second = bridge.open_or_resume_session(subject, session_id)
    assert first["created"] is True
    assert second == {"created": False, "session": first["session"]}
    assert first["session"]["tutor_id"] == SUBJECT_TUTORS[subject]
    bridge.close()


def test_incremental_checkpoint_is_durable_before_finalize(tmp_path):
    cfg = config(tmp_path)
    bridge = open_bridge(cfg)
    bridge.open_or_resume_session("mathematics", "session.math.001")
    checkpoint = tutor_event("checkpoint", event_id="event.math.checkpoint.001")
    recorded = bridge.checkpoint_session(checkpoint)
    assert recorded["durable"] is True and recorded["duplicate"] is False
    bridge.close()

    restored = open_bridge(cfg)
    session = restored.get_session("session.math.001")
    assert session["checkpoint_event_ids"] == ["event.math.checkpoint.001"]
    assert session["status"] == "active"
    restored.close()


def test_exact_retry_is_idempotent_and_changed_content_conflicts(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    document = tutor_event("checkpoint", event_id="event.math.checkpoint.001")
    first = bridge.record_learning_event(document)
    second = bridge.record_learning_event(deepcopy(document))
    assert first["journal_event_id"] == second["journal_event_id"]
    assert first["duplicate"] is False and second["duplicate"] is True
    changed = deepcopy(document)
    changed["payload"]["summary"] = "Changed content under the same event ID."
    with pytest.raises(JournalConflict, match="reused with different content"):
        bridge.record_learning_event(changed)
    bridge.close()


def test_finalize_is_idempotent_and_does_not_erase_checkpoints(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    bridge.checkpoint_session(tutor_event("checkpoint", event_id="event.math.checkpoint.001"))
    final = tutor_event("session_finalize", event_id="event.math.finalize.001")
    first = bridge.finalize_session(final)
    second = bridge.finalize_session(deepcopy(final))
    session = bridge.get_session("session.math.001")
    assert first["duplicate"] is False and second["duplicate"] is True
    assert session["status"] == "finalized"
    assert session["checkpoint_event_ids"] == ["event.math.checkpoint.001"]
    bridge.close()


def test_tutor_events_cannot_change_mastery_or_v1_queue(tmp_path):
    bridge = open_bridge(config(tmp_path))
    before = bridge.automation.state()
    bridge.open_or_resume_session("mathematics", "session.math.001")
    bridge.checkpoint_session(tutor_event("checkpoint", event_id="event.math.checkpoint.001"))
    after = bridge.automation.state()
    assert after["concepts"] == before["concepts"]
    assert after["queue"] == before["queue"]
    assert "tutor" not in before and len(after["tutor"]["events"]) == 2
    bridge.close()


@pytest.mark.parametrize("event_type", ["candidate_assessment", "independent_success"])
def test_tutor_assessment_is_incremental_unconfirmed_elite_evidence(tmp_path, event_type):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    document = tutor_event(event_type, event_id=f"event.math.{event_type}.001")
    first = bridge.record_learning_event(document)
    second = bridge.record_learning_event(deepcopy(document))
    state = bridge.automation.state()
    evidence = state["elite"]["evidence"][first["candidate_evidence_id"]]
    concept = next(item for item in state["concepts"].values()
                   if item["concept"] == "concept.synthetic-proof")
    assert first["evidence_confirmed"] is False
    assert first["evidence_duplicate"] is False and second["evidence_duplicate"] is True
    assert evidence["confirmed"] is False
    assert evidence["record"]["metadata"]["tutor_event_id"] == document["event_id"]
    assert concept["mastery_level"] == 0
    assert state["queue"] == {}
    bridge.close()


def test_submission_without_assessment_does_not_create_evidence(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    document = tutor_event("proof_submission", event_id="event.math.proof.001")
    document["payload"].update({
        "task_id": "task.math.proof.001",
        "attempt_id": "attempt.math.proof.001",
        "learner_response_reference": "response://synthetic/proof-001",
    })
    result = bridge.record_learning_event(document)
    assert "candidate_evidence_id" not in result
    assert "elite" not in bridge.automation.state()
    bridge.close()


def test_invalid_candidate_taxonomy_rolls_back_before_journal_append(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    before = bridge.automation.store.events()
    document = tutor_event("candidate_assessment", event_id="event.math.bad-taxonomy.001")
    document["payload"]["failure_tags"] = ["math:NOT_REGISTERED"]
    with pytest.raises(ValueError, match="Unregistered failure mode"):
        bridge.record_learning_event(document)
    assert bridge.automation.store.events() == before
    bridge.close()


def test_session_identity_and_operation_names_fail_closed(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("finance", "session.shared.001")
    with pytest.raises(JournalConflict, match="another subject"):
        bridge.open_or_resume_session("mathematics", "session.shared.001")
    with pytest.raises(ValueError, match="Unknown Gallop tutor operation"):
        bridge.dispatch("delete_history", {})
    bridge.close()


def test_second_start_backward_time_and_post_finalize_events_fail(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    second_start = tutor_event("session_start", event_id="event.math.start.002")
    with pytest.raises(JournalConflict, match="already open"):
        bridge.record_learning_event(second_start)
    backward = tutor_event("checkpoint", event_id="event.math.old.001")
    backward["occurred_at"] = "2026-09-13T10:59:59Z"
    with pytest.raises(JournalConflict, match="chronology"):
        bridge.record_learning_event(backward)
    bridge.finalize_session(tutor_event("session_finalize", event_id="event.math.finalize.001"))
    later = tutor_event("checkpoint", event_id="event.math.later.001")
    later["occurred_at"] = "2026-09-13T11:02:00Z"
    with pytest.raises(JournalConflict, match="Finalized"):
        bridge.record_learning_event(later)
    bridge.close()


def test_bridge_import_has_no_deeptutor_dependency_or_filesystem_effect(tmp_path):
    script = (
        "import json,sys; import gallop.tutor.bridge; "
        "print(json.dumps({'deeptutor': 'gallop.adapters.deeptutor' in sys.modules}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={"PYTHONPATH": str(ROOT)},
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == {"deeptutor": False}
    assert list(tmp_path.iterdir()) == []


def test_incremental_events_automatically_project_bounded_human_records(tmp_path):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    task = tutor_event("task_issued", event_id="event.math.task.001")
    task["payload"].update({
        "concept_id": "concept.synthetic-proof",
        "task_id": "task.math.proof.001",
        "task_type": "PROOF",
        "prompt_reference": "prompt://private/not-projected",
    })
    attempt = tutor_event("proof_submission", event_id="event.math.attempt.001")
    attempt["payload"].update({
        "concept_id": "concept.synthetic-proof",
        "task_id": "task.math.proof.001",
        "attempt_id": "attempt.math.proof.001",
        "learner_response_reference": "response://private/not-projected",
    })
    hint = tutor_event("hint_given", event_id="event.math.hint.001")
    hint["payload"].update({
        "task_id": "task.math.proof.001",
        "attempt_id": "attempt.math.proof.001",
        "assistance_level": 1,
        "independence_class": "HINT_1",
    })
    mistake = tutor_event("mistake_observed", event_id="event.math.mistake.001")
    mistake["payload"].update({
        "concept_id": "concept.synthetic-proof",
        "attempt_id": "attempt.math.proof.001",
        "failure_tags": ["math:PROOF_INCOMPLETE"],
    })
    candidate = tutor_event("candidate_assessment", event_id="event.math.assessment.001")
    for document in (task, attempt, hint, mistake, candidate):
        assert bridge.record_learning_event(document)["projection"]["status"] == "PASS"

    state = bridge.automation.state()
    session = bridge.get_session("session.math.001")
    session_note = bridge.automation.config.vault / session_path(session)
    concept_note = bridge.automation.config.vault / concept_path(
        "mathematics", "concept.synthetic-proof"
    )
    mistake_note = bridge.automation.config.vault / mistake_path(mistake)
    assert session_note.is_file() and concept_note.is_file() and mistake_note.is_file()
    body = session_note.read_text(encoding="utf-8")
    assert "attempt.math.proof.001" in body
    assert "Candidate Evidence" in body and "event.math.assessment.001" in body
    assert "response://private/not-projected" not in body
    assert "prompt://private/not-projected" not in body
    assert state["concepts"][next(iter(state["concepts"]))]["mastery_level"] == 0
    bridge.close()


def test_projection_failure_reports_failed_but_keeps_journal_and_retries(tmp_path, monkeypatch):
    bridge = open_bridge(config(tmp_path))
    bridge.open_or_resume_session("mathematics", "session.math.001")
    before = len(bridge.automation.store.events())
    import gallop.automation.views as views

    original = views.atomic_text

    def fail_projection(*_args, **_kwargs):
        raise OSError("simulated projection failure")

    monkeypatch.setattr(views, "atomic_text", fail_projection)
    document = tutor_event("checkpoint", event_id="event.math.checkpoint.projection-failure")
    result = bridge.record_learning_event(document)
    assert result["projection"] == {
        "status": "FAILED", "error_type": "OSError", "journal_durable": True
    }
    assert len(bridge.automation.store.events()) == before + 1
    assert document["event_id"] in bridge.get_session("session.math.001")["event_ids"]
    monkeypatch.setattr(views, "atomic_text", original)
    assert bridge.automation.project()["written"] >= 1
    bridge.close()
