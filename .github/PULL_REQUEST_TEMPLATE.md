## Problem and change

What learner/contributor problem does this solve? What changes for users?

## Surface and authority

- Affected surface: Tutor MCP / Protocol / Bridge / Journal / Progressive Mentorship / Projection / Reader / Automation V1 / legacy adapter / docs only
- Does Tutor/model/provider output gain any new authority? Why is that safe?
- Impact on candidate evidence, human attestation, assistance/agent provenance, current capability, target capability, mastery/readiness, or subject isolation:

## Validation

- Commands/checks run and results:
- Synthetic/offline evidence:
- Isolated real integration evidence:
- Real learner/device evidence, if any:
- Checks not run and why:

## Replay and compatibility

- Impact on schemas, event meaning, stable IDs/idempotency, deterministic replay, V1 exact replay, or migration:
- Legacy Automation V1 / v0.1 / DeepTutor impact:
- If persistent semantics change, where is the explicit version/migration design?

## Privacy and recovery

- Data sent to external services or copied to Obsidian/Reader:
- Journal-first durability/recovery behavior:
- Confirm no credentials, private learner responses, Journal/runtime output, local paths, cloud metadata, or Vault/Reader private data are included.

## Documentation and release state

- Update both READMEs and relevant technical docs if capability/setup/status changes.
- Distinguish source version from GitHub Release/tag/PyPI/artifact publication.
- Do not claim real acceptance from synthetic tests.

## Governance

- `ruff check gallop tests scripts`
- `mypy`
- `pytest`
- `python scripts/verify_v1_replay.py`
- `python scripts/validate_examples.py`
- `python scripts/check_architecture.py`
- `python scripts/audit_repository.py`
