"""Deterministic public demo adapter; it never calls an external model."""

from __future__ import annotations

from typing import Any


class DemoPracticeEngine:
    def generate(self, manifest: dict[str, Any]) -> dict[str, Any]:
        count = int(manifest.get("requested_question_count", 7))
        return {
            "practice_id": "practice-demo-epsilon-delta",
            "manifest_id": manifest["manifest_id"],
            "questions": [
                {
                    "question_id": f"q{index + 1}",
                    "prompt": f"Public synthetic continuity practice item {index + 1}",
                    "hint_gradient": ["direction", "key observation", "skeleton", "full solution"],
                }
                for index in range(count)
            ],
            "engine": "gallop-demo",
        }

