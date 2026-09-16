# Gallop v1.2 — Existing Capabilities and Product Boundaries

**Status snapshot: 2026-09-15.** This document is the public capability inventory for the current Gallop v1.2 source baseline. It distinguishes what already exists from compatibility-only surfaces, and it states the hard boundaries that future work must preserve unless an explicit architecture change is approved.

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

Gallop is a **headless, local-first learning control plane** for four subject-bound GPT Tutors: Mathematics, Statistics & Econometrics, Finance, and CS & AI. The Tutor conversations are the learner-facing surface. Gallop owns learning-state authority, evidence admission, replay, continuity, mentorship policy, and projections.

## 1. Existing primary capabilities

### Four subject-bound Tutor surfaces

Gallop exposes four permanent subject-bound MCP Tutor servers. Each server is bound to one subject and validates subject, Tutor identity, recorder identity, protocol version, and event shape before authoritative mutation. The four Tutors share one governed Gallop backend; they are not four independent learning stores.

### Tutor session lifecycle and stable identity

The v1.2 Tutor Protocol supports stable session IDs and event IDs, session open/resume, learning-event recording, meaningful checkpointing, finalization, and readback. Exact retries are idempotent; reuse of an identity with different normalized content fails closed.

### Fresh-chat continuity

A new Tutor conversation can restore bounded learning context from the Journal using stable identity. Continuity does not depend on retaining the old transcript or treating model memory as authoritative state.

### Incremental checkpointing and crash recovery

Meaningful learning progress can be committed before a session ends. Abrupt process/desktop exit can be followed by restart and session restoration from committed Journal history. Projection failure after an authoritative commit is treated as a recoverable projection problem, not as evidence that the learning event never happened.

### Append-only Journal and deterministic replay

Gallop stores authoritative learning events in an append-only Journal and rebuilds derived state by deterministic replay. Historical V1 replay remains a compatibility invariant. Hash-chain and database guards detect accidental history inconsistency; derived caches can be rebuilt and are not authoritative truth files.

### Evidence authority and provenance

Gallop distinguishes observation, attempt, candidate assessment, human-attested assessment, independent evidence, assisted work, solution-seen work, AI-assisted/generated work, provider output, and system-derived state. Tutor/model output cannot directly promote mastery. Assistance and agent-use provenance constrain whether work can count as independent evidence.

### Conservative mastery and readiness

Mastery/readiness changes require governed evidence rather than praise, exposure, a single strong answer, or a model score. Failures may lower confidence or add weakness evidence without mechanically erasing established capability. Missing evidence means unknown, not permission to infer success.

### Elite evidence, benchmarks, and readiness profiles

Gallop retains structured v1.1 evidence semantics for task type, quality, independence, hints, agent provenance, transfer, failure modes, benchmark conditions, and explicit prerequisite links. Readiness and benchmark views are evidence-backed and do not become a single opaque ability score or award predictor.

### Progressive Mentorship Engine

The pure `gallop.progression` domain derives current capability, explicit target gap, prerequisite diagnosis, productive-struggle state, training zone, designed scaffolding, progression action, capability gains, mentor role, and research-independence signals.

Permanent rules include:

- target capability never initializes or inflates current capability;
- difficulty may adapt while the target ceiling remains fixed;
- scaffolding fades conservatively rather than disappearing in one jump;
- assisted or AI-generated work cannot silently become independent evidence;
- prerequisite repair does not certify the original target;
- advanced/Monster failure does not erase unrelated established mastery;
- mentorship output is advisory and has no hidden scheduler/queue authority.

### Four-subject training policy

One governed engine supports Mathematics, Statistics & Econometrics, Finance, and CS & AI with subject-specific policy data. Supported high-level task families include proofs/hard problems, derivations, simulations and empirical reasoning, oral work, paper/replication work, coding/no-agent coding, systems problems, research tasks, and benchmarks.

### Automation V1 compatibility surface

`gallop/automation/` remains a working subsystem for explicit CLI-driven learning operations. It retains intake, queue/explain, preparation, confirmed start, human-confirmed result ingestion, cycle/projection, durable Journal/replay, recovery, and legacy provider-job orchestration. This is a compatibility/developer surface, not a second learner-facing product.

### Optional DeepTutor bridge

The existing DeepTutor adapter and durable submit/poll/collect lifecycle remain available for explicit external practice generation and historical compatibility. Provider output is preparation material, not learner-performance authority. DeepTutor is **legacy, optional, non-authoritative, and not required by the v1.2 Zero-Touch path**.

### Legacy v0.1 workflow compatibility

Historical session → practice-manifest → practice-result → mastery workflows, offline demo behavior, schemas, and CLI paths remain available. Old histories are not silently reinterpreted as v1.2 evidence.

### No-Agent learning support

Gallop can record and require no-agent / closed-book / assistance-constrained conditions. These conditions are evidence/provenance semantics, not technical proctoring. A successful run under AI-generated provenance does not become Coding Independence merely because the code works.

### Obsidian projections

Gallop projects governed state into human-readable Obsidian views, including Tutor session, concept, mistake, home/context, development, readiness/benchmark, and related learning views. Managed ownership is explicit: unknown or conflicting edits inside Gallop-owned regions fail closed instead of silently overwriting human data.

### Gallop-Reader one-way mobile mirror

The Reader exporter provides filtered, one-way publication from the main learning Vault to `Gallop-Reader`, with ownership receipts, backup/recovery, privacy filtering, dry-run support, atomic per-file publication, and validated mobile visibility. Reader is a reading mirror; phone edits do not become authoritative learning state.

### iCloud-aware Reader safety

