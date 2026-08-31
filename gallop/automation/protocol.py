"""Compatible v1 intake and explicit human assessment envelopes."""
from datetime import datetime, timezone
import hashlib
import json
import re

from gallop.core.validation import validate_protocol

ARRAYS = ("concepts", "proofs_derivations", "hard_problem_sessions", "oral_exams",
          "simulation_labs", "mistakes", "weakness_tags", "open_questions",
          "connections", "research_ideas", "artifacts")
TUTORS = ("mathematics", "statistics", "finance", "cs-ai")
KINDS = ("practice", "hard_problem", "proof", "oral_exam", "simulation", "coding",
         "conceptual", "empirical", "review")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or not re.match(r"^\d{4}-\d{2}-\d{2}T", value):
        raise ValueError("Timestamp must include a timezone")
    return dt.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc).isoformat()


def parse(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("Input exceeds 5 MiB")
    text = raw.decode("utf-8-sig").strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        match = re.fullmatch(fence + r"json\s*\n(.*?)\n" + fence, text, re.S)
        if not match:
            raise ValueError("Exactly one JSON fenced block is required")
        text = match[1]
    def pairs(items):
        output = {}
        for key, value in items:
            if key in output:
                raise ValueError("Duplicate JSON key")
            output[key] = value
        return output
    value = json.loads(text, object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite number")))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def synthetic(value):
    if isinstance(value, dict):
        return any((k in {"synthetic", "integration_test"} and v is True)
                   or (k == "namespace" and v == "integration_tests")
                   or synthetic(v) for k, v in value.items())
    if isinstance(value, list):
        return any(synthetic(v) for v in value)
    return False


def normalize_session(document):
    validate_protocol("tutor-intake.schema.json", document)
    result = {"schema_version": "1.0", "course": "", **document}
    for field in ARRAYS:
        result.setdefault(field, [])
    result.setdefault("session_id", "session-" + digest(result)[:32])
    if not result["session_id"].strip():
        raise ValueError("Empty session id")
    timestamp(result["occurred_at"])
    if timestamp(result["occurred_at"]) > timestamp(now()):
        raise ValueError("Future session timestamp")
    if "subject" in result and result["subject"].casefold() not in {
        result["tutor"], {"mathematics": "mathematics", "statistics": "statistics / econometrics",
                         "finance": "finance", "cs-ai": "cs / ai"}[result["tutor"]]
    }:
        raise ValueError("Tutor and subject disagree")
    return result


def concept_names(session):
    names = []
    for value in session["concepts"]:
        name = value if isinstance(value, str) else value.get("name", "") if isinstance(value, dict) else ""
        name = name.strip() if isinstance(name, str) else ""
        if name and name not in names:
            names.append(name)
    return names


def validate_result(document):
    validate_protocol("automation-result.schema.json", document)
    start, end = timestamp(document["started_at"]), timestamp(document["completed_at"])
    if start > end or end > timestamp(now()):
        raise ValueError("Invalid result chronology")
    attempted, correct = document["questions_attempted"], document["questions_correct"]
    if correct > attempted or (document["outcome"] == "pass" and not attempted):
        raise ValueError("Invalid attempt counts")
    if document["outcome"] == "pass" and correct / attempted < 0.8:
        raise ValueError("Passing evidence requires at least 80 percent confirmed success")
    if document["outcome"] != "ungraded" and not document["response_refs"]:
        raise ValueError("Graded evidence requires learner response references")
    return document
