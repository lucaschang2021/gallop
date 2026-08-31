"""Conservative evidence-based mastery transitions."""

from __future__ import annotations

from dataclasses import dataclass

from gallop.core.models import MasteryEvidence


MASTERY_LABELS = {
    0: "unseen",
    1: "exposed",
    2: "basic understanding",
    3: "guided application",
    4: "independent application",
    5: "robust mastery",
}


@dataclass(frozen=True)
class MasteryDecision:
    previous: int
    current: int
    reason: str


class MasteryEngine:
    """Update mastery without treating one quiz as durable understanding."""

    def evaluate(self, current: int, evidence: MasteryEvidence) -> MasteryDecision:
        if type(current) is not int or current not in MASTERY_LABELS:
            raise ValueError("mastery must be between 0 and 5")
        if any(type(v) is not int or v < 0 for v in
               (evidence.attempted, evidence.correct, evidence.hints_used, evidence.repeated_successes)):
            raise ValueError("attempt counts cannot be negative")
        if evidence.correct > evidence.attempted:
            raise ValueError("correct cannot exceed attempted")
        if evidence.attempted == 0:
            return MasteryDecision(current, current, "no evidence")

        score = evidence.score
        if score < 0.4:
            return MasteryDecision(current, max(0, current - 1), "weak performance")
        if score < 0.6:
            return MasteryDecision(current, current, "mixed performance")

        if score >= 0.8 and evidence.independent and evidence.hints_used == 0:
            ceiling = 4 if evidence.difficulty in {"medium", "hard", "research"} else 2
            proposed = max(current, min(ceiling, current + 1))
            reason = "strong independent performance"
        else:
            proposed = max(current, min(3, max(current, 2)))
            reason = "guided successful performance"

        robust = all(
            (
                score >= 0.8,
                evidence.independent,
                evidence.hints_used == 0,
                evidence.delayed_recall,
                evidence.transfer_success,
                evidence.oral_explanation,
                evidence.repeated_successes >= 2,
                evidence.difficulty in {"medium", "hard", "research"},
            )
        )
        if current >= 4 and robust:
            return MasteryDecision(current, 5, "durable transfer evidence")
        return MasteryDecision(current, proposed, reason)
