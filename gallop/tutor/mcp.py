"""Headless STDIO MCP transport for one subject-bound Gallop Tutor."""

from __future__ import annotations

import argparse
import anyio
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

import mcp.types as mcp_types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from gallop.automation.config import AutomationConfig
from gallop.mobile_icloud import validate_target
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


def _document_input_schema(document: dict[str, Any]) -> dict[str, Any]:
    nested = deepcopy(document)
    definitions = nested.pop("$defs")
    return {
        "type": "object",
        "properties": {"document": nested},
        "required": ["document"],
        "additionalProperties": False,
        "$defs": definitions,
    }


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
            "name": "get_runtime_status",
            "title": f"Check {subject} Gallop runtime",
            "description": "Read configuration and bound Reader identity without opening the Journal.",
            "inputSchema": {"type": "object", "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        },
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
            "inputSchema": _document_input_schema(document),
            "annotations": common,
        },
        {
            "name": "checkpoint_session",
            "title": f"Checkpoint {subject} Tutor session",
            "description": "Commit one meaningful checkpoint before more tutoring continues.",
            "inputSchema": _document_input_schema(document),
            "annotations": common,
        },
        {
            "name": "finalize_session",
            "title": f"Finalize {subject} Tutor session",
            "description": "Record session finalization after all meaningful checkpoints are durable.",
            "inputSchema": _document_input_schema(document),
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


def runtime_status(config: AutomationConfig, subject: str) -> dict[str, Any]:
    config.validate()
    reader_identity = "NOT_BOUND"
    if config.binding is not None:
        validate_target(config.reader, config.binding)
        reader_identity = "PASS"
    return {
        "status": "PASS",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "subject": subject,
        "tutor_id": SUBJECT_TUTORS[subject],
        "namespace": config.namespace,
        "runtime_initialized": (config.root / "namespace.json").is_file(),
        "vault_ready": (config.vault / ".obsidian").is_dir(),
        "reader_identity": reader_identity,
        "journal_opened": False,
    }


def call_tool(config: AutomationConfig, subject: str, name: str,
              arguments: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object")
    if name == "get_runtime_status":
        if arguments:
            raise ValueError("Runtime status takes no arguments")
        result = runtime_status(config, subject)
        return {
            "structuredContent": result,
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}],
        }
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


def build_server(config: AutomationConfig, subject: str) -> Server:
    server = Server(SERVER_NAME, version=SERVER_VERSION, instructions=INSTRUCTIONS)

    @server.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        return [mcp_types.Tool(**item) for item in tool_catalog(subject)]

    @server.call_tool()
    async def dispatch(name: str, arguments: dict[str, Any]) -> mcp_types.CallToolResult:
        try:
            result = call_tool(config, subject, name, arguments)
        except Exception as exc:
            error = _error(exc)
            return mcp_types.CallToolResult(
                isError=True,
                structuredContent=error["structuredContent"],
                content=[mcp_types.TextContent(**error["content"][0])],
            )
        return mcp_types.CallToolResult(
            structuredContent=result["structuredContent"],
            content=[mcp_types.TextContent(**result["content"][0])],
        )

    return server


def serve(config: AutomationConfig, subject: str) -> int:
    server = build_server(config, subject)

    async def run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    anyio.run(run)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gallop v1.2 subject-bound STDIO MCP server")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--subject", required=True, choices=tuple(SUBJECT_TUTORS))
    args = parser.parse_args(argv)
    return serve(AutomationConfig.load(args.config), args.subject)


if __name__ == "__main__":
    raise SystemExit(main())
