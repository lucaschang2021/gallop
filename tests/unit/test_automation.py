import copy
from datetime import date
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.automation.config import AutomationConfig
from gallop.automation.protocol import ARRAYS, canonical, now, normalize_session
from gallop.automation.service import Automation
from gallop.automation.state import POLICIES, blank, mastery_gate, replay, training_candidate
from gallop.automation.store import JournalConflict
from gallop.automation.views import START, END


def session(**changes):
    return {"schema_version": "1.0", "session_id": "synthetic-session-01",
            "tutor": "mathematics", "course": "Synthetic Analysis", "title": "Synthetic continuity lesson",
            "occurred_at": "2026-01-01T10:00:00Z", "summary": "Fictional protocol example.",
            **{field: [] for field in ARRAYS}, "concepts": [{"name": "Continuity", "definition": "Synthetic"}],
            "weakness_tags": ["quantifiers"], **changes}


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("gallop.automation.service.now", lambda: "2026-01-01T10:30:00Z")
    root = tmp_path / "isolated"
    cfg = AutomationConfig.from_dict({"namespace": "integration_tests", "root": str(root),
        "vault": str(root / "vault"), "reader": str(root / "reader/Gallop-Reader"),
        "export_state": str(root / "export")})
    instance = Automation(cfg)
    yield instance
    instance.close()


def put(app, document, name="input.json"):
    path = app.config.root / name
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def accept(app, document=None):
    return app.intake(put(app, document or session()))


def work(app):
    accept(app)
    q = next(q for q in app.queue() if q["status"] == "queued")
    p = app.prepare(q["queue_id"])
    app.start(q["queue_id"], confirm=True)
    return q, p


def result(q, p, **changes):
    return dict(schema_version="1.0", result_id="synthetic-result-01", queue_id=q["queue_id"],
        manifest_id=p["manifest_id"], practice_id=p["practice_id"], subject=q["subject"],
        concept=q["concept"], namespace="integration_tests", integration_test=True,
        evidence_kind=q["training_type"], outcome="pass", questions_attempted=7,
        questions_correct=7, hints_used=0, independent=True, transfer=False, grader="human",
        response_refs=["synthetic-answer-01"], weakness_tags=[], mistakes=[], open_questions=[],
        started_at="2026-01-01T11:00:00Z", completed_at="2026-01-01T12:00:00Z",
        grading_reason="Synthetic fixture, not a real learner.", **changes)


def test_intake_protocol_compatible_objects_optional_arrays_and_fenced_json(app):
    minimal = {k: v for k, v in session().items() if k in {"tutor", "title", "occurred_at", "summary"}}
    normalized = normalize_session(minimal)
    assert all(normalized[a] == [] for a in ARRAYS)
    path = put(app, session())
    fence = chr(96) * 3
    path.write_text(fence + "json\n" + path.read_text(encoding="utf-8") + "\n" + fence, encoding="utf-8")
    app.intake(path)
    item = app.explain("Continuity")
    assert item["mastery_level"] == 0 and item["confidence"] == "low"
    assert item["evidence_refs"] and item["history"][0]["reason"]


def test_unnamed_protocol_observations_retained_without_inventing_concepts(app):
    value = session(concepts=[{"definition": "An unnamed observation"}, {"name": ""}])
    accepted = accept(app, value)
    assert app.state()["sessions"][accepted["event_id"]]["concepts"] == value["concepts"]
    assert not app.state()["concepts"]


@pytest.mark.parametrize("changes", [
    {"tutor": "unknown"}, {"occurred_at": "2026-01-01T10:00:00"},
    {"occurred_at": "bad"}, {"concepts": 5}, {"weakness_tags": [1]},
    {"schema_version": "2.0"}, {"subject": "finance"},
])
def test_schema_rejection_retains_raw_without_validated_state(app, changes):
    with pytest.raises(ValueError):
        accept(app, session(**changes))
    assert not app.store.events()
    assert app.store.db.execute("SELECT count(*) FROM raw_inputs").fetchone()[0] == 1


