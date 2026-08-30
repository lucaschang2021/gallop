"""Compatibility schedule for knowledge-store-owned T+1/T+7/T+30 review."""

from __future__ import annotations

from datetime import date, timedelta


def review_dates(completed: date) -> dict[str, str]:
    return {
        "T+1": (completed + timedelta(days=1)).isoformat(),
        "T+7": (completed + timedelta(days=7)).isoformat(),
        "T+30": (completed + timedelta(days=30)).isoformat(),
    }

