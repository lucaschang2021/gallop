# Current status

**Snapshot: 2026-09-15.** Gallop source is at **v1.2.0 — Zero-Touch Learning Continuity**. The four-Tutor implementation is complete, controlled real learner dogfood passed, and the Windows/Ubuntu × Python 3.11/3.13 mainline CI matrix has completed successfully for the v1.2 source baseline.

Gallop is headless. The product definition is:

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

For the authoritative, item-by-item capability and boundary inventory, see [Capabilities and Product Boundaries](capabilities-and-boundaries.md).

## Operational status

| Area | Status | Evidence / boundary |
|---|---|---|
| Four subject-bound GPT Tutors | PASS | Mathematics, Statistics & Econometrics, Finance, CS & AI each use a bound local MCP server |
| Shared Journal/application | PASS | One append-only evidence system; subject identity is enforced at the server boundary |
| Fresh-chat continuity | PASS | Stable session identity restores bounded Journal-derived context without the old transcript |
| Incremental checkpointing | PASS | Meaningful work commits before projection refresh; abrupt exit recovery was exercised |
| Evidence authority | PASS | Tutor assessments remain candidate evidence; human attestation is distinct; assistance rules gate independence |
| Progressive Mentorship | PASS | Current capability, target, prerequisite gaps, struggle, scaffolding, and mentor role are deterministic advisory outputs |
| Obsidian projection | PASS | Managed Session / Concept / Mistake / Home and related views; ownership failures fail closed |
| Gallop-Reader one-way continuity | PASS | Controlled publication, republish recovery, and learner-confirmed mobile visibility passed |
| V1 exact replay compatibility | PASS | Historical V1 state/projection remain exact under the regression fixture |
| DeepTutor dependency | OPTIONAL / LEGACY | Preserved as an isolated adapter; not required for v1.2 Zero-Touch runtime |

The dated [real dogfood acceptance](audits/v1.2-real-dogfood-acceptance.md) is the authoritative controlled-use record. It deliberately keeps learner outcome quality separate from runtime acceptance: a partial Mathematics independent retest remained `GUIDED`, mastery `0`, rather than being promoted for release optics.

## Existing capability inventory

The following are **already implemented or intentionally preserved**, not roadmap promises:

### Primary v1.2 capabilities

- four subject-bound GPT Tutor MCP surfaces;
- stable Tutor/session/event identity with open/resume/record/checkpoint/finalize/readback;
- bounded Journal-derived fresh-chat continuity;
- incremental checkpoints, abrupt-close restore, idempotent exact retry, conflict detection;
- append-only Journal, deterministic replay, integrity guards, rebuildable derived state;
- candidate-vs-attested evidence authority with assistance and agent provenance;
- conservative mastery/readiness derivation;
- Elite evidence semantics for task type, quality, hints, provenance, transfer, failure modes, benchmarks, and prerequisite links;
- Progressive Mentorship over current capability, explicit targets, training zones, scaffolding, prerequisite repair, struggle, gains, mentor role, and research independence;
- subject-specific training policy for mathematics, statistics/econometrics, finance, and CS/AI;
- no-agent / closed-book evidence semantics;
- managed Obsidian projections;
- one-way Gallop-Reader publication with ownership, backup/recovery, and mobile continuity;
- iCloud-aware Reader binding/safety checks on the supported Windows path;
- versioned Tutor/evidence/context/readiness/benchmark/target/prerequisite and legacy schemas;
- executable architecture, replay, privacy, test, type, example, demo, and wheel gates.

### Retained compatibility capabilities

These remain real working surfaces, but they no longer define the primary learner experience:

- Automation V1 intake → queue/explain → prepare → confirmed start → human-confirmed ingest → cycle/projection;
- Automation V1 durable Journal/replay/recovery and provider job lifecycle;
- optional DeepTutor submit/poll/collect bridge;
- legacy v0.1 session → practice manifest → practice result → mastery workflow;
- historical schemas, CLI paths, offline demo, and exact replay fixtures.

The distinction matters: **compatibility is preserved without creating a second authority model or second learner-facing product.**

## Hard boundaries in force

The current source baseline explicitly does **not** claim or provide:

