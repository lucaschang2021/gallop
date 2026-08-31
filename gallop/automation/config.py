"""Explicit local configuration and namespace boundaries."""
from dataclasses import dataclass
import json
from pathlib import Path

from gallop.core.io import atomic_json
from gallop.mobile import check_path, overlap


@dataclass(frozen=True)
class AutomationConfig:
    root: Path
    vault: Path
    reader: Path
    export_state: Path
    namespace: str
    binding: Path | None = None
    deeptutor: Path | None = None
    deeptutor_home: Path | None = None

    @classmethod
    def load(cls, path):
        path = check_path(Path(path))
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key != "namespace" and value and isinstance(value, str):
                data[key] = str(path.parent / value) if not Path(value).is_absolute() else value
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data):
        if set(data) - set(cls.__dataclass_fields__):
            raise ValueError("Unknown automation setting")
        config = cls(**{k: check_path(Path(v)) if k != "namespace" and v else v
                        for k, v in data.items()})
        config.validate()
        return config

    def validate(self):
        if self.namespace not in {"learner", "integration_tests"}:
            raise ValueError("Explicit learner or integration_tests namespace required")
        for path in (self.root, self.vault, self.reader, self.export_state):
            check_path(path)
        if self.reader.name != "Gallop-Reader":
            raise ValueError("Only Gallop-Reader is supported")
        if any(overlap(a, b) for a, b in (
            (self.vault, self.reader), (self.vault, self.export_state),
            (self.reader, self.export_state),
        )):
            raise ValueError("Vault, Reader and export state must be separate")
        if self.namespace == "integration_tests" and not self.export_state.is_relative_to(self.root):
            raise ValueError("Export state must be inside the private automation root")
        if self.namespace == "integration_tests":
            if self.binding or any(not p.is_relative_to(self.root) or p == self.root
                                   for p in (self.vault, self.reader)):
                raise ValueError("Integration vault/Reader must be isolated inside its root, without cloud binding")
            if any("icloud" in str(p).lower() for p in (self.root, self.reader)):
                raise ValueError("Integration data cannot enter iCloud")
        elif any(overlap(self.root, p) for p in (self.vault, self.reader)):
            raise ValueError("Learner event root must be outside the vault and Reader")
        if any(part.lower() in {"icloud", "iclouddrive", "onedrive", "dropbox"}
               for part in (*self.root.parts, *self.export_state.parts)):
            raise ValueError("Event store must remain outside cloud storage")
        if self.namespace == "learner" and not (self.vault / ".obsidian").is_dir():
            raise ValueError("Learner mode requires an existing Obsidian vault")

    def bind(self):
        self.validate()
        self.root.mkdir(parents=True, exist_ok=True)
        marker = check_path(self.root / "namespace.json")
        expected = {"namespace": self.namespace, "vault": str(self.vault),
                    "reader": str(self.reader), "export_state": str(self.export_state),
                    "binding": str(self.binding) if self.binding else None}
        if marker.exists():
            if json.loads(marker.read_text(encoding="utf-8")) != expected:
                raise ValueError("Existing automation root belongs to another namespace or target")
        else:
            if any(self.root.iterdir()):
                raise ValueError("Initial automation root must be empty")
            atomic_json(marker, expected)
        if self.namespace == "integration_tests":
            (self.vault / ".obsidian").mkdir(parents=True, exist_ok=True)
