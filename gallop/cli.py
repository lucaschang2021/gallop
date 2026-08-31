"""Command-line entry points for the public, synthetic Gallop demo."""

from __future__ import annotations

import argparse
import json
from importlib.resources import files
from pathlib import Path

from dataclasses import fields
import sys

from gallop.adapters.deeptutor import DeepTutorAdapter
from gallop.core.config import GallopConfig, load_env
from gallop.core.io import atomic_json
from gallop.core.sync.logging import SyncLogger
from gallop.core.sync.session import build_manifest
from gallop.core.validation import validate_protocol


from gallop.adapters.mock import DemoPracticeEngine
from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.models import PracticeResult
from gallop.core.sync import GallopPipeline


def run_demo(output: Path) -> dict[str, object]:
    manifest = json.loads(files("gallop.demo").joinpath("practice-manifest.json").read_text(encoding="utf-8"))
    pipeline = GallopPipeline(ObsidianAdapter(output), DemoPracticeEngine(),
                              logger=SyncLogger(output / ".gallop" / "sync.jsonl"))
    practice = pipeline.generate_practice(manifest)
    atomic_json(output / "manifest.json", manifest)
    atomic_json(output / "practice.json", practice)
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
    atomic_json(output / "result.json", {k: v for k, v in imported.items() if k != "writeback_path"})
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
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="offline synthetic E2E, never learner evidence")
    demo.add_argument("--output", type=Path, default=Path("demo-output"))
    live = commands.add_parser("live-demo", help="explicit opt-in synthetic DeepTutor acceptance")
    live.add_argument("--output", type=Path, required=True)
    live.add_argument("--deeptutor", type=Path)
    live.add_argument("--home", type=Path)
    live.add_argument("--send", action="store_true", help="send synthetic manifest to configured provider")
    for command in ("sync-session", "manifest", "generate", "import-result"):
        sub = commands.add_parser(command)
        sub.add_argument("input", type=Path)
        sub.add_argument("--vault", type=Path)
        if command in {"manifest", "generate"}:
            sub.add_argument("--output", type=Path, required=True)
        if command == "manifest":
            sub.add_argument("--questions", type=int, default=7)
        if command == "generate":
            sub.add_argument("--deeptutor", type=Path)
            sub.add_argument("--home", type=Path)
    args = parser.parse_args(argv)
    try:
        load_env(args.env_file)
        config = GallopConfig.from_environment()
        if args.command == "demo":
            print(json.dumps(run_demo(args.output.resolve()), indent=2))
            return 0
        if args.command == "live-demo":
            from gallop.demo.live import run_live_demo
            executable = args.deeptutor or config.deeptutor_path
            if executable is None:
                raise ValueError("Configure the DeepTutor executable")
            print(json.dumps(run_live_demo(args.output, executable,
                             args.home or config.deeptutor_home, send=args.send), indent=2))
            return 0
        document = json.loads(args.input.read_text(encoding="utf-8"))
        vault = args.vault or config.vault_path
        store = ObsidianAdapter(vault, state_path=config.state_path) if vault else None
        log = SyncLogger(config.log_path or (vault / ".gallop" / "sync.jsonl")) if vault else None
        if args.command == "manifest":
            atomic_json(args.output, build_manifest(document, count=args.questions))
        elif args.command == "sync-session":
            if store is None:
                raise ValueError("Configure GALLOP_VAULT_PATH or --vault")
            store.write_session(document)
        elif args.command == "generate":
            executable = args.deeptutor or config.deeptutor_path
            if executable is None:
                raise ValueError("Configure GALLOP_DEEPTUTOR_PATH or --deeptutor")
            engine = DeepTutorAdapter(executable, home=args.home or config.deeptutor_home)
            # Input file remains the durable recovery source on transport failure.
            practice = GallopPipeline(store, engine, logger=log).generate_practice(document)
            answers = practice.pop("answer_key", [])
            atomic_json(args.output.with_suffix(".answer-key.json"), answers)
            atomic_json(args.output, practice)
        elif args.command == "import-result":
            if store is None:
                raise ValueError("Configure GALLOP_VAULT_PATH or --vault")
            validate_protocol("practice-result.schema.json", document)
            names = {field.name for field in fields(PracticeResult)}
            result = PracticeResult(**{key: value for key, value in document.items() if key in names})
            report = GallopPipeline(store, DemoPracticeEngine(), logger=log).import_result(result)
            print(json.dumps({"practice_id": report["practice_id"],
                              "mastery_before": report["mastery_before"],
                              "mastery_after": report["mastery_after"]}))
        return 0
    except Exception as exc:
        # Do not print provider errors, arbitrary input bodies, or filesystem paths.
        print(f"Gallop failed: {type(exc).__name__}. Input retained; check configuration and local diagnostics.",
              file=sys.stderr)
        return 1
