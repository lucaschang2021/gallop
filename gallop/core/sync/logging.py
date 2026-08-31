"""Privacy-minimal JSONL sync evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gallop.core.io import fingerprint


class SyncLogger:
    FIELDS = (
        "timestamp", "event", "subject", "source", "target", "manifest_id",
        "practice_id", "success", "error",
    )

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, event: str, **values: Any) -> None:
        record = {field: values.get(field) for field in self.FIELDS}
        record["timestamp"] = datetime.now(UTC).isoformat()
        record["event"] = event
        record["success"] = bool(values.get("success", False))
        for field in ("subject", "source", "target", "manifest_id", "practice_id"):
            if record[field] is not None:
                record[field] = fingerprint(record[field])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
