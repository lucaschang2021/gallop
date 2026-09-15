# Contributing to Gallop

Gallop welcomes focused contributions that strengthen evidence quality, local ownership, deterministic replay, learning continuity, and the four-Tutor Zero-Touch workflow.

The current product boundary is:

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

## Before opening an issue

- Remove private notes, learner answers, Vault/Reader paths, local account identifiers, credentials, and provider runtime data.
- Use a minimal synthetic reproduction whenever possible.
- State the Gallop source version, Python version, OS, and surface involved: Tutor MCP / Journal / projection / Reader / legacy Automation V1 / legacy DeepTutor.
- For security issues, follow `SECURITY.md` instead of filing a public issue.

## Development setup

```bash
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` on Linux/macOS, then run:

```bash
python -m pip install -e ".[dev]"
ruff check gallop tests scripts
mypy
pytest
python scripts/verify_v1_replay.py
python scripts/validate_examples.py
python scripts/check_architecture.py
python scripts/audit_repository.py
python -m gallop demo --output demo-output
python -m pip wheel . --no-deps --wheel-dir dist
```

Use Python 3.11+; CI covers Windows/Ubuntu with Python 3.11 and 3.13. Public tests and examples are synthetic and require no learner data or model credentials.

## v1.2 architecture rules

A contribution must preserve these authority boundaries unless an explicitly reviewed migration changes them:

- The append-only Journal is authoritative.
- Tutor output is observation or candidate evidence, never automatic mastery authority.
- Human attestation is distinct from Tutor assessment.
- Obsidian and Gallop-Reader are projections, not writable authority stores.
- Current capability is evidence-derived; an explicit target never raises it.
- Assistance and agent provenance constrain independence claims.
- Four subject-bound Tutor servers must not cross subject identity.
- Fresh-chat continuity must derive from bounded Journal state, not hidden model memory.
- DeepTutor is legacy/optional and must not become a required v1.2 dependency.
- Historical V1 replay must remain exact unless a deliberate, versioned migration is approved.

See [Architecture](docs/architecture.md), [Architecture Governance](docs/architecture-governance.md), [v1.2 Tutor Protocol](docs/v1.2-tutor-protocol.md), and [Current Status](docs/current-status.md).

## Documentation changes

Keep the Chinese and English READMEs semantically aligned. Current-facing docs must describe the accepted v1.2 state, not RC2 as the current product or Zero-Touch as a future target. Historical audit/release documents may retain their original facts but must be clearly labelled historical when later milestones supersede their status language.

Do not claim a GitHub Release, tag, PyPI publication, artifact upload, real-user acceptance, or learning outcome that has not actually occurred.

## Privacy and commit metadata

Before committing, inspect `git diff --check` and `git diff --cached`. Use a public GitHub noreply commit email: the repository privacy audit rejects private author/committer emails.

```bash
python scripts/audit_repository.py
```

The audit scans reachable committed blobs and commit metadata. It complements manual review; it is not complete secret detection. Never commit real Journal databases, private configs, Vault/Reader content, answer keys, provider logs, cloud metadata, generated wheels, or runtime directories.

## Adding Tutor protocol or evidence changes

- Use versioned schemas and explicit rejection cases.
- Preserve stable event/session identity and idempotency semantics.
- Keep candidate evidence separate from confirmed evidence.
- Add synthetic four-subject coverage where the change affects shared behavior.
- Explain replay, migration, authority, privacy, and fresh-chat implications in the PR.

## Adding adapters

Start with an issue describing the external boundary, data leaving the machine, failure/recovery behavior, and smallest useful API. Adapters must not mutate authoritative learning state implicitly.

## Pull requests

Use a focused branch and open a PR against `main`. Explain:

- problem and intended result;
- user-visible surface;
- authority/evidence impact;
- replay/migration impact;
- privacy/data egress;
- validation performed;
- whether evidence is synthetic, isolated-real, or learner-real;
- documentation changed;
- release/tag implications, if any.

A successful source build or wheel build is not publication. The project uses Apache-2.0 and semantic source versions; GitHub Release/tag/PyPI state is managed explicitly and separately.
