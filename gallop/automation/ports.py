"""Minimal application ports required by governance tests and explicit time."""
from datetime import date, datetime, timezone
from typing import Any, ContextManager, Protocol


class JournalStore(Protocol):
    def close(self) -> None: ...
    def transaction(self) -> ContextManager[None]: ...
    def raw(self, body: bytes) -> str: ...
    def append(self, kind: str, identity: Any, payload: Any, *, at: str,
               source: str, raw_sha: str | None = None) -> tuple[str, bool]: ...
    def events(self) -> list[dict]: ...


class Clock(Protocol):
    def now(self) -> str: ...
    def today(self) -> date: ...


class SystemClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def today(self) -> date:
        return date.today()
