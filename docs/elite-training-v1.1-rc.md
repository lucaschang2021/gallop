# Gallop v1.1 Elite Training — historical RC gate

> **Historical record.** This document records the `1.1.0rc1` gate that introduced Elite evidence/readiness semantics. Those semantics were subsequently governed by RC2 and integrated into the accepted v1.2 Zero-Touch architecture. The current state is documented in [Current Status](current-status.md).

Candidate at the time: `1.1.0rc1`, branched from immutable `v1.0.0` at `c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8`.

The candidate added structured Elite evidence, conservative readiness, benchmarks, explicit prerequisite links, optional Tutor/DeepTutor metadata, CLI commands, and concise Obsidian views. It did not change the scheduler, DeepTutor internals, Reader transport, or iCloud architecture.

## Gate evidence at the time

| Requirement | Implementation and verification |
| --- | --- |
| v1 replay and no semantic drift | Frozen v1.0.0 Journal included legacy mastery level 2; exact state/projection comparison |
| independence, hints and agents | Cross-field validation plus assisted/solution-seen/AI-generated non-credit tests |
| extensible failure modes | Packaged registry, validated additive config, historical replay independent of current registry |
| quality and transfer | Ordinal proof/derivation records; explicit novel-context transfer validation |
| benchmark support | Optional score/count fields, competition/custom contexts, complete-coverage rates, no award model |
| readiness safety | Full dimension matrices, provenance, audited transitions, conservative repeated-evidence thresholds |
| explicit links | Four relations, exposed gaps, no implicit queue/curriculum mutation |
| Tutor/DeepTutor compatibility | Optional unconfirmed Tutor extension; optional request metadata; no fabricated telemetry |
| projections/Reader | Concise views and subject summaries; no raw answers/metadata/DB/integration data in learner Reader |
| Golden E2E | Four isolated subject flows including benchmark, explicit link, and no-agent vs AI-generated comparison |

## Final local result at the time

- 243/243 tests passed: all 177 v1 tests plus 66 v1.1 tests.
- Main Vault matched the 56-file baseline and real mastery remained unchanged.
- The live Reader remained intact; the RC did not write to the live Vault or Reader.
- Reachable-history/prospective privacy scans found no new secret, personal path, private learner record, runtime, or mastery data.

## Supersession

The statement that this RC remained uncommitted/unreleased was true for this historical checkpoint. It is **not** the current Gallop status. v1.2 now uses the same evidence/readiness principles inside the four-Tutor Journal/Progressive Mentorship architecture, with controlled real dogfood completed.

See [Elite Training and Evidence Protocol](elite-training-protocol.md) and [v1.2 Real Tutor Integration](v1.2-real-tutor-integration.md).
