# v0.1.0 verification record

Release preparation was verified on 2026-08-31.

## Reproducible checks

```bash
python -m pip install -e ".[dev]"
python -m pytest
python scripts/validate_examples.py
python scripts/audit_repository.py
python -m gallop demo --output demo-output
python -m pip wheel . --no-deps --wheel-dir dist
```

- 47 local automated tests passed on Python 3.13 / Windows.
- Four public protocol examples passed schema validation.
- The suite includes the four original mastery safety cases, replay and
  collision checks, namespace isolation, path containment, lock handling,
  recoverable write failures, CLI configuration and DeepTutor transport checks.
- The installed wheel was exercised outside the source checkout; its bundled
  schemas and offline demo worked, with synthetic mastery 1 -> 2.
- CI runs the same test/schema/audit/demo/build workflow on Windows and Ubuntu,
  with Python 3.11 and 3.13. Its current status is recorded by GitHub Actions,
  not inferred from local success.

## Live DeepTutor acceptance

An explicit opt-in run against DeepTutor 1.6.1 generated seven real questions
from the bundled fictional continuity manifest. A scripted test actor supplied
a synthetic 5/7 summary with one hint. Gallop evaluated mastery 1 -> 2 and
wrote the result, Markdown, review entries and state only inside an isolated
`integration_tests` namespace. A replay reused saved practice without making
another external generation call.

This verifies the transport and writeback loop. It is not evidence of a human
learner's performance, independent grading or pedagogical question quality.
Provider credentials and local account state are not part of the test assets.

## Privacy and security scope

The release audit scans text blobs across every reachable Git ref, checks
commit author/committer identities, and rejects unexpected large/binary blobs.
Manual review complements the pattern scan. Only synthetic examples belong in
the public source tree. Public GitHub account/repository identifiers are
intentional; private notes, local paths, learning state and credentials are not.

The scanner is a release guardrail, not a proof that arbitrary secrets can
never escape detection. Publish source archives or a fresh remote clone; do
not distribute a development checkout's private reflogs or recovery objects.

## Scope boundaries

The release does not scrape ChatGPT accounts, install a background scheduler,
enable embeddings, copy DeepTutor, or assess genuine proof/oral performance
automatically. No-agent mode is a learning workflow, not an access-control or
proctoring boundary. Recovery and single-writer limitations are documented in
the [quickstart](../quickstart.md).
