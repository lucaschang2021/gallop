"""Deterministic Markdown projections with preflight ownership checks."""
import html
import json
from pathlib import Path

from gallop.core.io import atomic_json, atomic_text
from gallop.mobile import check_path
from .protocol import digest
from .state import POLICIES

START = "<!-- gallop-automation:start -->"
END = "<!-- gallop-automation:end -->"


def text(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return html.escape(value, quote=False).replace("[", "&#91;").replace("]", "&#93;").replace("\n", " ")


def bullets(values, limit=5):
    return "\n".join("- " + text(v) for v in values[:limit]) or "- No recorded evidence yet."


def render(state, namespace):
    concepts = list(state["concepts"].values())
    active = sorted([q for q in state["queue"].values() if q["status"] in {"queued", "ready", "in_progress"}],
                    key=lambda q: (q["priority"], q["queue_id"]))
    sessions = sorted(state["sessions"].items(), key=lambda v: v[1]["occurred_at"], reverse=True)
    ideas = [idea for _, s in sessions for idea in s["research_ideas"]]
    questions = [q for item in concepts for q in item["open_questions"]]
    status = [f"{subject}: {sum(c['subject'] == subject for c in concepts)} concepts with evidence"
              for subject in POLICIES]
    title = "# Today\n\n"
    if namespace == "integration_tests":
        title += "> Synthetic demonstration in an isolated local preview. Not learner evidence.\n\n"
    today = title + "## Today's Training\n" + bullets([
        f"{q['priority']} · {q['subject']} · {q['concept']} · {q['training_type']} · {q['status']}" for q in active])
    today += "\n\n## Weakest Concepts\n" + bullets([
        f"{c['concept']} — level {c['mastery_level']}, confidence {c['confidence']}"
        for c in sorted(concepts, key=lambda c: (-c["mistake_count"], c["mastery_level"]))])
    today += "\n\n## Due Reviews\n" + bullets([q["concept"] for q in active if q["due_review"]])
    today += "\n\n## Recent Sessions\n" + bullets([s["title"] for _, s in sessions])
    today += "\n\n## Open Questions\n" + bullets(questions)
    today += "\n\n## Research Ideas\n" + bullets(ideas)
    today += "\n\n## Four Subjects\n" + bullets(status)
    today += "\n\n[[Gallop/Automation/Training Queue|Training Queue]] · [[Gallop/Automation/Weakness|Weakness]]\n"
    result = {"Gallop/Automation/Today.md": today, "Today.md": today}
    queue_body = "# Training Queue\n\n" + bullets([
        f"{q['queue_id']} · {q['subject']} · {q['concept']} · {q['training_type']} · "
        f"{q['priority']} · {q['status']} — {q['reason']} (evidence: {', '.join(q['evidence_refs'])})"
        for q in sorted(state["queue"].values(), key=lambda q: (q["priority"], q["queue_id"]))], 1000) + "\n"
    result["Gallop/Automation/Training Queue.md"] = queue_body
    result["Gallop/Automation/Weakness.md"] = "# Weakness Evidence\n\n" + bullets([
        f"{c['subject']} / {c['concept']}: {', '.join(c['weakness_tags'])}; "
        f"mistakes {c['mistake_count']}; evidence {', '.join(c['evidence_refs'])}" for c in concepts], 1000) + "\n"
    for subject, policy in POLICIES.items():
        body = "# " + subject + "\n\n" + bullets([
            f"{c['concept']}: level {c['mastery_level']}, confidence {c['confidence']}, "
            f"{c['evidence_count']} evidence records" for c in concepts if c["subject"] == subject], 1000)
        body += "\n\n[[Gallop/Automation/Today|Today]] · [[Gallop/Automation/Training Queue|Training Queue]]\n"
        result[policy["folder"] + "/Home.md"] = body
        result[f"Gallop/Automation/Subjects/{subject}/Home.md"] = body
    for eid, session in sessions:
        body = (
            "# " + text(session["title"]) + "\n\n" + text(session["summary"]) +
            "\n\nSource event: " + eid + "\n\nOccurred: " + text(session["occurred_at"]) + "\n")
        for field in ("concepts", "proofs_derivations", "hard_problem_sessions", "oral_exams",
                      "simulation_labs", "mistakes", "weakness_tags", "open_questions",
                      "connections", "research_ideas", "artifacts"):
            if session[field]:
                body += "\n## " + field.replace("_", " ").title() + "\n" + bullets(session[field], 1000) + "\n"
        result[f"Gallop/Automation/Sessions/{eid}.md"] = body
    for rid, record in state["results"].items():
        result[f"Gallop/Automation/Practice/{digest(rid)[:24]}.md"] = (
            "# Practice record\n\n" + text(record["concept"]) + "\n\n" +
            bullets([f"Outcome: {record['outcome']}", f"Queue: {record['queue_id']}",
                     f"Manifest: {record['manifest_id']}", f"Result: {rid}",
                     "Human grading: " + record["grading_reason"],
                     "Response references: " + ", ".join(record["response_refs"])]) + "\n")
    if ideas:
        result["Gallop/Automation/Research Ideas.md"] = "# Research Ideas\n\n" + bullets(ideas, 1000) + "\n"
    return result


def managed(body):
    if body.count(START) != 1 or body.count(END) != 1 or body.index(START) > body.index(END):
        raise ValueError("Malformed Gallop managed region")
    return body.split(START, 1)[1].split(END, 1)[0]


def project(config, state):
    receipt = check_path(config.root / "projection-receipt.json")
    previous = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {}
    rendered = render(state, config.namespace)
    plan, hashes = [], {}
    for name, body in sorted(rendered.items()):
        path = check_path(config.vault / name)
        desired = "\n" + body.rstrip() + "\n"
        original = path.read_text(encoding="utf-8") if path.exists() else ""
        if START in original or END in original:
            existing = managed(original)
            if name not in previous or digest(existing) != previous[name]:
                # Accept the desired content after a previous interrupted publish.
                if existing != desired:
                    raise ValueError("Managed projection was edited; user content preserved")
            output = original.split(START, 1)[0] + START + desired + END + original.split(END, 1)[1]
        elif name in previous:
            raise ValueError("Managed region was removed; refusing to overwrite")
        elif path.exists() and name.startswith("Gallop/Automation/"):
            raise ValueError("Unowned file occupies a Gallop view path")
        else:
            output = original + ("\n\n" if original else "") + START + desired + END + "\n"
        hashes[name] = digest(desired)
        plan.append((path, original, output))
    # No files changed until every ownership check passes. Each file write is atomic.
    for path, original, output in plan:
        if original != output:
            atomic_text(check_path(path), output)
    if previous != hashes:
        atomic_json(receipt, hashes)
    return {"views": len(plan), "written": sum(old != new for _, old, new in plan)}


def collect_views(source):
    """Read only owned Markdown projections, with the exporter's privacy filters."""
    from gallop.mobile import blocked_path, SENSITIVE, SYNTHETIC, PRIVATE, MAX_NOTE_BYTES, hidden_or_system
    root = check_path(source / "Gallop/Automation")
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*.md")):
        check_path(path)
        relative = path.relative_to(source)
        if blocked_path(relative) or hidden_or_system(path):
            continue
        info = path.stat()
        if info.st_nlink != 1 or info.st_size > MAX_NOTE_BYTES:
            continue
        body = path.read_text(encoding="utf-8")
        if START not in body or END not in body:
            continue
        payload = managed(body).strip() + "\n"
        if any(pattern.search(payload) for pattern in (SENSITIVE, SYNTHETIC, PRIVATE)) or "\x00" in payload:
            continue
        result[relative.as_posix()] = payload.encode("utf-8")
    return result
