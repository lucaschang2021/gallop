"""Verify the frozen V1 journal, state, projections, mastery, and queue exactly."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gallop.automation.protocol import canonical
from gallop.automation.state import replay
from gallop.automation.views import render


ROOT = Path(__file__).parents[1]


def identity(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def main() -> int:
    fixture = json.loads((ROOT / "tests/fixtures/v1-replay.json").read_text(encoding="utf-8"))
    expected = fixture["expected_state"]
    actual = replay(fixture["events"])
    expected_views = render(expected, "integration_tests")
    actual_views = render(actual, "integration_tests")
    mastery_drift = sorted(
        key for key in set(actual["concepts"]) | set(expected["concepts"])
        if actual["concepts"].get(key, {}).get("mastery_level")
        != expected["concepts"].get(key, {}).get("mastery_level")
    )
    queue_drift = sorted(
        key for key in set(actual["queue"]) | set(expected["queue"])
        if actual["queue"].get(key) != expected["queue"].get(key)
    )
    report = {
        "baseline_commit": fixture["baseline_commit"],
        "events": len(fixture["events"]),
        "state_exact": actual == expected,
        "state_sha256": identity(actual),
        "projection_exact": actual_views == expected_views,
        "projection_sha256": identity(actual_views),
        "mastery_drift": mastery_drift,
        "queue_drift": queue_drift,
    }
    print(json.dumps(report, indent=2))
    return 0 if (report["state_exact"] and report["projection_exact"]
                 and not mastery_drift and not queue_drift) else 1


if __name__ == "__main__":
    raise SystemExit(main())
