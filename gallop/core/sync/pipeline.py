"""Small orchestration boundary connecting practice, mastery, and knowledge."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol

from gallop.core.mastery import MasteryEngine
from gallop.core.models import PracticeResult
from gallop.core.sync.logging import SyncLogger
from gallop.core.validation import validate_protocol


class KnowledgeStore(Protocol):
    def read_mastery(self, manifest_id: str, *, namespace: str) -> int: ...
    def write_result(self, result: dict[str, Any], *, namespace: str) -> str: ...


class PracticeEngine(Protocol):
    def generate(self, manifest: dict[str, Any]) -> dict[str, Any]: ...


class GallopPipeline:
    def __init__(
        self,
        knowledge: KnowledgeStore,
        practice: PracticeEngine,
        *,
        logger: SyncLogger | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.practice = practice
        self.mastery = MasteryEngine()
        self.logger = logger

    def generate_practice(self, manifest: dict[str, Any]) -> dict[str, Any]:
        validate_protocol("practice-manifest.schema.json", manifest)
        try:
            generated = self.practice.generate(manifest)
        except Exception as exc:
            if self.logger:
                self.logger.write(
                    "practice_generate", subject=manifest.get("subject"),
                    manifest_id=manifest.get("manifest_id"), success=False,
                    error=type(exc).__name__,
                )
            raise
        if self.logger:
            self.logger.write(
                "practice_generate", subject=manifest["subject"],
                manifest_id=manifest["manifest_id"],
                practice_id=generated.get("practice_id"), success=True,
            )
        return generated

    def import_result(self, result: PracticeResult) -> dict[str, Any]:
        namespace = "integration_tests" if result.integration_test else "learner"
        try:
            stored_before = self.knowledge.read_mastery(result.manifest_id, namespace=namespace)
            before = stored_before if stored_before else result.mastery_before
            decision = self.mastery.evaluate(before, result.evidence())
            payload = {"schema_version": "1.0", **asdict(result)}
            payload.update(
                {
                    "questions_incorrect": result.questions_attempted - result.questions_correct,
                    "score": result.questions_correct / result.questions_attempted if result.questions_attempted else 0.0,
                    "mastery_before": decision.previous,
                    "mastery_after": decision.current,
                    "mastery_reason": decision.reason,
                }
            )
            validate_protocol("practice-result.schema.json", payload)
            payload["writeback_path"] = self.knowledge.write_result(payload, namespace=namespace)
        except Exception as exc:
            if self.logger:
                self.logger.write(
                    "result_import", subject=result.subject,
                    manifest_id=result.manifest_id, practice_id=result.practice_id,
                    success=False, error=type(exc).__name__,
                )
            raise
        if self.logger:
            self.logger.write(
                "result_import", subject=result.subject,
                target=payload["writeback_path"], manifest_id=result.manifest_id,
                practice_id=result.practice_id, success=True,
            )
        return payload