1. a separate Gallop learner UI — the four GPT Tutor conversations are the learner-facing surface;
2. model/provider grading authority — model output may teach or submit candidate evidence but cannot directly award mastery;
3. identity verification or proctoring — human attestation is confirmation, not proof of authorship;
4. autonomous curriculum ownership — Progressive Mentorship is advisory and does not silently rewrite targets, schedules, or queues;
5. a general agent-swarm runtime — Gallop governs learning continuity/evidence, not arbitrary autonomous agents;
6. mandatory DeepTutor — it is legacy/optional only;
7. cross-subject or cross-concept evidence leakage;
8. silent reinterpretation/migration of historical persistent state;
9. psychometric or clinical validity of mastery/readiness;
10. tamper-proof security against a hostile local machine owner;
11. distributed atomicity across Journal + Markdown + cloud publication;
12. generic iCloud/Obsidian provisioning or repair;
13. perfect sensitive-text detection by repository/Reader filters;
14. semantic retrieval, broad plugin ecosystem, Gallop UI, or Yau-specific competition engine as v1.2 baseline capabilities;
15. equivalence between source version and GitHub Release/tag/PyPI/artifact state.

## Architecture now in use

The v1.2 daily-use path is:

```text
Learner
  ↕
Four GPT Tutor conversations
  ↕ subject-bound MCP
Gallop Tutor Bridge
  ↕
Append-only Journal → replayed state / evidence / mentorship / bounded context
  ↓
Owned Obsidian projections
  ↓
Filtered one-way Gallop-Reader
```

`gallop/tutor/` owns the v1.2 protocol/runtime bridge/context/MCP surface. `gallop/automation/` owns journal-backed orchestration, replay, queue, views, and legacy durable jobs. `gallop/progression/` remains a pure advisory decision domain. Obsidian and Reader are projections and never authoritative progression stores.

## Authority model

| Surface | Authority |
|---|---|
| GPT Tutor | teaching/observation/candidate evidence only |
| Tutor Bridge | protocol validation and durable recording, not grading authority |
| Journal | authoritative accepted learning-event history |
| Evidence/mastery policy | governed admission and capability derivation |
| Progressive Mentorship | advisory training decisions only; no hidden scheduler mutation |
| Obsidian | human-readable projection; manual edits do not mutate authority |
| Gallop-Reader | one-way reading mirror only |
| DeepTutor/provider | optional practice material only |

## CI and governance

The required matrix is Windows + Ubuntu on Python 3.11 and 3.13. The workflow runs:

- Ruff;
- scoped Mypy;
- full pytest regression;
- V1 exact replay verification;
- protocol/example validation;
- executable Architecture Gate;
- reachable-history repository/privacy audit;
- isolated offline demo;
- wheel build.

Architecture direction, time seams, authority boundaries, and hotspot growth are enforced by `ARCHITECTURE.toml`, `scripts/check_architecture.py`, and the governance documentation. Soft size warnings remain review signals, not hidden hard failures.

## Real acceptance scope

Controlled real dogfood covers:

- all four Tutor subjects;
- proof / derivation / simulation reasoning / No-Agent Coding;
- candidate assessment plus explicit authorship/human confirmation flow;
- incremental checkpoints;
- intentional process termination and restart restoration;
- exact duplicate event recovery;
- fresh-chat continuation without transcript access;
- automatic owned Obsidian projection;
- fail-closed backup-based projection recovery;
- Reader republish recovery and mobile visibility;
- subject isolation and no unsupported mastery promotion.

This is strong runtime acceptance evidence, not a claim that Gallop is a validated educational measurement instrument or that every learner answer was correct.

## Release-management status

Source package metadata is `gallop-learning` `1.2.0`. Source capability, CI acceptance, GitHub Release/tag state, PyPI publication, and attached release artifacts are separate facts and should be reported separately.

## Current operating rule

Gallop has moved from **BUILD → USE**. The default priority is now sustained daily learning, real evidence accumulation, regression monitoring, and small corrective maintenance. New architecture work should require a demonstrated need from real use rather than being added by default.

See [Capabilities and Product Boundaries](capabilities-and-boundaries.md), [Architecture](architecture.md), [Quickstart](quickstart.md), [v1.2 Tutor Protocol](v1.2-tutor-protocol.md), [Real Tutor Integration](v1.2-real-tutor-integration.md), [Zero-Touch baseline](baselines/v1.2-zero-touch-baseline.md), and the [Roadmap](roadmap.md).