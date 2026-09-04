"""Automation commands integrated with the existing Gallop parser."""
import argparse
import json
from pathlib import Path

from .config import AutomationConfig
from .service import Automation
from .protocol import parse
from gallop.mobile import check_path

COMMANDS = {"intake", "queue", "prepare", "start", "cancel", "retry", "ingest-result", "status",
            "publish", "cycle", "rebuild-state", "explain", "submit", "poll", "collect",
            "evidence", "benchmark", "readiness", "prerequisite", "target", "mentorship"}


def register(parser, commands):
    parser.add_argument("--automation-config", type=Path,
                        help="Private explicit configuration; never inferred from the legacy vault")
    for name in sorted(COMMANDS):
        sub = commands.add_parser(name, help="Automation V1: " + name)
        if name in {"intake", "ingest-result"}:
            sub.add_argument("input", type=Path)
        if name in {"prepare", "start", "cancel", "retry", "submit"}:
            sub.add_argument("queue_id")
        if name in {"poll", "collect"}:
            sub.add_argument("job_id")
        if name in {"submit", "prepare"}:
            sub.add_argument("--questions", type=int, default=7)
            sub.add_argument("--elite-policy", type=Path, help="Optional request metadata, never performance evidence")
        if name in {"evidence", "benchmark", "prerequisite", "target"}:
            actions = sub.add_subparsers(dest="action", required=True)
            add = actions.add_parser("add")
            add.add_argument("input", type=Path)
            add.add_argument("--confirm-human", action="store_true")
            show = actions.add_parser("show")
            show.add_argument("identity", nargs="?")
            show.add_argument("--subject", choices=["mathematics", "statistics", "finance", "cs-ai"])
        if name == 'mentorship':
            sub.add_argument('target_id', nargs='?')
        if name == "readiness":
            sub.add_argument("--subject", choices=["mathematics", "statistics", "finance", "cs-ai"])
            actions = sub.add_subparsers(dest="action")
            explain = actions.add_parser("explain")
            explain.add_argument("dimension")
            explain.add_argument("--subject", choices=["mathematics", "statistics", "finance", "cs-ai"],
                                 default=argparse.SUPPRESS)
        if name == "submit":
            sub.add_argument("--retry", action="store_true", help="Retry only a proven stopped, failed attempt")
        if name == "prepare":
            sub.add_argument("--send", action="store_true", help="Explicitly request DeepTutor diagnostic preparation")
        if name == "start":
            sub.add_argument("--confirm", action="store_true", help="The learner is actually starting this work")
        if name == "ingest-result":
            sub.add_argument("--confirm-human", action="store_true", help="Human verified actual performance and grading")
        if name == "publish":
            sub.add_argument("--dry-run", action="store_true")
        if name == "explain":
            sub.add_argument("concept")
            sub.add_argument("--subject", choices=["mathematics", "statistics", "finance", "cs-ai"])


def execute(args):
    if args.automation_config is None:
        raise ValueError("Provide --automation-config before the command")
    service = Automation(AutomationConfig.load(args.automation_config))
    try:
        elite = parse(check_path(args.elite_policy).read_bytes()) if getattr(args, "elite_policy", None) else None
        if args.command in {"evidence", "benchmark", "prerequisite", "target"}:
            kind = {"evidence": "elite_evidence", "benchmark": "benchmark", "prerequisite": "prerequisite_link",
                    "target":"target_capability"}[args.command]
            report = (service.add_record(kind, args.input, confirm_human=args.confirm_human) if args.action == "add"
                      else service.records(kind, args.identity, subject=args.subject))
        elif args.command == "readiness":
            report = service.readiness(subject=args.subject, dimension=getattr(args, "dimension", None))
        elif args.command == 'mentorship':
            report = service.mentorship(args.target_id)
        elif args.command == "intake":
            report = service.intake(args.input)
        elif args.command == "queue":
            report = service.refresh_queue()
        elif args.command == "prepare":
            prepared = service.prepare(args.queue_id, send=args.send, question_count=args.questions, elite=elite)
            report = prepared if args.send else {k: prepared[k] for k in ("queue_id", "manifest_id", "practice_id")}
            if not args.send:
                report["status"] = "ready"
        elif args.command == "submit":
            report = service.submit(args.queue_id, question_count=args.questions, retry=args.retry, elite=elite)
        elif args.command == "poll":
            report = service.poll(args.job_id)
            report.pop("completion", None)  # Instructor answers never go to console.
        elif args.command == "collect":
            report = service.collect(args.job_id)
        elif args.command == "start":
            report = service.start(args.queue_id, confirm=args.confirm)
        elif args.command == "cancel":
            report = service.cancel(args.queue_id)
        elif args.command == "retry":
            report = service.retry(args.queue_id)
        elif args.command == "ingest-result":
            report = service.ingest_result(args.input, confirm_human=args.confirm_human)
        elif args.command == "status":
            state = service.state()
            report = {"namespace": service.config.namespace, "events": state["seq"],
                      "concepts": len(state["concepts"]), "sessions": len(state["sessions"]),
                      "training": {s: sum(q["status"] == s for q in state["queue"].values())
                                   for s in ("queued", "ready", "in_progress", "completed", "failed", "cancelled")}}
        elif args.command == "cycle":
            report = service.cycle()
        elif args.command == "publish":
            report = service.publish(dry_run=args.dry_run)
        elif args.command == "rebuild-state":
            report = service.rebuild_state()
        elif args.command == "explain":
            report = service.explain(args.concept, subject=args.subject)
        if isinstance(report, dict):
            report.pop("completion", None)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if args.command == "cycle" and report["rejected"] else 0
    finally:
        service.close()
