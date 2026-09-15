"""Native STDIO MCP transport keeps every Tutor subject bound and durable."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import TextIO

from gallop.automation.config import AutomationConfig
from gallop.tutor.mcp import call_tool, runtime_status, tool_catalog
from gallop.tutor.protocol import SUBJECT_TUTORS


def configuration(tmp_path: Path) -> AutomationConfig:
    root = tmp_path / "runtime"
    return AutomationConfig.from_dict({
        "namespace": "integration_tests",
        "root": str(root),
        "vault": str(root / "vault"),
        "reader": str(root / "reader" / "Gallop-Reader"),
        "export_state": str(root / "export"),
    })


def request(method: str, params: dict | None = None, request_id: int = 1) -> dict:
    value = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        value["params"] = params
    return value


def initialized_input(*calls: dict) -> str:
    messages = [
        request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "gallop-test", "version": "1"},
        }, request_id=0),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        *calls,
    ]
    return "\n".join(json.dumps(message) for message in messages) + "\n"


def response_by_id(stdout: str, request_id: int) -> dict:
    responses = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    return next(response for response in responses if response.get("id") == request_id)


def read_response_by_id(stream: TextIO, request_id: int) -> dict:
    while True:
        line = stream.readline()
        if not line:
            raise AssertionError(f"MCP response id={request_id} was not emitted")
        response = json.loads(line)
        if response.get("id") == request_id:
            return response


def test_catalog_is_subject_bound_and_safety_annotated():
    tools = tool_catalog("mathematics")
    assert [tool["name"] for tool in tools] == [
        "get_runtime_status", "open_or_resume_session", "get_learning_context",
        "record_learning_event", "checkpoint_session", "finalize_session", "get_session",
    ]
    assert tools[0]["annotations"]["readOnlyHint"] is True
    assert tools[2]["annotations"]["readOnlyHint"] is True
    assert tools[3]["inputSchema"]["properties"]["document"]["properties"]["subject"] == {
        "const": "mathematics"
    }


def test_runtime_status_does_not_initialize_journal(tmp_path):
    cfg = configuration(tmp_path)
    status = runtime_status(cfg, "cs-ai")
    assert status == {
        "status": "PASS", "server": "gallop-zero-touch", "version": "1.2",
        "subject": "cs-ai", "tutor_id": "cs-ai-tutor",
        "namespace": "integration_tests", "runtime_initialized": False,
        "vault_ready": False, "reader_identity": "NOT_BOUND", "journal_opened": False,
    }
    assert not cfg.root.exists()


def test_bound_server_rejects_cross_subject_event(tmp_path):
    cfg = configuration(tmp_path)
    opened = call_tool(cfg, "mathematics", "open_or_resume_session", {
        "session_id": "session.math.mcp"
    })
    assert opened["structuredContent"]["created"] is True
    event = {
        "schema_version": "1.2",
        "event_id": "event.finance.cross-subject",
        "session_id": "session.math.mcp",
        "tutor_id": SUBJECT_TUTORS["finance"],
        "subject": "finance",
        "event_type": "checkpoint",
        "occurred_at": "2026-09-14T00:00:00Z",
        "payload": {"checkpoint_reason": "Cross-subject test."},
        "provenance": {
            "actor": "tutor", "recorded_by": SUBJECT_TUTORS["finance"],
            "source": "isolated-mcp-test", "content_scope": "learning_relevant_only",
            "synthetic": True,
        },
    }
    try:
        call_tool(cfg, "mathematics", "checkpoint_session", {"document": event})
    except ValueError as exc:
        assert "bound subject" in str(exc)
    else:
        raise AssertionError("Cross-subject event was accepted")


def test_stdio_restart_restores_session_without_chat_transcript(tmp_path):
    cfg = configuration(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "namespace": cfg.namespace,
        "root": str(cfg.root),
        "vault": str(cfg.vault),
        "reader": str(cfg.reader),
        "export_state": str(cfg.export_state),
    }), encoding="utf-8")
    command = [
        sys.executable, "-m", "gallop.tutor.mcp", "--config", str(config_path),
        "--subject", "statistics",
    ]
    first = subprocess.run(
        command,
        input=initialized_input(request("tools/call", {
            "name": "open_or_resume_session",
            "arguments": {"session_id": "session.statistics.restart"},
        })),
        text=True, capture_output=True, check=True,
    )
    first_result = response_by_id(first.stdout, 1)["result"]["structuredContent"]
    assert first_result["created"] is True

    second = subprocess.run(
        command,
        input=initialized_input(request("tools/call", {
            "name": "open_or_resume_session",
            "arguments": {"session_id": "session.statistics.restart"},
        })),
        text=True, capture_output=True, check=True,
    )
    second_result = response_by_id(second.stdout, 1)["result"]["structuredContent"]
    assert second_result["created"] is False
    assert second_result["context_restore"]["status"] == "PASS"


def test_stdio_abrupt_exit_and_duplicate_checkpoint_recover(tmp_path):
    cfg = configuration(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "namespace": cfg.namespace,
        "root": str(cfg.root),
        "vault": str(cfg.vault),
        "reader": str(cfg.reader),
        "export_state": str(cfg.export_state),
    }), encoding="utf-8")
    command = [
        sys.executable, "-m", "gallop.tutor.mcp", "--config", str(config_path),
        "--subject", "finance",
    ]
    process = subprocess.Popen(
        command, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(initialized_input(request("tools/call", {
        "name": "open_or_resume_session",
        "arguments": {"session_id": "session.finance.abrupt"},
    })))
    process.stdin.flush()
    opened = read_response_by_id(process.stdout, 1)["result"]["structuredContent"]
    process.kill()
    process.wait(timeout=10)

    checkpoint = {
        "schema_version": "1.2",
        "event_id": "event.finance.abrupt.checkpoint",
        "session_id": "session.finance.abrupt",
        "tutor_id": SUBJECT_TUTORS["finance"],
        "subject": "finance",
        "event_type": "checkpoint",
        "occurred_at": opened["session"]["last_event_at"],
        "payload": {"checkpoint_reason": "Durability retry after abrupt exit."},
        "provenance": {
            "actor": "tutor", "recorded_by": SUBJECT_TUTORS["finance"],
            "source": "isolated-mcp-test", "content_scope": "learning_relevant_only",
            "synthetic": True,
        },
    }
    checkpoint_call = request("tools/call", {
        "name": "checkpoint_session", "arguments": {"document": checkpoint},
    }, request_id=2)
    results = []
    for _ in range(2):
        retried = subprocess.run(
            command, input=initialized_input(checkpoint_call), text=True,
            capture_output=True, check=True,
        )
        response = response_by_id(retried.stdout, 2)
        assert "structuredContent" in response["result"], response
        results.append(response["result"]["structuredContent"])
    assert results[0]["duplicate"] is False
    assert results[1]["duplicate"] is True
    assert results[1]["journal_event_id"] == results[0]["journal_event_id"]


def test_initialize_and_notification_framing_do_not_write(tmp_path):
    cfg = configuration(tmp_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "namespace": cfg.namespace,
        "root": str(cfg.root),
        "vault": str(cfg.vault),
        "reader": str(cfg.reader),
        "export_state": str(cfg.export_state),
    }), encoding="utf-8")
    command = [
        sys.executable, "-m", "gallop.tutor.mcp", "--config", str(config_path),
        "--subject", "cs-ai",
    ]
    requests = initialized_input(request("tools/list", request_id=2))
    result = subprocess.run(command, input=requests, text=True, capture_output=True, check=True)
    initialize_response = response_by_id(result.stdout, 0)
    tools_response = response_by_id(result.stdout, 2)
    assert initialize_response["result"]["protocolVersion"] == "2025-06-18"
    assert initialize_response["result"]["serverInfo"]["version"] == "1.2"
    assert len(tools_response["result"]["tools"]) == 7
    assert not cfg.root.exists()
