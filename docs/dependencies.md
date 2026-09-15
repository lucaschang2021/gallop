# Dependency and license boundary

Gallop's own code is Apache-2.0. Third-party packages and external services retain their own licenses and terms.

## Direct runtime dependencies

The v1.2 package declares:

| Package | Role | Boundary |
|---|---|---|
| `jsonschema>=4.20,<5` | Versioned validation for Tutor, evidence, Automation, and policy contracts | Validation only; schemas do not become runtime authority |
| `mcp>=1.30,<2` | Local STDIO MCP transport for the four subject-bound GPT Tutor servers | No model call is performed by Gallop's MCP server itself |

Transitive packages are resolved by those dependencies and remain subject to their own licenses. The source tree does not vendor their code.

## Development dependencies

`pytest`, `ruff`, and `mypy` are development/CI dependencies. CI also uses standard GitHub Actions for checkout and Python setup. Development tooling does not become a learner runtime authority.

## DeepTutor

DeepTutor is **legacy, optional, external, and non-authoritative** in v1.2. Gallop does not redistribute DeepTutor source, models, credentials, assets, or private runtime state. Its adapter is retained for compatible Automation V1 diagnostic generation and is not required by the four-Tutor Zero-Touch workflow.

DeepTutor/model-provider terms, account eligibility, model outputs, rate limits, and service availability are outside Gallop's license and control.

## Obsidian and Gallop-Reader

Gallop writes Markdown projections that can be opened in Obsidian and publishes a filtered one-way Gallop-Reader mirror. Obsidian itself is not bundled as a Python dependency. iCloud/Cloud Files integration is an operating-system/provider boundary; Gallop does not redistribute or modify provider software.

## Data and authority boundary

A dependency or adapter may transport data but does not gain learning authority by doing so. In particular:

- MCP transport does not make Tutor output verified mastery.
- Provider output does not become learner evidence automatically.
- Obsidian/Reader storage does not become Journal authority.
- A dependency upgrade must not silently reinterpret historical Journal events.

Dependency upgrades that change protocol, serialization, persistence, or failure semantics require compatibility tests and, where relevant, migration design.

This document describes engineering/license boundaries and is not a legal opinion about every future integration.
