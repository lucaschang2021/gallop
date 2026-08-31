"""Canonical Markdown store with a lock, atomic state and replay-safe imports."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from gallop.core.io import atomic_json, atomic_text, contained, fingerprint, identifier
from gallop.core.review import review_dates
from gallop.core.validation import validate_protocol


class ObsidianAdapter:
    def __init__(self, vault: Path, *, state_path: Path | None = None) -> None:
        self.vault = vault.resolve()
        self.state_path = contained(self.vault, state_path or self.vault / ".gallop" / "mastery.json")
        self.lock_path = self.state_path.with_suffix(".lock")
        self._locked = False

    @contextmanager
    def transaction(self):
        contained(self.vault, self.state_path)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        contained(self.vault, self.lock_path)
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RuntimeError("Knowledge store busy; after a crash inspect and remove the stale lock") from exc
        os.close(fd)
        self._locked = True
        try:
            yield
        finally:
            self._locked = False
            self.lock_path.unlink()

    def _state(self) -> dict[str, Any]:
        contained(self.vault, self.state_path)
        if not self.state_path.exists():
            return {"schema_version": "1.0", "topics": {}, "imports": {}}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    @staticmethod
    def topic_key(subject: str, topic: str) -> str:
        return fingerprint([subject, topic])

    def read_topic(self, subject: str, topic: str, *, namespace: str) -> dict[str, Any] | None:
        return self._state().get("topics", {}).get(namespace, {}).get(self.topic_key(subject, topic))

    def get_import(self, practice_id: str, *, namespace: str) -> dict[str, Any] | None:
        return self._state().get("imports", {}).get(namespace, {}).get(practice_id)

    def write_result(self, result: dict[str, Any], *, namespace: str,
                     input_hash: str = "") -> str:
        if namespace not in {"learner", "integration_tests"}:
            raise ValueError("unsupported mastery namespace")
        if bool(result.get("integration_test")) != (namespace == "integration_tests"):
            raise ValueError("Result namespace mismatch")
        if not self._locked:
            with self.transaction():
                return self.write_result(result, namespace=namespace, input_hash=input_hash)
        validate_protocol("practice-result.schema.json", result)
        pid = identifier(result["practice_id"])
        identifier(result["manifest_id"])
        destination = contained(self.vault, self.vault / "Gallop" / "Practice" / namespace / f"{pid}.md")
        state = self._state()
        input_hash = input_hash or fingerprint(result)
        imported = state.get("imports", {}).get(namespace, {}).get(pid)
        if imported:
            if imported["fingerprint"] != input_hash:
                raise ValueError("Practice identifier already imported with different content")
            return str(contained(self.vault, self.vault / imported["path"]))
        topic_key = self.topic_key(result["subject"], result["topic"])
        topics = state.setdefault("topics", {}).setdefault(namespace, {})
        previous = topics.get(topic_key, {})
        evidence = {"practice_id": pid, "completed_at": result["completed_at"],
                    "score": result["score"], "hints_used": result["hints_used"],
                    "independent": result["metadata"].get("independent") is True,
                    "difficulty": result["difficulty"]}
        history = previous.get("history", []) + [{
            "practice_id": pid, "previous": result["mastery_before"],
            "current": result["mastery_after"], "reason": result["mastery_reason"],
        }]
        current = {
            "schema_version": "1.0", "subject": result["subject"], "topic": result["topic"],
            "mastery_previous": result["mastery_before"], "mastery_current": result["mastery_after"],
            "evidence": previous.get("evidence", []) + [evidence], "last_practice": pid,
            "last_success": result["completed_at"] if result["score"] >= 0.6 else previous.get("last_success"),
            "last_failure": result["completed_at"] if result["score"] < 0.4 else previous.get("last_failure"),
            "hint_dependency": min(1.0, result["hints_used"] / max(1, result["questions_attempted"])),
            "delayed_recall": result["metadata"].get("delayed_recall"),
            "transfer_performance": (float(result["metadata"]["transfer_success"])
                                     if "transfer_success" in result["metadata"] else None),
            "confidence": None, "history": history,
        }
        validate_protocol("mastery.schema.json", current)
        topics[topic_key] = current
        state.setdefault("imports", {}).setdefault(namespace, {})[pid] = {
            "fingerprint": input_hash, "result": result, "path": str(destination.relative_to(self.vault)),
        }
        warning = "> Integration test only; this is not learner evidence.\n\n" if result["integration_test"] else ""
        frontmatter = "\n".join(f"{key}: {json.dumps(result[key], ensure_ascii=False)}"
                                for key in ("practice_id", "manifest_id", "subject", "integration_test"))
        dates = review_dates(datetime.fromisoformat(result["completed_at"].replace("Z", "+00:00")).date())
        note = ("---\ntype: gallop-practice-result\n" + frontmatter + "\n---\n\n"
                + "# Practice — " + result["topic"].replace("\n", " ") + "\n\n" + warning
                + f"- Score: {result['questions_correct']}/{result['questions_attempted']}\n"
                + f"- Hints used: {result['hints_used']}\n"
                + f"- Mastery: {result['mastery_before']} → {result['mastery_after']}\n"
                + f"- Reason: {result['mastery_reason']}\n\n"
                + "## Review queue\n\n"
                + "\n".join(f"- [ ] {label}: {day}" for label, day in dates.items()) + "\n\n"
                + "## Recorded observations\n\n"
                + json.dumps({k: result[k] for k in ("mistakes", "weakness_tags", "open_questions")},
                             ensure_ascii=False, indent=2) + "\n")
        # State is the commit point. If it fails, replay rewrites the same note.
        atomic_text(destination, note)
        atomic_json(self.state_path, state)
        return str(destination)

    def write_session(self, session: dict[str, Any]) -> str:
        validate_protocol("session.schema.json", session)
        sid = identifier(session["session_id"])
        destination = contained(self.vault, self.vault / "Gallop" / "Sessions" / f"{sid}.md")
        record = contained(self.vault, self.vault / ".gallop" / "sessions" / f"{sid}.json")
        with self.transaction():
            if record.exists() and json.loads(record.read_text(encoding="utf-8")) != session:
                raise ValueError("Session identifier already exists with different content")
            note = ("---\ntype: gallop-session\nsession_id: " + json.dumps(sid)
                    + "\n---\n\n# " + session["title"].replace("\n", " ") + "\n\n"
                    + session["summary"] + "\n\n"
                    + json.dumps(session, ensure_ascii=False, indent=2) + "\n")
            atomic_text(destination, note)
            atomic_json(record, session)
        return str(destination)
