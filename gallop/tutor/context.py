"""Deterministic bounded context packets for fresh Tutor conversations."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from gallop.automation.protocol import canonical, timestamp
from gallop.core.validation import validate_protocol
from gallop.progression.evidence import capability_state
from gallop.tutor.protocol import SUBJECT_TUTORS


LIST_FIELDS = (
    "active_prerequisites",
    "recent_evidence",
    "recent_failures",
    "recent_gains",
    "reviews_due",
    "retests_due",
    "unfinished_tasks",
    "source_event_ids",
)
SENSITIVE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bBearer\s+\S+|"
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b|"
    r"[\"']?(?:api[ _-]?key|access[ _-]?token|refresh[ _-]?token|client[ _-]?secret|"
    r"password|passwd|authorization|private[ _-]?key|oauth[ _-]?token|api[ _-]?token)"
    r"[\"']?\s*[:=]\s*\S+|[a-z]+://[^\s/@:]+:[^\s/@]+@",
    re.I,
)
MACHINE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users)/)")


def clip(value: Any, limit: int = 500) -> str:
    text = str(value).strip()
    if "\x00" in text or SENSITIVE.search(text) or MACHINE_PATH.search(text):
        return "[private reference omitted]"
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _subject_sessions(state: dict[str, Any], subject: str) -> list[dict[str, Any]]:
    return sorted(
        (session for session in state.get("tutor", {}).get("sessions", {}).values()
         if session["subject"] == subject),
        key=lambda session: (timestamp(session["last_event_at"]), session["session_id"]),
        reverse=True,
    )


def _subject_events(state: dict[str, Any], subject: str) -> list[dict[str, Any]]:
    return sorted(
        (event for event in state.get("tutor", {}).get("events", {}).values()
         if event["subject"] == subject),
        key=lambda event: (timestamp(event["occurred_at"]), event["event_id"]),
        reverse=True,
    )


def build_context(
    state: dict[str, Any],
    subject: str,
    session_id: str,
    *,
    max_items: int = 10,
    max_chars: int = 12000,
) -> dict[str, Any]:
    if subject not in SUBJECT_TUTORS:
        raise ValueError("Unknown tutor subject")
    if not 1 <= max_items <= 50 or not 2000 <= max_chars <= 20000:
        raise ValueError("Context bounds are outside the governed range")
    sessions = _subject_sessions(state, subject)
    if not any(session["session_id"] == session_id for session in sessions):
        raise ValueError("Context session does not exist for this subject")
    events = _subject_events(state, subject)
    active_concept = next(
        (event["payload"].get("concept_id") for event in events
         if event["payload"].get("concept_id")),
        None,
    )
    elite = state.get("elite", {})
    evidence_entries = [
        entry for entry in elite.get("evidence", {}).values()
        if entry["record"]["subject"] == subject
        and (active_concept is None or entry["record"]["concept"] == active_concept)
    ]
    evidence_entries.sort(
        key=lambda entry: (timestamp(entry["record"]["occurred_at"]), entry["event_id"]),
        reverse=True,
    )
    current_state, _, _, _, _ = capability_state(evidence_entries)
    concept = next(
        (item for item in state["concepts"].values()
         if item["subject"] == subject and item["concept"] == active_concept),
        None,
    )
    targets = [entry for entry in elite.get("targets", {}).values()
               if entry["record"]["subject"] == subject]
    targets.sort(
        key=lambda entry: (
            timestamp(entry["record"]["created_at"]),
            entry["record"]["target_id"],
        ),
        reverse=True,
    )
    target_entry = targets[0] if targets else None
    target = target_entry["record"] if target_entry else None
    plan = None
    if target_entry is not None:
        from gallop.mentorship import plan as mentorship_plan

        plan = mentorship_plan(state, target_entry)
    prerequisites = [] if plan is None else [
        {
            "concept_id": clip(item.get("target_concept", "NOT_RECORDED"), 128),
            "certainty": clip(item.get("certainty", "NOT_RECORDED"), 64),
            "action": clip(item.get("curriculum_action", "NONE")),
        }
        for item in plan["prerequisite_gaps"] if item.get("certainty") != "CLOSED"
    ]
    recent_evidence = [
        {
            "evidence_id": entry["record"]["evidence_id"],
            "concept_id": entry["record"]["concept"],
            "result": entry["record"]["result"],
            "confirmed": entry["confirmed"],
            "independence_class": entry["record"].get("independence_class", "NOT_RECORDED"),
            "occurred_at": entry["record"]["occurred_at"],
        }
        for entry in evidence_entries
    ]
    failures = [
        {
            "event_id": event["event_id"],
            "concept_id": event["payload"].get("concept_id"),
            "failure_tags": list(event["payload"].get("failure_tags", [])),
            "occurred_at": event["occurred_at"],
        }
        for event in events if event["event_type"] == "mistake_observed"
    ]
    queues = [item for item in state["queue"].values() if item["subject"] == subject]
    reviews = [
        {"queue_id": item["queue_id"], "concept_id": clip(item["concept"], 128),
         "priority": item["priority"]}
        for item in queues if item.get("due_review")
    ]
    retests = [
        {"queue_id": item["queue_id"], "concept_id": clip(item["concept"], 128),
         "priority": item["priority"]}
        for item in queues if item.get("training_type") == "retest"
    ]
    unfinished = [clip(item) for event in events
                  for item in event["payload"].get("unfinished_work", [])]
    summaries = [clip(event["payload"]["summary"]) for event in events
                 if event["event_type"] != "session_start"
                 and event["payload"].get("summary")]
    next_actions = [clip(event["payload"]["next_action"]) for event in events
                    if event["payload"].get("next_action")]
    if plan is not None:
        next_action = plan["progression_action"]
    elif next_actions:
        next_action = next_actions[0]
    elif queues:
        next_action = f"{queues[0]['training_type']}:{queues[0]['concept']}"
    else:
        next_action = "CONTINUE_TEACHING_WITHOUT_UNSUPPORTED_STATE_CLAIMS"
    packet: dict[str, Any] = {
        "schema_version": "1.2",
        "subject": subject,
        "session_id": session_id,
        "active_concept_id": active_concept,
        "current_capability": {
            "state": current_state,
            "source": "journal_evidence" if evidence_entries else "not_recorded",
            "mastery_level": concept["mastery_level"] if concept else None,
            "confidence": concept["confidence"] if concept else None,
        },
        "target_capability": ({
            "target_id": clip(target["target_id"], 128),
            "dimension": clip(target["dimension"]),
            "target_state": target["target_state"],
            "description": clip(target["description"]),
        } if target else None),
        "active_prerequisites": prerequisites,
        "scaffold_level": plan["scaffolding_level"] if plan else None,
        "training_zone": plan["training_zone"] if plan else None,
        "recent_evidence": recent_evidence,
        "recent_failures": failures,
        "recent_gains": ([] if plan is None else [
            {"from": gain["before"], "to": gain["after"],
             "source_event_ids": list(gain["evidence_refs"])}
            for gain in plan["capability_gains"]
        ]),
        "reviews_due": reviews,
        "retests_due": retests,
        "unfinished_tasks": unfinished,
        "previous_relevant_summary": summaries[0] if summaries else None,
        "next_recommended_action": clip(next_action),
        "source_event_ids": [event["event_id"] for event in events],
        "truncation": {"applied": False, "omitted_items": 0,
                       "max_items": max_items, "max_chars": max_chars},
    }
    omitted = 0
    for field in LIST_FIELDS:
        omitted += max(0, len(packet[field]) - max_items)
        packet[field] = packet[field][:max_items]
    while len(canonical(packet)) > max_chars:
        candidates = [field for field in LIST_FIELDS if packet[field]]
        if not candidates:
            raise ValueError("Context packet cannot fit the governed character bound")
        field = max(candidates, key=lambda name: (len(packet[name]), name))
        packet[field].pop()
        omitted += 1
    packet["truncation"]["applied"] = omitted > 0
    packet["truncation"]["omitted_items"] = omitted
    validate_protocol("learning-context-v1.2.schema.json", packet)
    return deepcopy(packet)
