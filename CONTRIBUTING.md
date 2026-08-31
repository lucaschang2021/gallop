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
python -m pip install -e ".[dev]"
pytest
python scripts/validate_examples.py
```

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

Keep changes small and explain tests, privacy impact, and protocol impact. The
project uses semantic versioning and Apache-2.0 contributions.