@pytest.mark.parametrize("raw", [b'{"x":', b'{"a":1,"a":2}', b'{"a":NaN}', b"[]"])
def test_malformed_json_is_not_an_event(app, raw):
    path = app.config.root / "bad.json"
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        app.intake(path)
    assert not app.store.events()
    assert app.store.db.execute("SELECT body FROM raw_inputs").fetchone()[0] == raw


def test_duplicate_and_conflicting_session_are_atomic(app):
    first = accept(app)
    before = app.state()
    assert accept(app)["duplicate"] is True
    assert app.state() == before
    with pytest.raises(JournalConflict):
        accept(app, session(summary="Different body"))
    assert app.state() == before
    assert first["event_id"] in app.explain("Continuity")["evidence_refs"]


def test_events_raw_immutability_and_replay(app):
    accept(app)
    for sql in ("DELETE FROM events", "UPDATE events SET source='x'",
                "DELETE FROM raw_inputs", "UPDATE raw_inputs SET body=x'00'"):
        with pytest.raises(sqlite3.IntegrityError):
            app.store.db.execute(sql)
    assert replay(app.store.events()) == app.state()
    events = app.store.events()
    events[-1]["kind"] = "unknown"
    with pytest.raises(JournalConflict):
        replay(events)


def test_namespace_root_cannot_be_rebound_or_point_to_real_targets(app, tmp_path):
    data = {k: str(v) if isinstance(v, Path) else v for k, v in app.config.__dict__.items()}
    data["reader"] = str(tmp_path / "outside/Gallop-Reader")
    with pytest.raises(ValueError):
        AutomationConfig.from_dict(data)
    data["reader"] = str(app.config.reader)
    data["vault"] = str(app.config.root / "other-vault")
    with pytest.raises(ValueError):
        Automation(AutomationConfig.from_dict(data))


def test_learner_rejects_synthetic_envelope_before_state(tmp_path):
    vault = tmp_path / "real-vault"
    (vault / ".obsidian").mkdir(parents=True)
    root = tmp_path / "private"
    cfg = AutomationConfig.from_dict(dict(root=str(root), vault=str(vault),
        reader=str(tmp_path / "reader/Gallop-Reader"), export_state=str(root / "export"), namespace="learner"))
    app = Automation(cfg)
    try:
        with pytest.raises(ValueError):
            accept(app, session(integration_test=True))
        assert app.state()["concepts"] == {}
        assert list(vault.iterdir()) == [vault / ".obsidian"]
        with pytest.raises(ValueError):
            app.publish()
    finally:
        app.close()


def test_single_perfect_result_never_means_mastered_and_duplicate_does_not_count(app):
    q, p = work(app)
    path = put(app, result(q, p), "result.json")
    assert app.ingest_result(path, confirm_human=True)["duplicate"] is False
    after = app.state()
    assert app.explain("Continuity")["mastery_level"] == 0
    assert app.explain("Continuity")["success_count"] == 1
    assert app.ingest_result(path, confirm_human=True)["duplicate"] is True
    assert app.state() == after


def test_no_automatic_start_or_llm_only_grading(app):
    accept(app)
    q = app.queue()[0]
    p = app.prepare(q["queue_id"])
    assert app.state()["queue"][q["queue_id"]]["status"] == "ready"
    with pytest.raises(ValueError):
        app.start(q["queue_id"])
    with pytest.raises(ValueError):
        app.ingest_result(put(app, result(q, p)), confirm_human=True)
    app.start(q["queue_id"], confirm=True)
    before = app.state()
    with pytest.raises(ValueError):
        app.ingest_result(put(app, result(q, p)))
    assert app.state() == before


@pytest.mark.parametrize("field,value", [
    ("manifest_id", "wrong"), ("concept", "Other"), ("evidence_kind", "coding"),
    ("namespace", "learner"), ("questions_correct", 8), ("grader", "llm"),
    ("response_refs", []), ("completed_at", "2025-12-31T00:00:00Z"),
])
def test_invalid_practice_result_no_partial_mutation(app, field, value):
    q, p = work(app)
    data = result(q, p)
    data[field] = value
    before = app.state()
    with pytest.raises((ValueError, KeyError)):
        app.ingest_result(put(app, data), confirm_human=True)
    assert app.state() == before


