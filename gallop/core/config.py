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
    deeptutor_home: Path | None

    @classmethod
    def from_environment(cls) -> "GallopConfig":
        return cls(
            vault_path=_optional_path("GALLOP_VAULT_PATH"),
            deeptutor_path=_optional_path("GALLOP_DEEPTUTOR_PATH"),
            state_path=_optional_path("GALLOP_STATE_PATH"),
            log_path=_optional_path("GALLOP_LOG_PATH"),
            deeptutor_home=_optional_path("GALLOP_DEEPTUTOR_HOME"),
        )


def load_env(path: Path) -> None:
    """Read literal KEY=value configuration; never execute shell expressions."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.startswith("GALLOP_"):
            raise ValueError("Environment file must use GALLOP_KEY=value lines")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