On the supported Windows/iCloud path, the exporter can use explicit binding and Cloud Files metadata checks before mutation. This is a fail-closed safety gate and recovery aid, not a cloud provisioning or repair engine.

### Versioned schemas and validation

Gallop ships JSON Schema contracts for sessions, practice manifests/results, automation results, Elite evidence, benchmarks, readiness, targets, prerequisite links, Tutor events/directives, learning context, and related policy data. Invalid or contradictory input fails rather than being normalized into invented evidence.

### Architecture and privacy governance

`ARCHITECTURE.toml`, `scripts/check_architecture.py`, V1 replay verification, repository privacy audit, tests, Ruff, scoped Mypy, example validation, offline demo, and wheel build form the engineering gate. The primary CI matrix is Windows/Ubuntu × Python 3.11/3.13.

## 2. Authority boundaries

| Surface | May do | Must not do |
|---|---|---|
| GPT Tutor | teach, ask, explain, observe, submit candidate events/assessments | declare authoritative mastery, mutate another subject, replace the Journal |
| Tutor MCP / Runtime Bridge | validate, record, checkpoint, resume, expose bounded context | call itself the learner UI, bypass evidence rules, fabricate history |
| Journal | persist authoritative accepted events and support deterministic replay | infer unstated learner success |
| Evidence / mastery policy | admit and classify governed evidence, derive capability | treat praise/model confidence/provider output as mastery |
| Progressive Mentorship | recommend training zone, scaffold, next action, repair/retest | silently mutate the queue, lower the target ceiling, certify capability without evidence |
| Obsidian | present readable governed projections plus user notes | become source of truth by manual editing |
| Gallop-Reader | provide filtered mobile reading continuity | write back authoritative learning state |
| DeepTutor / other provider | generate optional practice material | become mandatory runtime dependency or independent assessment authority |
| Legacy Automation V1 | preserve explicit CLI workflows and compatibility | become a second competing authority model |

## 3. Product boundaries and explicit non-goals

Gallop v1.2 intentionally **does not** provide or claim the following:

- **No separate Gallop learner UI.** The four GPT Tutor conversations are the learner-facing interface.
- **No model-as-grader authority.** GPT/provider output can propose or observe; it cannot directly award mastery.
- **No identity verification or proctoring.** Human attestation is an explicit local confirmation, not cryptographic proof of authorship.
- **No autonomous curriculum owner.** Progressive Mentorship is advisory; it does not silently rewrite targets, schedules, or course plans.
- **No hidden agent swarm.** Gallop is a learning governance/control system, not a general autonomous-agent framework.
- **No mandatory DeepTutor.** DeepTutor is retained only as a legacy optional adapter.
- **No cross-subject evidence leakage.** Mathematics evidence does not silently become Finance/CS/Statistics evidence, and concept A evidence does not certify concept B.
- **No silent migration of historical state.** Persistent semantics require explicit versioning/migration; old data is not reinterpreted to fit a newer story.
- **No psychometric/clinical validity claim.** Mastery/readiness are conservative software-governance constructs, not a validated educational measurement instrument.
- **No hostile-owner tamper-proof claim.** Local hashes, triggers, and replay detect consistency problems; they do not defeat a machine owner with full control.
- **No distributed atomicity claim.** Journal commits are authoritative; multi-file Obsidian/Reader/cloud publication is recoverable but not one distributed transaction.
- **No universal cloud provisioning/sync engine.** Gallop can safely publish through a validated Reader path; it does not provision or repair arbitrary iCloud/Obsidian setups.
- **No guarantee that privacy filters detect every sensitive sentence.** Reader filtering and repository audits are defense in depth.
- **No semantic-retrieval platform in the v1.2 baseline.** Embeddings/RAG-style infrastructure is not part of the primary Zero-Touch path.
- **No broad plugin ecosystem in v1.2.** New adapters must preserve the authority/replay contract and require explicit justification.
- **No Gallop-owned competition specialization in v1.2.** Yau/competition-specific training policy is outside the baseline even though generic benchmark/task evidence exists.
- **No release-status inference from source version.** `gallop-learning==1.2.0` source capability, GitHub Release/tag, PyPI publication, and attached artifacts are separate facts.

## 4. What is primary vs compatibility-only

### Primary v1.2 daily-use path

```text
Learner
  ↕
Four subject-bound GPT Tutors
  ↕ MCP
Tutor Runtime Bridge
  ↕
Append-only Journal → deterministic replay → evidence / mastery / mentorship / bounded context
  ↓
Owned Obsidian projections
  ↓
Filtered one-way Gallop-Reader
```

### Compatibility / secondary surfaces

- Automation V1 CLI workflows;
- legacy v0.1 session/manifest/result/mastery path;
- optional DeepTutor adapter and durable provider jobs;
- legacy schemas and demos required for replay/non-regression coverage.

These remain real capabilities, but they do not redefine the v1.2 learner-facing product.

## 5. Scope rule for future changes

A future change is inside the normal maintenance envelope only if it preserves:

1. Journal authority and deterministic replay;
2. evidence-first mastery/readiness;
3. subject/concept isolation;
4. explicit assistance and agent provenance;
5. target/current-capability separation;
6. one-way projection authority;
7. v1 exact-replay compatibility unless an explicit migration exists;
8. the headless Four-Tutor learner-facing model.

Changes to persistent event meaning, migration semantics, mastery authority, subject isolation, Reader directionality, or the learner-facing surface require explicit architecture review rather than being treated as routine feature work.

See also [Architecture](architecture.md), [Current Status](current-status.md), [Progressive Mentorship](progressive-mentorship.md), [Tutor Protocol](v1.2-tutor-protocol.md), [Real Tutor Integration](v1.2-real-tutor-integration.md), and [Security](../SECURITY.md).