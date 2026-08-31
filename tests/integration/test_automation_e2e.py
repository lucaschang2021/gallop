"""Synthetic Golden CLI chain, with the real adapter parsing controlled provider output."""
import json
from pathlib import Path
import subprocess

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.automation.config import AutomationConfig
from gallop.automation.service import Automation
from gallop.automation.jobs import Jobs
from gallop.core.io import atomic_json
from gallop.cli import main


def test_golden_cli_end_to_end_and_external_vault_unchanged(tmp_path, monkeypatch, capsys):
    root = tmp_path / "isolated"
    untouched = tmp_path / "real-masterystate.json"
    untouched.write_bytes(b'{"real":"keep unchanged"}')
    original = untouched.read_bytes()
    config = tmp_path / "automation.json"
    executable = tmp_path / "deeptutor.exe"
    executable.write_bytes(b"controlled test transport")
    config.write_text(json.dumps(dict(namespace="integration_tests", root=str(root),
        vault=str(root / "vault"), reader=str(root / "reader/Gallop-Reader"),
        export_state=str(root / "export"), deeptutor=str(executable))), encoding="utf-8")
    monkeypatch.setattr("gallop.automation.service.now", lambda: "2026-01-01T10:30:00Z")
    def runner(command, **kwargs):
        assert kwargs["shell"] is False
        output = {"questions": [{"question": "Synthetic diagnostic " + str(i), "correct_answer": "A"} for i in range(7)]}
        return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
    monkeypatch.setattr("gallop.automation.service.DeepTutorAdapter",
                        lambda executable, home=None: DeepTutorAdapter(executable, home=home, runner=runner))
    def submit_controlled(self, job_id, **kwargs):
        directory = self.directory(job_id)
        request = json.loads((directory / 'request.json').read_text())
        run = directory / 'attempt-0001'
        run.mkdir()
        atomic_json(run / 'submitted.json', dict(at=0, deadline=240, attempt=1))
        practice = DeepTutorAdapter(executable, runner=runner).generate(request['manifest'])
        practice['practice_id'] = 'controlled-' + job_id
        atomic_json(run / 'completed.json', dict(job_id=job_id, manifest_id=request['manifest']['manifest_id'],
                    practice=practice, turn_id='controlled-turn', at=1))
        return dict(job_id=job_id, status='submitted')
    monkeypatch.setattr(Jobs, 'submit', submit_controlled)
    def command(*args):
        assert main(["--automation-config", str(config), *args]) == 0
        return json.loads(capsys.readouterr().out)
    sample = Path(__file__).parents[2] / "examples/automation/session.json"
    command("intake", str(sample))
    queue = command("queue")
    q = next(q for q in queue if q["status"] == "queued")
    submitted = command("prepare", q["queue_id"], "--send")
    assert submitted["status"] == "submitted"
    prepared = command("collect", submitted['job_id'])
    assert prepared["status"] == "completed"
    command("start", q["queue_id"], "--confirm")
    template = root / "prepared" / q["queue_id"] / "result-template.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    assert data["questions_correct"] is None and data["grader"] == "ungraded"
    data.update(result_id="synthetic-golden-result", outcome="fail", questions_attempted=7,
                questions_correct=5, hints_used=1, independent=False, transfer=False,
                grader="human", grading_reason="Explicit synthetic fixture; not real learner work",
                response_refs=["synthetic-proof-response"], started_at="2026-01-01T11:00:00Z",
                completed_at="2026-01-01T12:00:00Z", mistakes=["Synthetic quantifier error"])
    result = tmp_path / "result.json"
    result.write_text(json.dumps(data), encoding="utf-8")
    command("ingest-result", str(result), "--confirm-human")
    report = command("cycle")
    assert report["training_started"] is False
    assert report["publish"]["written"] > 2
    assert command("cycle")["publish"]["written"] == 0
    explanation = command("explain", q["concept"])
    assert explanation["mastery_level"] == 0 and explanation["mistake_count"] == 1
    assert explanation["evidence_refs"] and explanation["history"][-1]["reason"]
    assert command("rebuild-state")["replaced"]
    assert command("ingest-result", str(result), "--confirm-human")["duplicate"]
    assert command("status")["namespace"] == "integration_tests"
    assert untouched.read_bytes() == original
    app = Automation(AutomationConfig.load(config))
    try:
        assert {"session", "practice", "assessment", "state_transition"} <= {e["kind"] for e in app.store.events()}
        assert "Today's Training" in (app.config.reader / "Today.md").read_text(encoding="utf-8")
        assert not list(app.config.reader.rglob("*.json"))
    finally:
        app.close()


def test_cli_rejects_bad_cycle_without_claiming_success(tmp_path, capsys):
    root = tmp_path / "isolated"
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(dict(namespace="integration_tests", root=str(root),
        vault=str(root / "vault"), reader=str(root / "reader/Gallop-Reader"), export_state=str(root / "export"))))
    assert main(["--automation-config", str(cfg), "status"]) == 0
    capsys.readouterr()
    pending = root / "pending-intake"
    pending.mkdir()
    (pending / "bad.json").write_text('{"malformed":')
    assert main(["--automation-config", str(cfg), "cycle"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["rejected"] and report["publish"]["written"] == 0
    assert not (root / "reader/Gallop-Reader").exists()
