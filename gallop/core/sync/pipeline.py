"""Validated, logged orchestration with recoverable inputs and replay protection."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
from typing import Any, Protocol

from gallop.core.io import atomic_json, contained, fingerprint, identifier
from gallop.core.mastery import MasteryEngine
from gallop.core.models import PracticeResult
from gallop.core.sync.logging import SyncLogger
from gallop.core.validation import validate_protocol


class KnowledgeStore(Protocol):
    def transaction(self): ...
    def read_topic(self, subject: str, topic: str, *, namespace: str) -> dict | None: ...
    def get_import(self, practice_id: str, *, namespace: str) -> dict | None: ...
    def write_result(self, result: dict, *, namespace: str, input_hash: str = "") -> str: ...


class PracticeEngine(Protocol):
    def generate(self, manifest: dict[str, Any]) -> dict[str, Any]: ...


class GallopPipeline:
    def __init__(self, knowledge: KnowledgeStore, practice: PracticeEngine,
                 *, logger: SyncLogger | None = None) -> None:
        self.knowledge = knowledge
        self.practice = practice
        self.mastery = MasteryEngine()
        self.logger = logger

    def _log(self, event: str, payload: dict, success: bool, error: str | None = None) -> None:
        if self.logger:
            self.logger.write(event, subject=payload.get("subject"),
                              manifest_id=payload.get("manifest_id"),
                              practice_id=payload.get("practice_id"),
                              success=success, error=error)

    def generate_practice(self, manifest: dict[str, Any]) -> dict[str, Any]:
        try:
            validate_protocol("practice-manifest.schema.json", manifest)
            generated = self.practice.generate(manifest)
        except Exception as exc:
            self._log("practice_generate", manifest, False, type(exc).__name__)
            raise
        self._log("practice_generate", {**manifest, **generated}, True)
        return generated

    def import_result(self, result: PracticeResult) -> dict[str, Any]:
        original = asdict(result)
        try:
            identifier(result.practice_id)
            identifier(result.manifest_id)
            evidence = result.evidence()
            # Validate input types/counts before reading or changing store state.
            self.mastery.evaluate(result.mastery_before, evidence)
            provisional = {"schema_version": "1.0", **original,
                           "questions_incorrect": result.questions_attempted - result.questions_correct,
                           "score": evidence.score, "mastery_after": result.mastery_before}
            validate_protocol("practice-result.schema.json", provisional)
            if (result.metadata.get("synthetic") or result.engine == "gallop-demo") and not result.integration_test:
                raise ValueError("Synthetic evidence requires integration_tests isolation")
            start = datetime.fromisoformat(result.started_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(result.completed_at.replace("Z", "+00:00"))
            if start > end:
                raise ValueError("Result ends before it starts")
            namespace = "integration_tests" if result.integration_test else "learner"
            digest = fingerprint(original)
            with self.knowledge.transaction():
                imported = self.knowledge.get_import(result.practice_id, namespace=namespace)
                if imported:
                    if imported["fingerprint"] != digest:
                        raise ValueError("Practice identifier already imported with different content")
                    payload = dict(imported["result"])
                    payload["writeback_path"] = str(contained(self.knowledge.vault, self.knowledge.vault / imported["path"]))
                    return payload
                topic = self.knowledge.read_topic(result.subject, result.topic, namespace=namespace)
                before = result.mastery_before if topic is None else topic["mastery_current"]
                prior = topic.get("evidence", []) if topic else []
                if prior and end <= datetime.fromisoformat(prior[-1]["completed_at"].replace("Z", "+00:00")):
                    raise ValueError("Out-of-order result rejected; preserve it for manual reconciliation")
                successful = [item for item in prior if item["independent"] and item["hints_used"] == 0
                              and item["score"] >= 0.8 and item["difficulty"] in {"medium", "hard", "research"}]
                # Repetitions come from distinct stored sessions, never a claimed count.
                decision = self.mastery.evaluate(before, replace(evidence, repeated_successes=len(successful)))
                payload = {**provisional, "mastery_before": decision.previous,
                           "mastery_after": decision.current, "mastery_reason": decision.reason}
                validate_protocol("practice-result.schema.json", payload)
                pending = contained(self.knowledge.vault, self.knowledge.vault / ".gallop" /
                                    "pending" / namespace / f"{result.practice_id}.json")
                atomic_json(pending, provisional)
                path = self.knowledge.write_result(payload, namespace=namespace, input_hash=digest)
                pending.unlink()
                payload["writeback_path"] = path
        except Exception as exc:
            self._log("result_import", original, False, type(exc).__name__)
            raise
        self._log("result_import", original, True)
        return payload
