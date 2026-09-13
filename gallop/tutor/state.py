"""Derived tutor-session state; journal events remain authoritative."""

from copy import deepcopy

from gallop.automation.store import JournalConflict
from gallop.automation.protocol import timestamp


def apply_tutor_event(state: dict, event: dict) -> None:
    document = event["payload"]
    external_id = document["event_id"]
    session_id = document["session_id"]
    tutor = state.setdefault("tutor", {"events": {}, "sessions": {}})
    if external_id in tutor["events"]:
        raise JournalConflict("Duplicate external tutor event ID")

    sessions = tutor["sessions"]
    session = sessions.get(session_id)
    if session is None:
        if document["event_type"] != "session_start":
            raise JournalConflict("Tutor session must start before learning events")
        session = {
            "session_id": session_id,
            "subject": document["subject"],
            "tutor_id": document["tutor_id"],
            "status": "active",
            "opened_at": document["occurred_at"],
            "last_event_at": document["occurred_at"],
            "event_ids": [],
            "checkpoint_event_ids": [],
        }
        sessions[session_id] = session
    elif (session["subject"], session["tutor_id"]) != (
        document["subject"], document["tutor_id"]
    ):
        raise JournalConflict("Tutor session identity changed")
    elif session["status"] == "finalized":
        raise JournalConflict("Finalized tutor session contains later events")
    elif timestamp(document["occurred_at"]) < timestamp(session["last_event_at"]):
        raise JournalConflict("Tutor session chronology moved backwards")

    session["event_ids"].append(external_id)
    session["last_event_at"] = document["occurred_at"]
    if document["event_type"] == "checkpoint":
        session["checkpoint_event_ids"].append(external_id)
    elif document["event_type"] == "session_idle":
        session["status"] = "idle"
    elif document["event_type"] == "session_finalize":
        session["status"] = "finalized"
    elif document["event_type"] != "context_request":
        session["status"] = "active"
    tutor["events"][external_id] = deepcopy(document)
