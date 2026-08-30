import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).parents[2]
SCHEMAS = ROOT / "gallop" / "schemas"


def validate(schema_name: str, document: dict) -> None:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)


def test_public_session_matches_schema():
    document = json.loads((ROOT / "examples" / "mathematics" / "session.json").read_text(encoding="utf-8"))
    validate("session.schema.json", document)


def test_public_manifest_matches_schema():
    document = json.loads((ROOT / "examples" / "mathematics" / "practice-manifest.json").read_text(encoding="utf-8"))
    validate("practice-manifest.schema.json", document)


def test_public_result_matches_schema():
    document = json.loads((ROOT / "examples" / "mathematics" / "practice-result.json").read_text(encoding="utf-8"))
    validate("practice-result.schema.json", document)


def test_public_mastery_matches_schema():
    document = json.loads((ROOT / "examples" / "mathematics" / "mastery.json").read_text(encoding="utf-8"))
    validate("mastery.schema.json", document)


def test_session_requires_empty_arrays_instead_of_omission():
    document = json.loads((ROOT / "examples" / "mathematics" / "session.json").read_text(encoding="utf-8"))
    del document["oral_exams"]
    schema = json.loads((SCHEMAS / "session.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(document))
    assert errors
