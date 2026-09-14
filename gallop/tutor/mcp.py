"""Headless STDIO MCP transport for one subject-bound Gallop Tutor."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
from typing import Any

from gallop.automation.config import AutomationConfig
from gallop.tutor.bridge import TutorBridge
from gallop.tutor.protocol import SUBJECT_TUTORS


SERVER_NAME = "gallop-zero-touch"
SERVER_VERSION = "1.2"
PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users)/)[^\s\"']+")
INSTRUCTIONS = (
    "Journal commit is authoritative and must precede projection. Use the bound subject only. "
    "Record meaningful checkpoints incrementally; reuse stable event IDs for exact retries. "
    "Tutor assessments remain candidate evidence. Never claim mastery or human confirmation. "
    "Only record evidence_confirmation after the learner explicitly confirms authorship. "
    "For CS/AI NO_AGENT_CODING, AI-generated code is never independent evidence."
)


def _event_schema(subject: str) -> dict[str, Any]:
    path = Path(__file__).parents[1] / "schemas" / "tutor-event-v1.2.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema.pop("$schema", None)
    schema.pop("$id", None)
    schema["properties"]["subject"] = {"const": subject}
    tutor_id = SUBJECT_TUTORS[subject]
    schema["properties"]["tutor_id"] = {"const": tutor_id}
    schema["properties"]["provenance"]["properties"]["recorded_by"] = {
        "const": tutor_id
    }
    return schema


def tool_catalog(subject: str) -> list[dict[str, Any]]:
    stable_id = {
        "type": "string",
        "minLength": 1,
        "maxLength": 128,
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    }
    document = _event_schema(subject)
    common = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
    return [
        {
            "name": "open_or_resume_session",
            "title": f"Open or resume {subject} Tutor session",
            "description": "Open a durable subject-bound session and restore journal-derived context.",
            "inputSchema": {
                "type": "object",
                "properties": {"session_id": stable_id},
                "required": ["session_id"],
                "additionalProperties": False,
            },
            "annotations": common,
        },
        {
            "name": "get_learning_context",
            "title": f"Get {subject} learning context",
            "description": "Read bounded advisory context reconstructed only from the Gallop journal.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": stable_id,
                    "max_items": {"type": "integer", "minimum": 1, "maximum": 100},
                    "max_chars": {"type": "integer", "minimum": 1000, "maximum": 50000},
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        },
        {
            "name": "record_learning_event",
            "title": f"Record {subject} learning event",
            "description": "Validate and append one real learning event, then refresh owned projections.",
            "inputSchema": {
                "type": "object",
                "properties": {"document": document},
                "required": ["document"],
                "additionalProperties": False,
            },
            "annotations": common,
        },
        {
            "name": "checkpoint_session",
            "title": f"Checkpoint {subject} Tutor session",
            "description": "Commit one meaningful checkpoint before more tutoring continues.",
            "inputSchema": {
                "type": "object",
                "properties": {"document": deepcopy(document)},
                "required": ["document"],
                "additionalProperties": False,
            },
            "annotations": common,
        },
        {
            "name": "finalize_session",
            "title": f"Finalize {subject} Tutor session",
            "description": "Record session finalization after all meaningful checkpoints are durable.",
            "inputSchema": {
                "type": "object",
                "properties": {"document": deepcopy(document)},
                "required": ["document"],
                "additionalProperties": False,
            },
            "annotations": common,
        },
        {
            "name": "get_session",
            "title": f"Get {subject} Tutor session",
            "description": "Read one durable session after validating its subject ownership.",
            "inputSchema": {
                "type": "object",
                "properties": {"session_id": stable_id},
                "required": ["session_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        },
    ]


def _bound_event(arguments: dict[str, Any], subject: str) -> dict[str, Any]:
    document = arguments.get("document")
    if not isinstance(document, dict):
        raise ValueError("document must be an object")
    tutor_id = SUBJECT_TUTORS[subject]
    if document.get("subject") != subject or document.get("tutor_id") != tutor_id:
        raise ValueError("Tutor event does not match the server's bound subject")
    provenance = document.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("recorded_by") != tutor_id:
        raise ValueError("Tutor event recorder does not match the server's bound subject")
    return document


def call_tool(config: AutomationConfig, subject: str, name: str,
              arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object")
    with TutorBridge.open(config) as bridge:
        if name == "open_or_resume_session":
            result = bridge.open_or_resume_session(subject, arguments["session_id"])
        elif name == "get_learning_context":
            result = bridge.get_learning_context(subject, **arguments)
        elif name == "get_session":
            result = bridge.get_session(arguments["session_id"])
            if result["subject"] != subject:
                raise ValueError("Session does not belong to the server's bound subject")
        elif name in {"record_learning_event", "checkpoint_session", "finalize_session"}:
            document = _bound_event(arguments, subject)
            result = bridge.dispatch(name, {"document": document})
        else:
            raise ValueError("Unknown Gallop Tutor tool")
    return {
        "structuredContent": result,
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}],
    }


def _error(exc: Exception) -> dict[str, Any]:
    message = PATH.sub("[private path]", str(exc))
    return {
        "isError": True,
        "structuredContent": {"error_type": type(exc).__name__, "message": message},
        "content": [{"type": "text", "text": f"{type(exc).__name__}: {message}"}],
    }


def handle(request: dict[str, Any], config: AutomationConfig,
           subject: str) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if request_id is None:
        return None
    response: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    try:
        if method == "initialize":
            protocol = request.get("params", {}).get("protocolVersion", "2025-06-18")
            response["result"] = {
                "protocolVersion": protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": INSTRUCTIONS,
            }
        elif method == "ping":
            response["result"] = {}
        elif method == "tools/list":
            response["result"] = {"tools": tool_catalog(subject)}
        elif method == "tools/call":
            params = request.get("params", {})
            response["result"] = call_tool(
                config, subject, params.get("name", ""), params.get("arguments", {})
            )
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}
    except Exception as exc:
        if method == "tools/call":
            response["result"] = _error(exc)
        else:
            response["error"] = {"code": -32602, "message": _error(exc)["content"][0]["text"]}
    return response


def serve(config: AutomationConfig, subject: str) -> int:
    for raw in sys.stdin:
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ValueError("JSON-RPC request must be an object")
            response = handle(request, config, subject)
        except (json.JSONDecodeError, ValueError) as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(exc)},
            }
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gallop v1.2 subject-bound STDIO MCP server")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--subject", required=True, choices=tuple(SUBJECT_TUTORS))
    args = parser.parse_args(argv)
    return serve(AutomationConfig.load(args.config), args.subject)


if __name__ == "__main__":
    raise SystemExit(main())
