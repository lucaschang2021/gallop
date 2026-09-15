# Verification and acceptance index

Gallop keeps **source capability**, **historical release records**, **real acceptance**, and **GitHub Release/tag/PyPI publication** separate. A source version or successful wheel build is not by itself proof of publication.

## Current v1.2 source verification

The maintained source baseline is `gallop-learning 1.2.0` with four subject-bound GPT Tutor MCP surfaces, Journal-backed continuity, Progressive Mentorship, Obsidian projection, and Gallop-Reader publication.

The v1.2 source baseline has evidence for:

- Windows/Ubuntu × Python 3.11/3.13 CI;
- Ruff and scoped Mypy;
- full pytest regression;
- exact V1 replay;
- public protocol/example validation;
- executable architecture gate;
- repository privacy audit on the clean mainline baseline;
- offline synthetic demo and wheel build;
- controlled real four-Tutor dogfood.

The authoritative real-use record is [v1.2 Real Four-Tutor Dogfood Acceptance](../audits/v1.2-real-dogfood-acceptance.md). It covers real sessions in Mathematics, Statistics & Econometrics, Finance, and CS & AI; fresh-chat continuation; incremental checkpoints; abrupt-close and duplicate recovery; owned Obsidian projection; Reader recovery; and learner-confirmed mobile visibility.

Synthetic Golden E2E remains implementation evidence, not learner evidence.

## Historical v1.0.0 verification

Automation V1 acceptance is preserved in [Automation V1 final gate](../automation-final-gate.md). That record includes the historical real DeepTutor generation/collection and user-confirmed isolated response, while preserving real mastery.

It remains compatibility/transport evidence; DeepTutor is now optional legacy infrastructure rather than the v1.2 primary workflow.

## Historical v0.1.0 verification

v0.1.0 release preparation was verified on 2026-08-31 using the then-current test/schema/audit/demo/build workflow. Historical local verification included 47 tests on Python 3.13/Windows plus protocol-example validation and installed-wheel checks.

An explicit opt-in DeepTutor 1.6.1 run generated questions from a fictional manifest and wrote only to an isolated integration namespace. That verified the historical transport/writeback loop, not human learning performance or pedagogical quality.

See [v0.1.0 release record](v0.1.0.md).

## Reproducible source checks

Current contributors should use the maintained gate set rather than copying historical counts:

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

CI status should be read from GitHub Actions for the exact commit/ref being evaluated; do not infer a future commit's health from an older successful run.

## Privacy and publication boundary

The repository audit scans reachable text blobs and commit metadata and rejects private commit identities outside the explicitly governed debt baseline. Manual review complements the scanner.

Only synthetic examples and public engineering records belong in source history. Real learner work, Journal databases, Vault/Reader private content, credentials, private paths, provider state, and cloud metadata stay outside the public repository.

A GitHub Release/tag/PyPI/artifact statement must be backed by the corresponding publication record. Current source documentation intentionally does not convert `version = 1.2.0` into an unsupported publication claim.
