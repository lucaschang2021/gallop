"""Environment-based machine configuration with no built-in local paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _optional_path(name: str) -> Path | None:
    value = os.getenv(name)
    return Path(value).expanduser() if value else None


@dataclass(frozen=True)
class GallopConfig:
    vault_path: Path | None
    deeptutor_path: Path | None
    state_path: Path | None
    log_path: Path | None
    model: str | None
    embedding_model: str | None

    @classmethod
    def from_environment(cls) -> "GallopConfig":
        return cls(
            vault_path=_optional_path("GALLOP_VAULT_PATH"),
            deeptutor_path=_optional_path("GALLOP_DEEPTUTOR_PATH"),
            state_path=_optional_path("GALLOP_STATE_PATH"),
            log_path=_optional_path("GALLOP_LOG_PATH"),
            model=os.getenv("GALLOP_MODEL"),
            embedding_model=os.getenv("GALLOP_EMBEDDING_MODEL"),
        )

