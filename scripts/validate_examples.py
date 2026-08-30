"""Validate every bundled protocol example with its JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).parents[1]
PAIRS = [
    ("session.schema.json", "examples/mathematics/session.json"),
    ("practice-manifest.schema.json", "examples/mathematics/practice-manifest.json"),
    ("practice-result.schema.json", "examples/mathematics/practice-result.json"),
    ("mastery.schema.json", "examples/mathematics/mastery.json"),
]


def main() -> int:
    for schema_name, example_name in PAIRS:
        schema = json.loads((ROOT / "gallop" / "schemas" / schema_name).read_text(encoding="utf-8"))
        example = json.loads((ROOT / example_name).read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)
        print(f"PASS {example_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
