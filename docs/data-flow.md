# Data flow

This document describes the **current v1.2 primary data path**. The older file/CLI and DeepTutor flows remain compatibility paths and are described at the end.

## Primary v1.2 flow

```text
Learner
  ↕
Subject-bound GPT Tutor
  ↕ local MCP tools
Tutor Protocol / Runtime Bridge
  ↓ validated, stable-ID events
Append-only Journal
  ↓ deterministic replay
Evidence + mastery + readiness + Progressive Mentorship
  ↓ advisory bounded context / next action
Tutor

Journal
  ↓ owned projection refresh
Obsidian
  ↓ filtered one-way publication
Gallop-Reader
```

## 1. Tutor session open / resume

`open_or_resume_session` validates the configured learner runtime and the server's fixed subject/Tutor identity. A session start is committed with stable identity, then Gallop returns bounded context derived from replayed Journal state.

Fresh-chat continuity never treats the old transcript, model memory, or an Obsidian note as authority.

## 2. Learning events

The Tutor emits structured events such as concept exposure, task issue, learner attempt, hint, feedback, candidate assessment, mistake, repair, proof/coding/simulation activity, checkpoint, and finalization.

Each event has stable identity and provenance. Exact retries are idempotent; reuse of an ID with different normalized content is a conflict.

## 3. Evidence authority

Tutor-originated assessment is **candidate evidence**. It does not directly promote mastery. Explicit human attestation is a separate event/authority boundary. Assistance and agent provenance constrain whether evidence can count as independent.

A target capability is policy intent, not evidence of current capability.

## 4. Journal → replayed state

The append-only Journal is authoritative. Deterministic replay derives concept state, evidence, readiness, unfinished work, review/retest signals, and mentorship inputs. Cached derived state may be rebuilt; editing a cache does not alter history.

## 5. Progressive Mentorship → Tutor directive

Gallop derives advisory current capability, training zone, scaffolding, prerequisite focus, target, next action, assessment boundary, and unfinished work. Directives are bounded and reference their source Journal evidence. They are not authoritative learner outcomes.

## 6. Projection

After a durable Journal commit, Gallop refreshes its owned Obsidian regions. If projection fails, the event remains committed and projection can be retried. Human edits outside managed regions are preserved; unsafe managed-region ownership loss fails closed.

## 7. Reader publication

Privacy-filtered Markdown is published one-way from PC/Vault to the existing validated Gallop-Reader. Journal databases, answers, provider runtime, credentials, configuration, and raw private evidence do not belong in Reader.

Reader is a reading mirror. Phone edits are never imported as learning authority.

## Recovery ordering

The durability rule is:

> **validate → append Journal event → replay/derive → refresh projection → publish Reader**

A later-stage failure must not erase an earlier committed event. Repeating an exact checkpoint or recovery operation must not create duplicate learning evidence.

## Legacy Automation V1 path

The compatible Automation CLI still supports:

```text
Tutor v1 batch package → intake → Journal/queue → prepare
→ optional legacy DeepTutor generation → learner work
→ human-confirmed result → replay → Obsidian → Reader
```

This path remains useful for testing, migration, explicit queue workflows, and legacy integrations, but it is no longer the normal v1.2 learner-facing path.

## Legacy v0.1 path

`sync-session`, `manifest`, `generate`, and `import-result` retain their separate historical state/mastery semantics. They are not silently merged into the v1.2 Journal model.

## Logging / privacy contract

Operational logs should use identifiers, timestamps, event types, subject, success/error codes, and recovery metadata. Do not log whole transcripts, learner answers not required for recovery, credentials, tokens, private paths, or cloud/provider secrets. Hashing an identifier is pseudonymization, not anonymity.
