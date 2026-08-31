"""Runtime JSON Schema validation for Gallop protocol boundaries."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


class ProtocolValidationError(ValueError):
    pass


def validate_protocol(schema_name: str, document: dict[str, Any]) -> None:
    schema_file = files("gallop.schemas").joinpath(schema_name)
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    try:
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    except ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise ProtocolValidationError(f"{schema_name} validation failed at {path} ({exc.validator})") from exc
