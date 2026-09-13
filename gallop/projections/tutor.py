"""Deterministic, privacy-filtered Tutor session projections for Obsidian."""

from __future__ import annotations

import html
import json
import re
from typing import Any

from gallop.automation.protocol import digest
from gallop.mobile import SENSITIVE


SUBJECT_FOLDERS = {
    "mathematics": "01-Mathematics",
    "statistics": "02-Statistics-Econometrics",
    "finance": "03-Finance",
    "cs-ai": "04-CS-AI",
}
MACHINE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users)/)")


def safe(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if "\x00" in value or SENSITIVE.search(value) or MACHINE_PATH.search(value):
        return "[private reference omitted]"
    return html.escape(value, quote=False).replace("[", "&#91;").replace("]", "&#93;")


def lines(values: list[str]) -> str:
    return "\n".join(f"- {safe(value)}" for value in values) or "- None recorded."


def session_path(session: dict[str, Any]) -> str:
    day = session["opened_at"][:10]
    name = digest(session["session_id"])[:16]
    return f"{SUBJECT_FOLDERS[session['subject']]}/Sessions/{day}-tutor-{name}.md"


def concept_path(subject: str, concept_id: str) -> str:
    name = digest([subject, concept_id])[:16]
    return f"{SUBJECT_FOLDERS[subject]}/Concepts/tutor-{name}.md"


def mistake_path(document: dict[str, Any]) -> str:
    name = digest(document["event_id"])[:16]
    return f"{SUBJECT_FOLDERS[document['subject']]}/Mistakes/{document['occurred_at'][:10]}-{name}.md"


def render_session(session: dict[str, Any], events: list[dict[str, Any]], synthetic: bool) -> str:
    concepts = sorted({event["payload"]["concept_id"] for event in events
                       if event["payload"].get("concept_id")})
    tasks = [event for event in events if event["event_type"] == "task_issued"]
    attempts = [event for event in events if event["event_type"] in {
        "learner_attempt", "repair_attempt", "reconstruction_attempt", "oral_response",
        "proof_submission", "coding_submission", "simulation_result"}]
    hints = [event for event in events if event["event_type"] == "hint_given"]
    mistakes = [event for event in events if event["event_type"] == "mistake_observed"]
    evidence = [event for event in events if event["event_type"] in {
        "candidate_assessment", "independent_success"}]
    summaries = [event["payload"]["summary"] for event in events if event["payload"].get("summary")]
    unfinished = sorted({item for event in events
                         for item in event["payload"].get("unfinished_work", [])})
    next_actions = [event["payload"]["next_action"] for event in events
                    if event["payload"].get("next_action")]
    assistance = [
        f"{event['payload'].get('attempt_id', 'unknown')} · level "
        f"{event['payload']['assistance_level']}"
        for event in hints
    ]
    warning = "> Isolated synthetic projection; not learner evidence.\n\n" if synthetic else ""
    body = (
        f"# Tutor Session {safe(session['session_id'])}\n\n{warning}"
        f"- Subject: {safe(session['subject'])}\n"
        f"- Tutor: {safe(session['tutor_id'])}\n"
        f"- Status: {safe(session['status'])}\n"
        f"- Opened: {safe(session['opened_at'])}\n"
        f"- Last event: {safe(session['last_event_at'])}\n"
        f"- Durable checkpoints: {len(session['checkpoint_event_ids'])}\n\n"
        f"## Concise Summary\n\n{safe(summaries[-1]) if summaries else 'No summary recorded.'}\n\n"
        f"## Concepts\n\n{lines(concepts)}\n\n"
        f"## Tasks\n\n{lines([event['payload']['task_id'] for event in tasks])}\n\n"
        f"## Learner Attempts\n\n{lines([event['payload']['attempt_id'] for event in attempts])}\n\n"
        f"## Assistance\n\n{lines(assistance)}\n\n"
        f"## Mistakes\n\n{lines([event['event_id'] for event in mistakes])}\n\n"
        f"## Candidate Evidence\n\n{lines([event['event_id'] for event in evidence])}\n\n"
        f"## Unfinished Work\n\n{lines(unfinished)}\n\n"
        f"## Next Actions\n\n{lines(next_actions)}\n"
    )
    return body


def render_tutor(state: dict[str, Any], namespace: str) -> dict[str, str]:
    tutor = state.get("tutor", {"events": {}, "sessions": {}})
    output: dict[str, str] = {}
    for session in tutor["sessions"].values():
        events = [tutor["events"][event_id] for event_id in session["event_ids"]]
        output[session_path(session)] = render_session(
            session, events, namespace == "integration_tests"
        )
    concepts: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for document in tutor["events"].values():
        concept_id = document["payload"].get("concept_id")
        if concept_id:
            concepts.setdefault((document["subject"], concept_id), []).append(document)
        if document["event_type"] == "mistake_observed":
            payload = document["payload"]
            output[mistake_path(document)] = (
                f"# Mistake {safe(document['event_id'])}\n\n"
                f"- Subject: {safe(document['subject'])}\n"
                f"- Concept: {safe(payload.get('concept_id', 'NOT_RECORDED'))}\n"
                f"- Attempt: {safe(payload.get('attempt_id', 'NOT_RECORDED'))}\n"
                f"- Observed: {safe(document['occurred_at'])}\n\n"
                f"## Failure Taxonomy\n\n{lines(payload.get('failure_tags', []))}\n"
            )
    for (subject, concept_id), events in concepts.items():
        candidates = [event for event in events if event["event_type"] in {
            "candidate_assessment", "independent_success"}]
        output[concept_path(subject, concept_id)] = (
            f"# Concept {safe(concept_id)}\n\n"
            f"- Subject: {safe(subject)}\n"
            f"- Observations: {len(events)}\n"
            f"- Candidate evidence: {len(candidates)}\n\n"
            "Tutor candidate evidence is not mastery authority.\n\n"
            f"## Source Events\n\n{lines([event['event_id'] for event in events])}\n"
        )
    return output
