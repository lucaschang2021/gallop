# Tutor Output Protocol v1 — legacy batch compatibility

> **Current primary protocol:** Gallop v1.2 uses the incremental bidirectional [v1.2 Tutor Protocol](v1.2-tutor-protocol.md) over four subject-bound MCP surfaces. This document remains the compatibility contract for historical batch/session intake and Automation V1.

The v1 and v1.2 contracts coexist without silently reinterpreting historical Journal data.

## Batch session semantics

A Tutor v1 session is an observation record. Record what actually occurred; never invent scores, completed work, mastery, confidence, independence, or research output.

Automation intake accepts `tutor`, `title`, `occurred_at`, and `summary`; `schema_version` is `1.0`. A stable `session_id` should be supplied in normal use. If omitted, the compatible intake path may derive a deterministic ID from normalized content.

Tutor is one of `mathematics`, `statistics`, `finance`, or `cs-ai`. `occurred_at` must be timezone-aware and valid for the intake rules.

Supported arrays include concepts, proofs/derivations, hard-problem sessions, oral exams, simulation labs, mistakes, weakness tags, open questions, connections, research ideas, and artifacts. Empty arrays are truthful and valid; missing evidence must never be fabricated.

## Validation and identity

Use UTF-8 JSON or the documented fenced-JSON Markdown form. Malformed JSON, duplicate keys, wrong Tutor identity, invalid timestamps, and schema violations are rejected. Raw bytes remain separate from validated events.

Same `session_id` + same normalized content is idempotent. Same ID + different content is a conflict; corrections use a new identity and explicit provenance. Historical sessions are not overwritten.

The normative Automation intake schema is `gallop/schemas/tutor-intake.schema.json`. The stricter legacy `gallop/schemas/session.schema.json` remains for the v0.1 `sync-session` / `manifest` path.

See the synthetic [Automation example](../examples/automation/session.json).

## v1.1 evidence extensions retained for compatibility

A valid v1 payload may contain `elite_evidence`. Tutor-provided items are retained as **unconfirmed/candidate provenance**. They cannot establish independent readiness or mastery until the applicable human/evidence gate admits them.

The compatible `progressive_mentorship` extension may carry target records and attributed context. Tutor-proposed current capability, zone, scaffolding, gains, or research-independence claims do not become derived state merely because they appear in the package.

## Relationship to v1.2

The v1.2 protocol replaces batch handoff as the normal learner-facing continuity path. It adds stable per-event identity, incremental checkpointing, subject-bound MCP transport, bounded Journal-derived context, fresh-chat restoration, candidate assessment, explicit human attestation, and session lifecycle events.

Historical v1 packages remain replay-compatible. Migrating to v1.2 does not rewrite old evidence, and a fresh-chat Tutor does not reconstruct truth from old chat prose.