def test_failure_increases_weakness_and_does_not_clear_mastery(app):
    q, p = work(app)
    data = result(q, p)
    data.update(outcome="fail", questions_correct=1, mistakes=["Synthetic counterexample omitted"])
    app.ingest_result(put(app, data), confirm_human=True)
    item = app.explain("Continuity")
    assert item["mistake_count"] == 1 and "proof-failure" in item["weakness_tags"]
    assert mastery_gate(4, [], "fail")[0] == 4
    assert item["history"][-1]["evidence_refs"]


def test_mastery_gate_requires_multiple_days_and_types_caps_each_transition():
    successes = []
    level = 0
    for index, kind in enumerate(["proof", "practice", "oral_exam", "simulation", "coding"]):
        successes.append(dict(at=f"2026-0{index+1}-01T12:00:00Z", kind=kind,
                              independent=True, hints_used=0, transfer=index == 4))
        next_level, _ = mastery_gate(level, successes, "pass")
        assert next_level <= level + 1
        level = next_level
    assert level == 4
    assert mastery_gate(4, successes, "pass")[0] == 5
    assert mastery_gate(4, [{**s, "kind": "practice"} for s in successes], "pass")[0] == 4
    assert mastery_gate(2, [{**s, "hints_used": 1} for s in successes], "pass")[0] == 2


@pytest.mark.parametrize("subject,first", [("mathematics", "proof"), ("statistics", "simulation"),
                                         ("finance", "conceptual"), ("cs-ai", "coding")])
def test_subject_policy_and_priority(subject, first):
    item = blank(subject, "Synthetic")
    item.update(last_seen="2026-01-01T00:00:00Z", evidence_refs=["session-1"])
    assert training_candidate(item, date(2026, 1, 1))["training_type"] == first
    assert training_candidate(item, date(2026, 1, 1))["priority"] == "P2"
    item["weakness_tags"] = ["prerequisite-failure"]
    assert training_candidate(item, date(2026, 1, 1))["priority"] == "P0"
    item.update(weakness_tags=[], mistake_count=2)
    assert training_candidate(item, date(2026, 1, 1))["priority"] == "P1"
    item.update(mistake_count=0, confidence="medium")
    assert training_candidate(item, date(2026, 1, 2))["priority"] == "P3"
    assert training_candidate(item, date(2026, 1, 1))["priority"] == "P4"


def test_prepare_uses_existing_deeptutor_transport_and_stable_linkage(app, tmp_path):
    accept(app)
    q = app.queue()[0]
    executable = tmp_path / "deeptutor.exe"
    executable.write_bytes(b"test-only")
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        data = {"questions": [{"question": f"Synthetic question {i}", "correct_answer": "A"} for i in range(7)]}
        return subprocess.CompletedProcess(command, 0, json.dumps(data), "")
    prepared = app.prepare(q["queue_id"], send=True, engine=DeepTutorAdapter(executable, runner=runner))
    assert calls[0][1:3] == ["run", "deep_question"]
    assert prepared["queue_id"] == q["queue_id"]
    assert prepared["manifest"]["practice_modes"] == ["proof"]
    assert "never proof" in prepared["practice"]["notice"]
    assert app.prepare(q["queue_id"]) == prepared
    assert len(calls) == 1
    assert not app.state()["results"]
    assert app.explain("Continuity")["mastery_level"] == 0


def test_backend_failure_only_changes_queue_status(app):
    accept(app)
    q = app.queue()[0]
    before = copy.deepcopy(app.state()["concepts"])
    class FailedEngine:
        def generate(self, manifest):
            raise RuntimeError("provider failed")
    with pytest.raises(RuntimeError):
        app.prepare(q["queue_id"], send=True, engine=FailedEngine())
    assert app.state()["concepts"] == before
    assert app.state()["queue"][q["queue_id"]]["status"] == "failed"
    app.retry(q["queue_id"])
    assert app.state()["queue"][q["queue_id"]]["status"] == "queued"
    prepared = app.prepare(q["queue_id"])
    practice_path = app.config.root / "prepared" / q["queue_id"] / "practice.json"
    practice_path.unlink()
    assert app.prepare(q["queue_id"]) == prepared
    assert practice_path.is_file()


