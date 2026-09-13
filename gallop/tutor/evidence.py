"""Map admitted tutor assessments into the existing evidence architecture."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from gallop.automation.elite_protocol import failure_registry, validate as validate_elite


RESULTS = {
    "CORRECT": "PASS",
    "PARTIAL": "PARTIAL",
    "INCORRECT": "FAIL",
    "UNASSESSED": "NOT_RECORDED",
}


def candidate_record(document: dict[str, Any], *, namespace: str) -> dict[str, Any] | None:
    """Reuse Elite Evidence 1.1; never manufacture a confirmed parallel model."""

    if document["event_type"] not in {"candidate_assessment", "independent_success"}:
        return None
    payload = document["payload"]
    record: dict[str, Any] = {
        "schema_version": "1.1",
        "namespace": namespace,
        "integration_test": namespace == "integration_tests",
        "evidence_id": f"tutor:{document['event_id']}",
        "subject": document["subject"],
        "concept": payload["concept_id"],
        "task_type": payload["task_type"],
        "occurred_at": document["occurred_at"],
        "source": f"tutor:{document['tutor_id']}",
        "result": RESULTS[payload["correctness"]],
        "assessment_context": "FORMATIVE",
        "evidence_refs": list(payload["evidence_refs"]),
        "metadata": {
            "context_id": document["session_id"],
            "attempt_id": payload["attempt_id"],
            "task_id": payload["task_id"],
            "capability_id": payload["capability_id"],
            "tutor_event_id": document["event_id"],
            "evaluator_confidence": payload["evaluator_confidence"],
            "reasoning_quality": payload.get("reasoning_quality", "UNKNOWN"),
            "authority_class": "CANDIDATE_EVIDENCE",
        },
    }
    for source, target in (
        ("independence_class", "independence_class"),
        ("assistance_level", "hint_level"),
        ("agent_usage", "agent_usage"),
        ("failure_tags", "failure_modes"),
    ):
        if source in payload and payload[source] != "UNKNOWN":
            record[target] = payload[source]
    for quality in ("proof_quality", "derivation_quality"):
        if quality in payload:
            record[quality] = deepcopy(payload[quality])
    validate_elite(
        "elite_evidence",
        record,
        namespace=namespace,
        registry=failure_registry(),
    )
    return record


def confirmation_record(
    document: dict[str, Any], state: dict[str, Any], *, namespace: str
) -> dict[str, Any] | None:
    """Create a distinct confirmed attestation for an existing Tutor candidate."""

    if document["event_type"] != "evidence_confirmation":
        return None
    candidate_event_id = document["payload"]["candidate_event_id"]
    candidate_event = state.get("tutor", {}).get("events", {}).get(candidate_event_id)
    if candidate_event is None or candidate_event["event_type"] not in {
        "candidate_assessment", "independent_success"
    }:
        raise ValueError("Human confirmation must reference an existing Tutor candidate")
    if candidate_event["subject"] != document["subject"]:
        raise ValueError("Human confirmation cannot cross subjects")
    candidate_id = f"tutor:{candidate_event_id}"
    candidate = state.get("elite", {}).get("evidence", {}).get(candidate_id)
    if candidate is None or candidate["confirmed"]:
        raise ValueError("Human confirmation requires one unconfirmed Tutor candidate")
    evidence_id = f"human:{document['event_id']}"
    prior_confirmations = [
        entry for entry in state.get("elite", {}).get("evidence", {}).values()
        if entry["record"].get("metadata", {}).get("candidate_event_id")
        == candidate_event_id
    ]
    if any(entry["record"]["evidence_id"] != evidence_id for entry in prior_confirmations):
        raise ValueError("Tutor candidate already has a human confirmation")
    record = deepcopy(candidate["record"])
    record["evidence_id"] = evidence_id
    record["source"] = "human:tutor-dialogue"
    record["metadata"] = {
        **record.get("metadata", {}),
        "authority_class": "HUMAN_ATTESTATION",
        "candidate_event_id": candidate_event_id,
        "confirmation_event_id": document["event_id"],
    }
    validate_elite(
        "elite_evidence", record, namespace=namespace, registry=failure_registry()
    )
    return record
