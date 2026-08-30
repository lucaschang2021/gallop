"""Command-line entry points for the public, synthetic Gallop demo."""

from __future__ import annotations

import argparse
import json
from importlib.resources import files
from pathlib import Path

from gallop.adapters.mock import DemoPracticeEngine
from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.models import PracticeResult
from gallop.core.sync import GallopPipeline


def run_demo(output: Path) -> dict[str, object]:
    manifest = json.loads(files("gallop.demo").joinpath("practice-manifest.json").read_text(encoding="utf-8"))
    pipeline = GallopPipeline(ObsidianAdapter(output), DemoPracticeEngine())
    practice = pipeline.generate_practice(manifest)
    result = PracticeResult(
        practice_id=practice["practice_id"],
        manifest_id=manifest["manifest_id"],
        subject=manifest["subject"],
        topic=manifest["topic"],
        questions_attempted=7,
        questions_correct=5,
        hints_used=1,
        mastery_before=1,
        difficulty="medium",
        mistakes=["synthetic quantifier-order mistake"],
        weakness_tags=["quantifier-order"],
        started_at="2026-01-01T11:45:00Z",
        completed_at="2026-01-01T12:00:00Z",
        engine="gallop-demo",
        integration_test=True,
    )
    imported = pipeline.import_result(result)
    return {
        "practice_id": practice["practice_id"],
        "questions": len(practice["questions"]),
        "score": "5/7",
        "mastery": f"{imported['mastery_before']} -> {imported['mastery_after']}",
        "namespace": "integration_tests",
        "writeback": imported["writeback_path"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gallop")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run the synthetic local E2E demo")
    demo.add_argument("--output", type=Path, default=Path("demo-output"))
    args = parser.parse_args(argv)
    if args.command == "demo":
        print(json.dumps(run_demo(args.output.resolve()), indent=2))
        return 0
    return 2
