"""Four-subject Zero-Touch Golden path over one isolated Gallop runtime."""

from pathlib import Path

from gallop.automation.config import AutomationConfig
from gallop.automation.ports import Clock
from gallop.projections.tutor import session_path
from gallop.tutor import SUBJECT_TUTORS, TutorBridge


class GoldenClock(Clock):
    def __init__(self, value: str):
        self.value = value

    def now(self) -> str:
        return self.value

    def today(self):
        raise AssertionError("Tutor Golden path uses explicit event time")


def configuration(tmp_path: Path) -> AutomationConfig:
    root = tmp_path / "golden-runtime"
    return AutomationConfig.from_dict({
        "namespace": "integration_tests",
        "root": str(root),
        "vault": str(root / "vault"),
        "reader": str(root / "reader" / "Gallop-Reader"),
        "export_state": str(root / "export"),
    })


def event(subject: str, session_id: str, event_type: str, event_id: str,
          occurred_at: str, payload: dict, *, actor: str = "tutor") -> dict:
    return {
        "schema_version": "1.2",
        "event_id": event_id,
        "session_id": session_id,
        "tutor_id": SUBJECT_TUTORS[subject],
        "subject": subject,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "payload": payload,
        "provenance": {
            "actor": actor,
            "recorded_by": SUBJECT_TUTORS[subject],
            "source": "synthetic-four-subject-golden",
            "content_scope": "learning_relevant_only",
            "synthetic": True,
        },
    }


def assessment(subject: str, session_id: str, concept: str, task_type: str,
               suffix: str, *, assisted: bool = False) -> dict:
    payload = {
        "concept_id": concept,
        "capability_id": f"capability.{subject}.golden",
        "task_id": f"task.{subject}.{suffix}",
        "task_type": task_type,
        "attempt_id": f"attempt.{subject}.{suffix}",
        "correctness": "CORRECT",
        "reasoning_quality": "SOLID",
        "evaluator_confidence": "MEDIUM",
        "authority_class": "CANDIDATE_EVIDENCE",
        "evidence_refs": [f"response.{subject}.{suffix}"],
        "agent_usage": "HINT_ONLY" if assisted else "NONE",
        "independence_class": "HINT_1" if assisted else "INDEPENDENT",
        "assistance_level": 1 if assisted else 0,
        "summary": f"Synthetic {subject} assessment for {concept}.",
    }
    if task_type == "PROOF":
        payload["proof_quality"] = {
            "logical_completeness": "SOLID",
            "definition_precision": "SOLID",
            "condition_awareness": "SOLID",
        }
    if task_type == "DERIVATION":
        payload["derivation_quality"] = {
            "steps_valid": "SOLID",
            "assumption_awareness": "SOLID",
            "interpretation": "SOLID",
        }
    return event(
        subject, session_id,
        "candidate_assessment" if assisted else "independent_success",
        f"event.{subject}.{suffix}.assessment", "2026-09-13T10:00:00Z", payload,
    )


def confirmation(candidate: dict, suffix: str) -> dict:
    subject = candidate["subject"]
    return event(
        subject,
        candidate["session_id"],
        "evidence_confirmation",
        f"event.{subject}.{suffix}.confirmation",
        "2026-09-13T10:01:00Z",
        {
            "candidate_event_id": candidate["event_id"],
            "authority_class": "HUMAN_ATTESTATION",
            "summary": "Learner explicitly confirmed authorship in Tutor dialogue.",
        },
        actor="human",
    )


def test_four_subject_golden_loop_restores_and_schedules_without_v1_drift(tmp_path):
    cfg = configuration(tmp_path)
    bridge = TutorBridge.open(cfg)
    bridge.automation.clock = GoldenClock("2026-09-13T09:00:00Z")
    subjects = {
        "mathematics": ("concept.compactness", "PROOF"),
        "statistics": ("concept.bootstrap-inference", "SIMULATION"),
        "finance": ("concept.sdf-euler-equation", "DERIVATION"),
        "cs-ai": ("concept.lock-free-queue", "NO_AGENT_CODING"),
    }
    initial_queue = bridge.automation.state()["queue"]
    for subject, (concept, task_type) in subjects.items():
        session_id = f"session.{subject}.golden"
        opened = bridge.open_or_resume_session(subject, session_id)
        assert opened["context_restore"]["status"] == "PASS"
        if subject == "mathematics":
            hint = event(
                subject, session_id, "hint_given", "event.mathematics.hint",
                "2026-09-13T09:20:00Z",
                {
                    "task_id": "task.mathematics.assisted",
                    "attempt_id": "attempt.mathematics.assisted",
                    "assistance_level": 1,
                    "independence_class": "HINT_1",
                    "agent_usage": "HINT_ONLY",
                    "summary": "One bounded hint was given and retained as provenance.",
                },
            )
            bridge.record_learning_event(hint)
            assisted = assessment(
                subject, session_id, concept, task_type, "assisted", assisted=True
            )
            assisted["occurred_at"] = "2026-09-13T09:30:00Z"
            bridge.record_learning_event(assisted)
            assisted_confirmation = confirmation(assisted, "assisted")
            assisted_confirmation["occurred_at"] = "2026-09-13T09:31:00Z"
            bridge.record_learning_event(assisted_confirmation)
        candidate = assessment(subject, session_id, concept, task_type, "independent")
        bridge.record_learning_event(candidate)
        confirmed = bridge.record_learning_event(confirmation(candidate, "independent"))
        assert confirmed["evidence_confirmed"] is True
        note = cfg.vault / session_path(bridge.get_session(session_id))
        assert note.is_file()
    state = bridge.automation.state()
    assert state["queue"] == initial_queue == {}
    assert len(state["tutor"]["sessions"]) == 4
    assert len(state["elite"]["evidence"]) == 10
    assert all(item["mastery_level"] == 0 for item in state["concepts"].values())
    bridge.close()

    restored = TutorBridge.open(cfg)
    restored.automation.clock = GoldenClock("2026-09-21T12:00:00Z")
    for subject, (concept, _task_type) in subjects.items():
        opened = restored.open_or_resume_session(subject, f"session.{subject}.fresh")
        packet = opened["context"]["payload"]["context_packet"]
        assert opened["context_restore"]["prior_session_count"] == 1
        assert packet["subject"] == subject
        assert packet["active_concept_id"] == concept
        assert packet["current_capability"]["state"] == "PARTIALLY_INDEPENDENT"
        assert any(item["delay_days"] == 7 for item in packet["retests_due"])
        replayed = restored.automation.state()
        assert all(
            replayed["tutor"]["events"][event_id]["subject"] == subject
            for event_id in packet["source_event_ids"]
        )
    final = restored.automation.state()
    assert final["queue"] == initial_queue
    assert len(final["tutor"]["sessions"]) == 8
    assert all(item["mastery_level"] == 0 for item in final["concepts"].values())
    restored.close()
