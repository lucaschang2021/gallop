from copy import deepcopy

import pytest

from gallop.core.validation import ProtocolValidationError
from gallop.tutor import (
    DIRECTIVE_TYPES,
    EVENT_TYPES,
    SUBJECT_TUTORS,
    validate_directive,
    validate_event,
)
from gallop.tutor.protocol import DIRECTIVE_PAYLOAD_FIELDS


def event(event_type: str = "checkpoint", subject: str = "mathematics") -> dict:
    return {
        "schema_version": "1.2",
        "event_id": f"event.{subject}.{event_type}.001",
        "session_id": f"session.{subject}.001",
        "tutor_id": SUBJECT_TUTORS[subject],
        "subject": subject,
        "event_type": event_type,
        "occurred_at": "2026-09-13T10:00:00Z",
        "payload": {
            "concept_id": "concept.synthetic",
            "target_concept_id": "concept.target",
            "prerequisite_concept_id": "concept.prerequisite",
            "capability_id": "capability.synthetic",
            "task_id": "task.synthetic.001",
            "attempt_id": "attempt.synthetic.001",
            "task_type": "PROOF",
            "prompt_reference": "prompt://synthetic/001",
            "learner_response_reference": "response://synthetic/001",
            "assistance_level": 0,
            "independence_class": "INDEPENDENT",
            "agent_usage": "NONE",
            "correctness": "CORRECT",
            "reasoning_quality": "SOLID",
            "failure_tags": ["synthetic_failure"],
            "evaluator_confidence": "MEDIUM",
            "authority_class": "CANDIDATE_EVIDENCE",
            "evidence_refs": ["attempt.synthetic.001"],
            "summary": "Synthetic protocol event.",
            "checkpoint_reason": "Synthetic durable boundary.",
        },
        "provenance": {
            "actor": "tutor",
            "recorded_by": SUBJECT_TUTORS[subject],
            "source": "unit-test",
            "content_scope": "learning_relevant_only",
            "synthetic": True,
        },
    }


def directive(directive_type: str = "learning_context") -> dict:
    payload = {
        "current_capability": "UNKNOWN",
        "target_capability": "GUIDED",
        "training_zone": "FOUNDATION",
        "scaffold_level": "S5",
        "prerequisite_focus": [],
        "task_type": "PROOF",
        "due_at": "2026-09-20T10:00:00Z",
        "independence_requirement": "ANY",
        "assessment_boundary": "CANDIDATE_ONLY",
        "next_action": "Continue the synthetic task.",
        "unfinished_work": [],
    }
    return {
        "schema_version": "1.2",
        "directive_id": f"directive.{directive_type}.001",
        "session_id": "session.mathematics.001",
        "subject": "mathematics",
        "directive_type": directive_type,
        "issued_at": "2026-09-13T10:00:01Z",
        "authority": "ADVISORY",
        "source_event_ids": ["event.mathematics.checkpoint.001"],
        "payload": payload,
    }


@pytest.mark.parametrize("event_type", EVENT_TYPES)
def test_every_tutor_event_type_has_a_valid_versioned_envelope(event_type):
    assert validate_event(event(event_type))["event_type"] == event_type


@pytest.mark.parametrize("subject", SUBJECT_TUTORS)
def test_one_protocol_serves_all_four_subjects(subject):
    assert validate_event(event(subject=subject))["tutor_id"] == SUBJECT_TUTORS[subject]


@pytest.mark.parametrize("directive_type", DIRECTIVE_TYPES)
def test_every_directive_type_has_a_required_payload(directive_type):
    document = directive(directive_type)
    assert validate_directive(document)["authority"] == "ADVISORY"
    del document["payload"][DIRECTIVE_PAYLOAD_FIELDS[directive_type]]
    with pytest.raises(ValueError):
        validate_directive(document)


def test_tutor_and_subject_cannot_cross():
    document = event(subject="finance")
    document["tutor_id"] = "mathematics-tutor"
    document["provenance"]["recorded_by"] = "mathematics-tutor"
    with pytest.raises(ValueError, match="does not own"):
        validate_event(document)


def test_tutor_claim_cannot_be_mastery_or_human_authority():
    document = event("candidate_assessment")
    document["payload"]["authority_class"] = "MASTERED"
    with pytest.raises(ProtocolValidationError):
        validate_event(document)
    document = event("checkpoint")
    document["payload"]["authority_class"] = "HUMAN_ATTESTATION"
    with pytest.raises(ValueError, match="human authority"):
        validate_event(document)


def test_ai_generated_code_cannot_be_independent_evidence():
    document = event("coding_submission", "cs-ai")
    document["payload"]["agent_usage"] = "AI_GENERATED"
    with pytest.raises(ValueError, match="cannot be independent"):
        validate_event(document)


def test_assistance_downgrades_independence_at_protocol_boundary():
    document = event("proof_submission")
    document["payload"]["assistance_level"] = 1
    with pytest.raises(ValueError, match="Assisted work"):
        validate_event(document)


def test_ids_are_stable_bounded_tokens_and_unknown_fields_fail_closed():
    document = event()
    document["event_id"] = "contains spaces"
    with pytest.raises(ProtocolValidationError):
        validate_event(document)
    document = event()
    document["payload"]["private_chat_dump"] = "not learning-scoped"
    with pytest.raises(ProtocolValidationError):
        validate_event(document)


def test_directives_are_advisory_and_do_not_mutate_inputs():
    document = directive()
    before = deepcopy(document)
    assert validate_directive(document) is document
    assert document == before
    document["authority"] = "AUTHORITATIVE"
    with pytest.raises(ProtocolValidationError):
        validate_directive(document)
