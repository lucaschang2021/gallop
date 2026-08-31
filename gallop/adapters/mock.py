"""Deterministic public demo adapter; it never calls an external model."""

from __future__ import annotations

from typing import Any


class DemoPracticeEngine:
    def generate(self, manifest: dict[str, Any]) -> dict[str, Any]:
        count = int(manifest.get("requested_question_count", 7))
        prompts = [
            "State the quantifier order in continuity at a fixed point a.",
            "Negate the epsilon-delta definition of continuity at a.",
            "For f(x)=2x at a=1, propose delta in terms of epsilon.",
            "Why may delta depend on a in pointwise continuity?",
            "Explain the role of 0 < |x-a| in a limit definition.",
            "Give a function whose limit at a exists but differs from f(a).",
            "Which dependency is forbidden when continuity becomes uniform?",
        ]
        if count != 7:
            raise ValueError("The bundled synthetic demo contains exactly seven questions")
        return {
            "practice_id": "practice-demo-epsilon-delta",
            "manifest_id": manifest["manifest_id"],
            "questions": [
                {
                    "question_id": f"q{index + 1}",
                    "prompt": prompts[index],
                    "hint_gradient": ["direction", "key observation", "skeleton", "full solution"],
                }
                for index in range(count)
            ],
            "engine": "gallop-demo",
        }
