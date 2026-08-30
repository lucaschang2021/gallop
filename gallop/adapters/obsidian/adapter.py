"""Markdown knowledge-store adapter with isolated mastery namespaces."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "practice"


class ObsidianAdapter:
    def __init__(self, vault: Path, *, state_path: Path | None = None) -> None:
        self.vault = vault
        self.state_path = state_path or vault / ".gallop" / "mastery.json"

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"schema_version": "1.0", "topics": {}}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def read_mastery(self, manifest_id: str, *, namespace: str) -> int:
        return int(self._state().get("topics", {}).get(namespace, {}).get(manifest_id, {}).get("mastery_current", 0))

    def write_result(self, result: dict[str, Any], *, namespace: str) -> str:
        if namespace not in {"learner", "integration_tests"}:
            raise ValueError("unsupported mastery namespace")
        destination = self.vault / "Gallop" / "Practice" / namespace / (
            f"{_slug(result['topic'])}-{result['practice_id']}.md"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        warning = "\n> Integration test only; this is not learner evidence.\n" if namespace == "integration_tests" else ""
        markdown = (
            "---\n"
            "type: gallop-practice-result\n"
            f"practice_id: {result['practice_id']}\n"
            f"manifest_id: {result['manifest_id']}\n"
            f"subject: {result['subject']}\n"
            f"integration_test: {str(namespace == 'integration_tests').lower()}\n"
            "---\n\n"
            f"# Practice — {result['topic']}\n"
            f"{warning}\n"
            f"- Score: {result['questions_correct']}/{result['questions_attempted']}\n"
            f"- Hints used: {result['hints_used']}\n"
            f"- Mastery: {result['mastery_before']} → {result['mastery_after']}\n"
            f"- Reason: {result['mastery_reason']}\n"
        )
        destination.write_text(markdown, encoding="utf-8")

        state = self._state()
        topics = state.setdefault("topics", {}).setdefault(namespace, {})
        topics[result["manifest_id"]] = {
            "subject": result["subject"],
            "topic": result["topic"],
            "mastery_previous": result["mastery_before"],
            "mastery_current": result["mastery_after"],
            "last_practice": result["practice_id"],
            "updated_at": result["completed_at"],
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)
        return str(destination)

