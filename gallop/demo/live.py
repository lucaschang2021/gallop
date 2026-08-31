"""Opt-in synthetic DeepTutor transport acceptance; never learner evidence."""

import json
from importlib.resources import files
from pathlib import Path

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.io import atomic_json
from gallop.core.models import PracticeResult
from gallop.core.sync import GallopPipeline
from gallop.core.sync.logging import SyncLogger


def run_live_demo(output: Path, executable: Path, home: Path | None, *, send: bool = False) -> dict:
    output = output.resolve()
    manifest = json.loads(files("gallop.demo").joinpath("practice-manifest.json").read_text(encoding="utf-8"))
    practice_path = output / "practice.json"
    engine = DeepTutorAdapter(executable, home=home)
    pipeline = GallopPipeline(ObsidianAdapter(output / "vault"), engine,
                              logger=SyncLogger(output / "sync.jsonl"))
    if practice_path.exists():
        practice = json.loads(practice_path.read_text(encoding="utf-8"))
        if practice.get("manifest_id") != manifest["manifest_id"]:
            raise ValueError("Saved practice belongs to a different manifest")
    else:
        if not send:
            raise ValueError("First live run requires explicit --send")
        atomic_json(output / "manifest.json", manifest)
        practice = pipeline.generate_practice(manifest)
        atomic_json(output / "instructor-answer-key.json", practice.pop("answer_key", []))
        atomic_json(practice_path, practice)
    # A transport-only synthetic summary; no learner answered these questions.
    result = PracticeResult(
        practice_id=practice["practice_id"], manifest_id=manifest["manifest_id"],
        subject=manifest["subject"], topic=manifest["topic"],
        questions_attempted=7, questions_correct=5, hints_used=1, mastery_before=1,
        started_at="2026-01-01T11:45:00Z", completed_at="2026-01-01T12:00:00Z",
        engine="deeptutor", integration_test=True,
        metadata={"synthetic": True, "actor": "integration-test", "independent": False},
    )
    imported = pipeline.import_result(result)
    atomic_json(output / "result.json", {k: v for k, v in imported.items() if k != "writeback_path"})
    return {"questions": len(practice["questions"]), "correct": 5,
            "mastery_before": imported["mastery_before"], "mastery_after": imported["mastery_after"],
            "namespace": "integration_tests", "synthetic": True}