def test_projection_preserves_user_regions_and_detects_managed_edits(app):
    accept(app)
    home = app.config.vault / "01-Mathematics/Home.md"
    home.parent.mkdir()
    home.write_text("User's private home introduction.\n", encoding="utf-8")
    app.project()
    assert home.read_text(encoding="utf-8").startswith("User's private home introduction.\n")
    before = home.read_bytes()
    assert app.project()["written"] == 0
    assert home.read_bytes() == before
    home.write_text(home.read_text(encoding="utf-8").replace("level 0", "level 5"), encoding="utf-8")
    changed = home.read_bytes()
    with pytest.raises(ValueError):
        app.project()
    assert home.read_bytes() == changed


def test_rebuild_detects_corruption_and_recovers_stale_cache(app):
    accept(app)
    original = app.cache.read_bytes()
    state = json.loads(original)
    key = next(iter(state["concepts"]))
    state["concepts"][key]["mastery_level"] = 5
    app.cache.write_text(json.dumps(state), encoding="utf-8")
    corrupted = app.cache.read_bytes()
    with pytest.raises(JournalConflict):
        app.rebuild_state()
    assert app.cache.read_bytes() == corrupted
    assert list((app.config.root / "recovery").glob("derived-*.json"))
    app.cache.write_bytes(original)
    accept(app, session(session_id="second", title="Second exposure"))
    app.cache.write_bytes(original)
    report = app.rebuild_state()
    assert report["comparison"] == "verified-prefix"
    assert len(app.state()["sessions"]) == 2


def test_cycle_idempotency_and_reader_filtering(app):
    inbox = app.config.root / "pending-intake"
    inbox.mkdir()
    (inbox / "lesson.json").write_text(json.dumps(session()), encoding="utf-8")
    first = app.cycle()
    before = app.state()
    second = app.cycle()
    assert app.state() == before and second["training_started"] is False
    assert second["projection"]["written"] == 0 and second["publish"]["written"] == 0
    assert first["publish"]["written"] > 2
    today = (app.config.reader / "Today.md").read_text(encoding="utf-8")
    assert "Today's Training" in today and "Weakest Concepts" in today
    assert not list(app.config.reader.rglob("*.json"))
    root = app.config.vault / "Gallop/Automation"
    (root / "private.md").write_text(START + "\npassword: FAKE_TEST_VALUE\n" + END, encoding="utf-8")
    from gallop.automation.views import collect_views
    assert "Gallop/Automation/private.md" not in collect_views(app.config.vault)
    assert not any(q["status"] in {"in_progress", "completed"} for q in app.queue())


def test_legacy_reader_export_preserves_automation_today_and_rejects_synthetic_flags(app):
    accept(app)
    app.publish()
    before = (app.config.reader / "Today.md").read_bytes()
    from gallop.mobile import export_mobile
    report = export_mobile(app.config.vault, app.config.reader, app.config.export_state)
    assert (app.config.reader / "Today.md").read_bytes() == before
    assert report["written"] == 0
    forbidden = app.config.vault / "Gallop/Automation/forbidden.md"
    forbidden.write_text(START + "\nintegration_test: true\nSynthetic test data\n" + END, encoding="utf-8")
    app.publish()
    assert not (app.config.reader / "Gallop/Automation/forbidden.md").exists()


def test_new_result_id_cannot_recount_same_practice(app):
    q, p = work(app)
    data = result(q, p)
    app.ingest_result(put(app, data), confirm_human=True)
    before = app.state()
    data["result_id"] = "another-id-same-practice"
    with pytest.raises(JournalConflict):
        app.ingest_result(put(app, data), confirm_human=True)
    assert app.state() == before


def test_result_before_confirmed_start_and_missing_human_evidence_fail(app):
    q, p = work(app)
    data = result(q, p)
    data["started_at"] = "2026-01-01T09:00:00Z"
    before = app.state()
    with pytest.raises(ValueError):
        app.ingest_result(put(app, data), confirm_human=True)
    assert app.state() == before
    data.update(outcome="ungraded", grader="ungraded")
    with pytest.raises(ValueError):
        app.ingest_result(put(app, data), confirm_human=True)
    assert app.state() == before


