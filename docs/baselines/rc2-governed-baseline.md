# GALLOP v1.1 RC2 — GOVERNED BASELINE

> **Historical frozen predecessor.** This record captures the governance boundary immediately before v1.2 implementation. Its statements that the four-Tutor surface was planned and v1.2 was not started were true at this checkpoint. v1.2 has since been implemented and accepted in controlled real dogfood; see [v1.2 baseline](v1.2-zero-touch-baseline.md) and [Current Status](../current-status.md).

Record date: 2026-09-13

Governed code SHA: `d2c4d9357c2553824cf44cc29c8961286e244a46`

Baseline record commit: the commit containing this file. The record does not self-reference an object ID because that would make the commit hash impossible to stabilize.

## Closure result at this checkpoint

- Governance closure G0-G11: PASS at the governed code SHA.
- Product boundary: Gallop remained headless.
- Four GPT Tutor chats: planned v1.2 learner-facing surface, not yet part of this RC2 baseline.
- DeepTutor: legacy, optional, non-authoritative, and not the future primary workflow.
- v1.2 implementation: not started by this closure.

## Required evidence

- Tests: 298 passed locally; GitHub Actions covered Ubuntu/Windows × Python 3.11/3.13.
- Pull-request CI for the governed code SHA: PASS, run `34747391949`.
- Ruff: PASS for configured correctness rules.
- Scoped Mypy: PASS for the frozen progression/application-port boundary.
- Architecture contract: PASS with zero existing/introduced hard violations.
- Repository privacy audit: PASS for history reachable from the exact governed SHA, with the exact commit-scoped historical metadata debt recorded by repository policy.
- Protocol examples, offline demo, and wheel build: PASS.
- Local wheel at the time: `gallop_learning-1.1.0rc2-py3-none-any.whl`.

## Replay and semantic invariants

Frozen V1 replay source commit: `c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8`.

- Events replayed: 38.
- State exact: true.
- Projection exact: true.
- Mastery drift: none.
- Queue drift: none.
- Evidence drift: none.
- Journal authoritative; Reader/Markdown projections only.
- `queue_mutation=NONE` remained non-mutating.

These invariants continue to constrain v1.2 compatibility.

## Historical compatibility/debt notes

- Public v1 deterministic replay, mastery, queue, evidence, CLI demo, schemas, and wheel construction were covered by the RC2 matrix.
- Mypy coverage was intentionally scoped.
- File-size warnings were governance review signals rather than automatic split triggers.
- Synthetic/integration evidence was not Human Production E2E and did not change real learner mastery.

## Freeze decision

The RC2 governance decision was **GO FOR ZERO-TOUCH AUTOMATION**, followed by STOP for the closure task. That sequential rule was subsequently respected: v1.2 work proceeded after governance closure rather than in parallel.

This file is retained as an immutable historical governance explanation; it is not the current product-status document.
