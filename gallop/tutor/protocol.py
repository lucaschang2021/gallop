"""Pure validation for the v1.2 bidirectional Tutor Protocol."""

from __future__ import annotations

from typing import Any

from gallop.core.validation import validate_protocol

PROTOCOL_VERSION = "1.2"

SUBJECT_TUTORS = {
    "mathematics": "mathematics-tutor",
    "statistics": "statistics-econometrics-tutor",
    "finance": "finance-tutor",
    "cs-ai": "cs-ai-tutor",
}

EVENT_TYPES = (
    "session_start",
    "context_request",
    "concept_exposed",
    "task_issued",
    "learner_attempt",
    "hint_given",
    "feedback_given",
    "candidate_assessment",
    "evidence_confirmation",
    "mistake_observed",
    "prerequisite_issue",
    "repair_attempt",
    "reconstruction_attempt",
    "independent_success",
    "oral_response",
    "proof_submission",
    "coding_submission",
    "simulation_result",
    "paper_activity",
    "checkpoint",
    "session_idle",
    "session_finalize",
)

DIRECTIVE_TYPES = (
    "learning_context",
    "training_zone",
    "scaffold_level",
    "target_capability",
    "prerequisite_focus",
    "task_type",
    "review_due",
    "retest_due",
    "independence_requirement",
    "assessment_boundary",
    "next_action",
    "unfinished_work",
)

DIRECTIVE_PAYLOAD_FIELDS = {
    "learning_context": "context_packet",
    "training_zone": "training_zone",
    "scaffold_level": "scaffold_level",
    "target_capability": "target_capability",
    "prerequisite_focus": "prerequisite_focus",
    "task_type": "task_type",
    "review_due": "due_at",
    "retest_due": "due_at",
    "independence_requirement": "independence_requirement",
    "assessment_boundary": "assessment_boundary",
    "next_action": "next_action",
    "unfinished_work": "unfinished_work",
}


def _validate_tutor(subject: str, tutor_id: str) -> None:
    if SUBJECT_TUTORS[subject] != tutor_id:
        raise ValueError("Tutor ID does not own the declared subject")


def validate_event(document: dict[str, Any]) -> dict[str, Any]:
    """Validate Tutor -> Gallop input without turning claims into authority."""

    validate_protocol("tutor-event-v1.2.schema.json", document)
    _validate_tutor(document["subject"], document["tutor_id"])
    payload = document["payload"]
    provenance = document["provenance"]

    if provenance["recorded_by"] != document["tutor_id"]:
        raise ValueError("Tutor event recorder does not match tutor ID")
    if provenance["actor"] == "tutor" and payload.get("authority_class") == "HUMAN_ATTESTATION":
        raise ValueError("Tutor output cannot assert human authority")
    if document["event_type"] in {"candidate_assessment", "independent_success"}:
        if payload.get("authority_class") != "CANDIDATE_EVIDENCE":
            raise ValueError("Tutor assessment must remain candidate evidence")
    if document["event_type"] == "evidence_confirmation":
        if provenance["actor"] != "human" or payload.get("authority_class") != "HUMAN_ATTESTATION":
            raise ValueError("Evidence confirmation requires explicit human authority")
    if payload.get("independence_class") == "INDEPENDENT":
        if payload.get("assistance_level", 0) != 0:
            raise ValueError("Assisted work cannot be independent")
        if payload.get("agent_usage") in {"HINT_ONLY", "AI_ASSISTED", "AI_GENERATED"}:
            raise ValueError("AI-assisted work cannot be independent")
    if (document["event_type"] == "coding_submission"
            and payload.get("agent_usage") == "AI_GENERATED"
            and payload.get("independence_class") == "INDEPENDENT"):
        raise ValueError("AI-generated code is not independent evidence")
    return document


def validate_directive(document: dict[str, Any]) -> dict[str, Any]:
    """Validate Gallop -> Tutor advisory output."""

    validate_protocol("tutor-directive-v1.2.schema.json", document)
    required = DIRECTIVE_PAYLOAD_FIELDS[document["directive_type"]]
    if required not in document["payload"]:
        raise ValueError(f"{document['directive_type']} directive requires {required}")
    if document["directive_type"] == "learning_context":
        packet = document["payload"]["context_packet"]
        validate_protocol("learning-context-v1.2.schema.json", packet)
        if (packet["subject"], packet["session_id"]) != (
            document["subject"], document["session_id"]
        ):
            raise ValueError("Learning context does not match its directive identity")
        if packet["source_event_ids"] != document["source_event_ids"]:
            raise ValueError("Learning context source events do not match its directive")
    return document