def test_writer_collision_preflight_and_operation_lock(app):
    accept(app)
    path = app.config.vault / "Gallop/Automation/Today.md"
    path.parent.mkdir(parents=True)
    path.write_text("User-owned note", encoding="utf-8")
    with pytest.raises(ValueError):
        app.project()
    assert path.read_text(encoding="utf-8") == "User-owned note"
    assert not (app.config.vault / "Today.md").exists()
    lock = app.config.root / "operation.lock"
    lock.write_text("Other process")
    with pytest.raises(FileExistsError):
        app.cycle()
    assert lock.read_text() == "Other process"
    lock.unlink()


def test_atomic_journal_rolls_back_event_and_transitions_on_failure(app, monkeypatch):
    original = app.store.append
    def fail(kind, *args, **kwargs):
        if kind == "state_transition":
            raise OSError("simulated storage failure")
        return original(kind, *args, **kwargs)
    monkeypatch.setattr(app.store, "append", fail)
    with pytest.raises(OSError):
        accept(app)
    assert app.store.events() == []
    assert app.store.db.execute("SELECT count(*) FROM raw_inputs").fetchone()[0] == 1


def test_cache_write_failure_replays_committed_event(app, monkeypatch):
    import gallop.automation.service as service
    original = service.atomic_json
    def fail(path, value):
        if path == app.cache:
            raise OSError("simulated cache write failure")
        return original(path, value)
    monkeypatch.setattr(service, "atomic_json", fail)
    with pytest.raises(OSError):
        accept(app)
    assert len(app.state()["sessions"]) == 1
    monkeypatch.setattr(service, "atomic_json", original)
    assert accept(app)["duplicate"]
    assert len(app.state()["sessions"]) == 1
    assert app.cache.exists()


def test_confidence_can_fall_without_erasing_established_mastery(app):
    # Feed immutable synthetic events through the same reducer, including separate days/types.
    events = []
    def event(kind, data, index):
        return {"kind": kind, "payload": data, "event_id": f"e-{index}", "timestamp": data["completed_at"],
                "seq": index, "hash": str(index)}
    for index, kind in enumerate(["proof", "oral_exam", "coding"], 1):
        data = dict(subject="mathematics", concept="C", result_id=f"r{index}",
                    completed_at=f"2026-0{index}-01T12:00:00Z", outcome="pass", evidence_kind=kind,
                    independent=True, hints_used=0, transfer=False, grading_reason="Synthetic confirmed",
                    weakness_tags=[], open_questions=[], mistakes=[])
        events.append(event("assessment", data, index))
    state = replay(events, verify=False)
    item = next(iter(state["concepts"].values()))
    assert item["mastery_level"] == 2 and item["confidence"] == "medium"
    data = {**data, "completed_at": "2026-04-01T12:00:00Z", "outcome": "fail"}
    events.append(event("assessment", data, 4))
    item = next(iter(replay(events, verify=False)["concepts"].values()))
    assert item["mastery_level"] == 2 and item["confidence"] == "low"


def test_session_review_dates_preserve_t_plus_schedule_and_completed_slots():
    item = blank("finance", "Synthetic concept")
    item.update(last_seen="2026-01-01T01:00:00+08:00", evidence_refs=["session-1"],
                confidence="medium", last_practiced="2026-01-07T12:00:00Z",
                observations=[{"kind": "course_exposure", "at": "2026-01-01T01:00:00+08:00", "source": "session-1"}])
    first = training_candidate(item, date(2026, 1, 2))
    assert "T+1 due 2026-01-02" in first["reason"]
    second = training_candidate(item, date(2026, 1, 8), {first["review_key"]})
    assert "T+7 due 2026-01-08" in second["reason"]
    third = training_candidate(item, date(2026, 1, 31), {first["review_key"], second["review_key"]})
    assert "T+30 due 2026-01-31" in third["reason"]
