"""Headless application boundary for custom-tool or MCP transport adapters."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from gallop.automation.config import AutomationConfig
from gallop.automation.protocol import canonical, synthetic, timestamp
from gallop.automation.service import Automation
from gallop.automation.store import JournalConflict

from .protocol import SUBJECT_TUTORS, validate_event


class TutorBridge:
    """Transport-neutral JSON operations over the authoritative journal."""

    def __init__(self, automation: Automation, *, owns_runtime: bool = False):
        self.automation = automation
        self._owns_runtime = owns_runtime

    @classmethod
    def open(cls, config: AutomationConfig) -> TutorBridge:
        return cls(Automation.open(config), owns_runtime=True)

    def close(self) -> None:
        if self._owns_runtime:
            self.automation.close()

    def __enter__(self) -> TutorBridge:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _sessions(self) -> dict[str, dict[str, Any]]:
        return self.automation.state().get("tutor", {}).get("sessions", {})

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self._sessions().get(session_id)
        if session is None:
            raise ValueError("Tutor session not found")
        return deepcopy(session)

    def open_or_resume_session(self, subject: str, session_id: str) -> dict[str, Any]:
        if subject not in SUBJECT_TUTORS:
            raise ValueError("Unknown tutor subject")
        existing = self._sessions().get(session_id)
        if existing is not None:
            if existing["subject"] != subject:
                raise JournalConflict("Session ID belongs to another subject")
            return {"created": False, "session": deepcopy(existing)}
        tutor_id = SUBJECT_TUTORS[subject]
        document = {
            "schema_version": "1.2",
            "event_id": f"{session_id}:start",
            "session_id": session_id,
            "tutor_id": tutor_id,
            "subject": subject,
            "event_type": "session_start",
            "occurred_at": self.automation.clock.now(),
            "payload": {"summary": "Session opened through Gallop runtime bridge."},
            "provenance": {
                "actor": "system",
                "recorded_by": tutor_id,
                "source": "gallop-runtime-bridge",
                "content_scope": "learning_relevant_only",
                "synthetic": self.automation.config.namespace == "integration_tests",
            },
        }
        result = self.record_learning_event(document)
        return {"created": True, **result, "session": self.get_session(session_id)}

    def record_learning_event(self, document: dict[str, Any]) -> dict[str, Any]:
        validate_event(document)
        if self.automation.config.namespace == "learner" and synthetic(document):
            raise ValueError("Synthetic tutor event cannot enter learner state")
        state = self.automation.state()
        tutor_state = state.get("tutor", {})
        session = tutor_state.get("sessions", {}).get(document["session_id"])
        known_event = document["event_id"] in tutor_state.get("events", {})
        if document["event_type"] != "session_start" and session is None:
            raise ValueError("Open the tutor session before recording learning events")
        if session is not None and (session["subject"], session["tutor_id"]) != (
            document["subject"], document["tutor_id"]
        ):
            raise JournalConflict("Tutor event does not match its session")
        if session is not None and not known_event:
            if document["event_type"] == "session_start":
                raise JournalConflict("Tutor session is already open")
            if session["status"] == "finalized":
                raise JournalConflict("Finalized tutor session cannot accept new events")
            if timestamp(document["occurred_at"]) < timestamp(session["last_event_at"]):
                raise JournalConflict("Tutor event chronology moved backwards")

        raw = canonical(document).encode("utf-8")

        def append() -> dict[str, Any]:
            raw_sha = self.automation.store.raw(raw)
            journal_id, added = self.automation.store.append(
                "tutor_event",
                document["event_id"],
                document,
                at=document["occurred_at"],
                source=f"tutor:{document['tutor_id']}",
                raw_sha=raw_sha,
            )
            return {
                "event_id": document["event_id"],
                "journal_event_id": journal_id,
                "duplicate": not added,
                "durable": True,
            }

        return self.automation.mutate(append)

    def checkpoint_session(self, document: dict[str, Any]) -> dict[str, Any]:
        if document.get("event_type") != "checkpoint":
            raise ValueError("checkpoint_session requires a checkpoint event")
        return self.record_learning_event(document)

    def finalize_session(self, document: dict[str, Any]) -> dict[str, Any]:
        if document.get("event_type") != "session_finalize":
            raise ValueError("finalize_session requires a session_finalize event")
        return self.record_learning_event(document)

    def dispatch(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
        operations: dict[str, Callable[..., dict[str, Any]]] = {
            "open_or_resume_session": self.open_or_resume_session,
            "record_learning_event": self.record_learning_event,
            "checkpoint_session": self.checkpoint_session,
            "finalize_session": self.finalize_session,
            "get_session": self.get_session,
        }
        handler = operations.get(operation)
        if handler is None:
            raise ValueError("Unknown Gallop tutor operation")
        return handler(**arguments)
