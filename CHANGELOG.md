# Changelog

All notable changes follow Keep a Changelog and Semantic Versioning.

## [Unreleased]

## [1.2.0] - 2026-09-16

### Added

- Four subject-bound GPT Tutor STDIO MCP surfaces for Mathematics, Statistics,
  Finance, and CS/AI.
- Journal-derived context restoration for fresh chats and process restarts.
- Incremental checkpoints, exact duplicate-event recovery, and fail-closed
  Obsidian projection/recovery.
- Controlled real four-Tutor dogfood and PC → Vault → Gallop-Reader continuity
  evidence, while preserving conservative evidence and mastery authority.

### Changed

- Promoted package metadata from `1.2.0rc1` to stable `1.2.0`.
- DeepTutor remains optional legacy compatibility and is not a required v1.2
  runtime dependency.

### Verification

- Full CI matrix passed on Windows and Ubuntu with Python 3.11 and 3.13.
- Release tag: `v1.2.0`.

## [0.1.0] - 2026-08-31

### Added

- Session, practice manifest, practice result, and mastery protocols.
- Conservative native mastery engine with safety tests.
- Markdown/Obsidian knowledge-store adapter.
- External DeepTutor practice-engine adapter boundary.
- T+1/T+7/T+30 review compatibility.
- Synthetic seven-question mathematics demo and isolated writeback.
- Four optional subject profiles and open-source governance documentation.

### Known limitations

- Embedding-backed semantic retrieval is optional and not configured by Gallop.
- Real DeepTutor E2E requires a separately installed and authorized runtime.
- v0.1 uses a simple deterministic mastery policy rather than calibrated analytics.
