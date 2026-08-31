"""Truthful session-to-manifest conversion without inventing learner outcomes."""

from gallop.core.io import identifier
from gallop.core.validation import validate_protocol


def build_manifest(session: dict, *, count: int = 7, difficulty: str = "medium",
                   no_agent: bool = True) -> dict:
    validate_protocol("session.schema.json", session)
    sid = identifier(session["session_id"])
    manifest = {
        "schema_version": "1.0", "manifest_id": identifier("m-" + sid),
        "session_id": sid, "subject": session["subject"], "course": session["course"],
        "topic": session["title"], "concepts": session["concepts"],
        "weakness_tags": session["weakness_tags"], "mistakes": session["mistakes"],
        "open_questions": session["open_questions"], "difficulty": difficulty,
        "practice_priority": 3, "source_notes": [f"Gallop/Sessions/{sid}.md"],
        "requested_question_count": count, "practice_modes": ["diagnostic-quiz"],
        "no_agent": no_agent,
        "hint_gradient": ["independent_attempt", "direction_only", "key_observation",
                          "skeleton", "full_solution"],
        "created_at": session["occurred_at"],
    }
    validate_protocol("practice-manifest.schema.json", manifest)
    return manifest
