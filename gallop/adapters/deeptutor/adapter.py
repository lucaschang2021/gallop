"""Subprocess adapter; DeepTutor itself is never vendored into Gallop."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any


class DeepTutorUnavailable(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess[str]]


class DeepTutorAdapter:
    def __init__(self, executable: Path, *, runner: Runner = subprocess.run) -> None:
        self.executable = executable
        self.runner = runner

    def generate(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if not self.executable.is_file():
            raise DeepTutorUnavailable(f"DeepTutor executable unavailable: {self.executable}")
        prompt = (
            "Generate structured deliberate practice from this Gallop manifest. "
            "Respect no_agent and hint_gradient settings.\n" + json.dumps(manifest, ensure_ascii=False)
        )
        completed = self.runner(
            [str(self.executable), "run", "deep_question", "--prompt", prompt, "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode:
            raise DeepTutorUnavailable(f"DeepTutor exited {completed.returncode}: {completed.stderr[-500:]}")
        payload = self._extract(completed.stdout)
        if not payload.get("questions"):
            raise ValueError("DeepTutor returned no usable questions")
        return payload

    @staticmethod
    def _extract(output: str) -> dict[str, Any]:
        for line in reversed(output.splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            candidates = [event, event.get("payload"), event.get("result"), event.get("data")]
            metadata = event.get("metadata") or event.get("metadata_json")
            if isinstance(metadata, str):
                try:
                    candidates.append(json.loads(metadata))
                except json.JSONDecodeError:
                    pass
            elif isinstance(metadata, dict):
                candidates.append(metadata)
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                summary = candidate.get("summary", candidate)
                if isinstance(summary, dict) and isinstance(summary.get("questions"), list):
                    return summary
                results = summary.get("results") if isinstance(summary, dict) else None
                if isinstance(results, list):
                    return {"questions": results, "metadata": summary}
        raise ValueError("DeepTutor output did not contain a structured result")

