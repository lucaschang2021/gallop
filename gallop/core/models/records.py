"""Typed records shared by adapters and the mastery engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MasteryEvidence:
    correct: int
    attempted: int
    hints_used: int = 0
    independent: bool = False
    delayed_recall: bool = False
    transfer_success: bool = False
    oral_explanation: bool = False
    difficulty: str = "medium"
    repeated_successes: int = 0

    @property
    def score(self) -> float:
        return self.correct / self.attempted if self.attempted else 0.0


@dataclass(frozen=True)
class PracticeResult:
    practice_id: str
    manifest_id: str
    subject: str
    topic: str
    questions_attempted: int
    questions_correct: int
    hints_used: int
    mastery_before: int
    difficulty: str = "medium"
    mistakes: list[Any] = field(default_factory=list)
    weakness_tags: list[str] = field(default_factory=list)
    open_questions: list[Any] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    engine: str = "unknown"
    integration_test: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def evidence(self) -> MasteryEvidence:
        return MasteryEvidence(
            correct=self.questions_correct,
            attempted=self.questions_attempted,
            hints_used=self.hints_used,
            independent=bool(self.metadata.get("independent", self.hints_used == 0)),
            delayed_recall=bool(self.metadata.get("delayed_recall", False)),
            transfer_success=bool(self.metadata.get("transfer_success", False)),
            oral_explanation=bool(self.metadata.get("oral_explanation", False)),
            repeated_successes=int(self.metadata.get("repeated_successes", 0)),
            difficulty=self.difficulty,
        )

