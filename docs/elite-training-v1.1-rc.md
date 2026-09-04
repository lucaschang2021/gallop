# Gallop v1.1 Elite Training — RC gate

Candidate: `1.1.0rc1`, branched from immutable `v1.0.0` at
`c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8`.

This candidate adds structured Elite evidence, conservative readiness,
benchmarks, explicit prerequisite links, optional Tutor/DeepTutor metadata,
CLI commands and concise Obsidian views. It does not change the scheduler,
DeepTutor internals, Reader transport or iCloud architecture.

## Gate evidence

| Requirement | Implementation and verification |
| --- | --- |
| v1 replay and no semantic drift | Frozen v1.0.0 journal includes legacy mastery level 2; exact state and projection comparison |
| independence, hints and agents | Cross-field validation plus assisted/solution-seen/AI-generated non-credit tests |
| extensible failure modes | Packaged registry, validated additive config, historical replay independent of current registry |
| quality and transfer | Ordinal proof/derivation records; explicit novel-context transfer validation |
| benchmark and competition support | Optional score/count fields, IMC/YAU contexts, complete-coverage rates, comparable rolling observations, no award model |
| readiness safety | Full dimension matrices, provenance, audited transitions, conservative repeated-evidence thresholds |
| explicit links | Four relations, exposed gaps, no queue or curriculum mutation |
| Tutor and DeepTutor compatibility | Optional unconfirmed Tutor extension; optional request metadata; no fabricated telemetry |
| projections and Reader | Three concise views and subject summaries; no answers, metadata, raw state, DB or integration data in learner Reader |
| Golden E2E | Four isolated subject flows including benchmark, explicit link and no-agent versus AI-generated comparison |

The final report records the full test count, repository privacy scan, real Vault,
mastery and Reader integrity checks, and reviewed diff. This file is an RC report,
not a release announcement.

## Final local result

- 243/243 tests passed: all 177 v1 tests plus 66 v1.1 tests.
- The real main Vault matches its 56-file baseline and real mastery hash is unchanged.
- The live Reader has eight synchronized Markdown files. The expected seven are
  present and healthy; an externally created empty `00-System/Review Queue.md`
  is also synchronized. This RC did not write to the live Vault or Reader.
- Reachable-history and prospective-worktree privacy scans found no new secret,
  personal path, private learner record, integration runtime, or mastery data.
- The candidate remains uncommitted and unreleased for review.
