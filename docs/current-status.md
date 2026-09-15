# Current status

**Snapshot: 2026-09-15.** Gallop source is at **v1.2.0 — Zero-Touch Learning Continuity**. The four-Tutor implementation is complete, controlled real learner dogfood passed, and the Windows/Ubuntu × Python 3.11/3.13 mainline CI matrix has completed successfully for the v1.2 source baseline.

Gallop is headless. The product definition is:

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

## Operational status

| Area | Status | Evidence / boundary |
|---|---|---|
| Four subject-bound GPT Tutors | PASS | Mathematics, Statistics & Econometrics, Finance, CS & AI each use a bound local MCP server |
| Shared Journal/application | PASS | One append-only evidence system; subject identity is enforced at the server boundary |
| Fresh-chat continuity | PASS | Stable session identity restores bounded Journal-derived context without the old transcript |
| Incremental checkpointing | PASS | Meaningful work commits before projection refresh; abrupt exit recovery was exercised |
| Evidence authority | PASS | Tutor assessments remain candidate evidence; human attestation is distinct; assistance rules gate independence |
| Progressive Mentorship | PASS | Current capability, target, prerequisite gaps, struggle, scaffolding, and mentor role are deterministic advisory outputs |
| Obsidian projection | PASS | Managed Session / Concept / Mistake / Home views; ownership failures fail closed |
| Gallop-Reader one-way continuity | PASS | Controlled publication, republish recovery, and learner-confirmed mobile visibility passed |
| V1 exact replay compatibility | PASS | Historical V1 state/projection remain exact under the regression fixture |
| DeepTutor dependency | OPTIONAL / LEGACY | Preserved as an isolated adapter; not required for v1.2 Zero-Touch runtime |

The dated [real dogfood acceptance](audits/v1.2-real-dogfood-acceptance.md) is the authoritative controlled-use record. It deliberately keeps learner outcome quality separate from runtime acceptance: a partial Mathematics independent retest remained `GUIDED`, mastery `0`, rather than being promoted for release optics.

## Architecture now in use

The v1.2 daily-use path is:

```text
Learner
  ↕
Four GPT Tutor conversations
  ↕ subject-bound MCP
Gallop Tutor Bridge
  ↕
Append-only Journal → replayed state / evidence / mentorship
  ↓
Owned Obsidian projections
  ↓
Filtered one-way Gallop-Reader
```

`gallop/tutor/` owns the v1.2 protocol/runtime bridge/context/MCP surface. `gallop/automation/` owns journal-backed orchestration, replay, queue, views, and legacy durable jobs. `gallop/progression/` remains a pure advisory decision domain. Obsidian and Reader are projections and never authoritative progression stores.

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

## Compatibility

Automation V1 and legacy v0.1 commands remain available. Historical state is not silently migrated or reinterpreted. DeepTutor submit/poll/collect remains a compatibility path for explicit external practice generation, but v1.2 requires zero DeepTutor runtime dependency for its primary Four-Tutor workflow.

## Release-management status

Source package metadata is `gallop-learning` `1.2.0`. Source capability, CI acceptance, GitHub Release/tag state, PyPI publication, and attached release artifacts are separate facts and should be reported separately. The repository must not describe an old GitHub Release as the current source capability baseline.

## Known limitations

1. **First-time real setup is technical.** Real learner mode still requires an existing Vault plus a validated Reader/export binding; the repository does not provide a universal cloud provisioning wizard.
2. **Evidence authority remains human-governed.** Gallop structures and constrains evidence; it does not independently verify identity, authorship, or truth like a proctor.
3. **No hostile-owner security claim.** SQLite triggers and hash links protect consistency and accidental corruption, not a machine owner with full local control.
4. **Projection/cloud atomicity is limited.** Journal commit is authoritative; multi-file Markdown and cloud synchronization are recoverable but not one distributed transaction.
5. **Learning efficacy is not established.** The mastery/readiness system is a conservative software governance model, not a clinically or psychometrically validated instrument.
6. **v1.2 scope is intentionally narrow.** Competition Mathematics / Yau specialization, semantic retrieval, a general plugin ecosystem, autonomous curriculum expansion, and a Gallop UI are not part of this baseline.

## Current operating rule

Gallop has moved from **BUILD → USE**. The default priority is now sustained daily learning, real evidence accumulation, regression monitoring, and small corrective maintenance. New architecture work should require a demonstrated need from real use rather than being added by default.

See [Architecture](architecture.md), [Quickstart](quickstart.md), [v1.2 Tutor Protocol](v1.2-tutor-protocol.md), [Real Tutor Integration](v1.2-real-tutor-integration.md), [Zero-Touch baseline](baselines/v1.2-zero-touch-baseline.md), and the [Roadmap](roadmap.md).