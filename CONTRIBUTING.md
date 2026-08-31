# Contributing to Gallop

Gallop welcomes focused contributions that strengthen deliberate practice,
local ownership, and evidence quality.

## Before opening an issue

- Remove private notes, Vault paths, credentials, and learner history.
- Include a minimal synthetic reproduction.
- State the Gallop version, Python version, operating system, and adapter.
- For security issues, follow `SECURITY.md` instead of filing a public issue.

## Development setup

```bash
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell or
`source .venv/bin/activate` on Linux/macOS, then run:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python scripts/validate_examples.py
python -m gallop demo --output demo-output
python -m pip wheel . --no-deps --wheel-dir dist
```

Use Python 3.11+; CI runs Windows/Ubuntu with Python 3.11 and 3.13. Tests and
the demo use synthetic fixtures and need no provider credentials. Documentation
changes should also follow the Automation example in [quickstart](docs/quickstart.md).
Keep [Chinese](README.md) and [English](README.en.md) README capabilities,
commands, status and limitations aligned.

Before committing, inspect `git diff --check` and `git diff --cached`. Use a
public GitHub noreply commit email: the repository privacy audit rejects private
author/committer emails. After committing, run:

```bash
python scripts/audit_repository.py
```

The audit scans committed blobs across reachable refs and commit metadata, not
uncommitted edits. It complements manual review; do not treat it as complete
secret detection. CI runs it with full Git history. Never commit virtual
environments, generated wheels, demo/runtime outputs, real responses or vaults.

## Proposing an adapter

Start with an issue describing the boundary, external dependency, privacy
surface, failure modes, and smallest useful API. Tutor, knowledge-store, and
practice-engine adapters must not move canonical learning state implicitly.

## Adding schemas

- Use JSON Schema draft 2020-12.
- Preserve truthful empty arrays rather than inferred content.
- Add a valid public example and a rejection test.
- Document compatibility and migration implications.

## Adding practice engines or learning examples

Practice engines need mocked unit coverage and explicit unavailable/error paths.
Examples must be fictional, deterministic where possible, and independent of
private accounts. Never commit generated real-learning artifacts.

## Pull requests

Use a focused branch and open a PR against `main`; do not combine unrelated
refactors. Explain the problem, user-visible result, validation, privacy impact,
and protocol/replay compatibility. Clearly separate mocked/offline checks from
live provider or device validation. Substantial architecture or migration work
should start with an issue. See the [architecture](docs/architecture.md) and
[roadmap](docs/roadmap.md) for boundaries and contribution priorities.

The project uses semantic versioning and Apache-2.0 contributions. Keep version,
tags and release notes consistent; a successful wheel build alone is not
publication to GitHub Releases or PyPI.
