"""Native STDIO MCP transport keeps every Tutor subject bound and durable."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from gallop.automation.config import AutomationConfig
from gallop.tutor.mcp import handle, tool_catalog
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


def test_catalog_is_subject_bound_and_safety_annotated():
    tools = tool_catalog("mathematics")
    assert [tool["name"] for tool in tools] == [
        "open_or_resume_session", "get_learning_context", "record_learning_event",
        "checkpoint_session", "finalize_session", "get_session",
    ]
    assert tools[1]["annotations"]["readOnlyHint"] is True
    assert tools[2]["inputSchema"]["properties"]["document"]["properties"]["subject"] == {
        "const": "mathematics"
    }


def test_bound_server_rejects_cross_subject_event(tmp_path):
    cfg = configuration(tmp_path)
    opened = handle(request("tools/call", {
        "name": "open_or_resume_session", "arguments": {"session_id": "session.math.mcp"}
    }), cfg, "mathematics")
    assert opened["result"]["structuredContent"]["created"] is True
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
    result = handle(request("tools/call", {
        "name": "checkpoint_session", "arguments": {"document": event}
    }), cfg, "mathematics")
    assert result["result"]["isError"] is True
    assert result["result"]["structuredContent"]["error_type"] == "ValueError"


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
        input=json.dumps(request("tools/call", {
            "name": "open_or_resume_session",
            "arguments": {"session_id": "session.statistics.restart"},
        })) + "\n",
        text=True, capture_output=True, check=True,
    )
    first_result = json.loads(first.stdout)["result"]["structuredContent"]
    assert first_result["created"] is True

    second = subprocess.run(
        command,
        input=json.dumps(request("tools/call", {
            "name": "open_or_resume_session",
            "arguments": {"session_id": "session.statistics.restart"},
        })) + "\n",
        text=True, capture_output=True, check=True,
    )
    second_result = json.loads(second.stdout)["result"]["structuredContent"]
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
    process.stdin.write(json.dumps(request("tools/call", {
        "name": "open_or_resume_session",
        "arguments": {"session_id": "session.finance.abrupt"},
    })) + "\n")
    process.stdin.flush()
    opened = json.loads(process.stdout.readline())["result"]["structuredContent"]
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
    calls = "\n".join(json.dumps(request("tools/call", {
        "name": "checkpoint_session", "arguments": {"document": checkpoint},
    }, request_id=index)) for index in (2, 3)) + "\n"
    retried = subprocess.run(command, input=calls, text=True, capture_output=True, check=True)
    results = [json.loads(line)["result"]["structuredContent"]
               for line in retried.stdout.splitlines()]
    assert results[0]["duplicate"] is False
    assert results[1]["duplicate"] is True
    assert results[1]["journal_event_id"] == results[0]["journal_event_id"]


def test_initialize_and_notification_framing_do_not_write(tmp_path):
    cfg = configuration(tmp_path)
    initialized = handle(request("initialize", {"protocolVersion": "2025-06-18"}), cfg, "cs-ai")
    assert initialized["result"]["protocolVersion"] == "2025-06-18"
    assert initialized["result"]["serverInfo"]["version"] == "1.2"
    assert handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, cfg, "cs-ai") is None
    assert not cfg.root.exists()
