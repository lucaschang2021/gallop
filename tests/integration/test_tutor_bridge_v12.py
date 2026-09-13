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
