# Changelog

Gallop follows Semantic Versioning for package/source versions. GitHub Release, tag, PyPI, and artifact publication are separate release-management states and are never inferred from the source version alone.

## [Unreleased]

- Sustained-use maintenance, regression monitoring, evidence calibration, and documentation hardening after the v1.2 Zero-Touch baseline.

## [1.2.0] - 2026-09-14 — source baseline

### Added

- Four permanent subject-bound GPT Tutor MCP surfaces: Mathematics, Statistics & Econometrics, Finance, and CS & AI.
- Versioned v1.2 Tutor Protocol with stable session/event identity, candidate evidence, explicit human attestation, and subject isolation.
- Runtime Bridge for incremental Journal commits, checkpoints, session finalization, and idempotent retry handling.
- Journal-derived bounded learning context and fresh-chat restoration without treating the old transcript or model memory as authority.
- Automatic owned Obsidian projections for Tutor sessions, concepts, mistakes, and home/context views.
- Controlled one-way Gallop-Reader publication and recovery through the existing validated Reader binding.
- Real four-Tutor dogfood covering fresh-chat continuation, abrupt-close recovery, duplicate checkpoint recovery, projection recovery, and mobile visibility.

### Integrated

- Progressive Mentorship Engine as deterministic advisory policy over current capability, explicit targets, prerequisites, productive struggle, scaffolding, gains, mentor role, and research independence.
- Elite evidence/readiness/benchmark semantics from v1.1 into the v1.2 Tutor and Journal authority model.
- DeepTutor retained only as an optional legacy adapter; it is not required by the v1.2 Zero-Touch runtime.

### Compatibility and safety

- Historical V1 replay remains exact under the frozen regression fixture.
- Tutor assessments remain candidate evidence; neither GPT output nor Obsidian edits directly promote mastery.
- AI-generated or assisted work cannot be silently counted as independent evidence.
- The Journal remains authoritative; Obsidian and Reader remain projections.

### Acceptance

- Controlled real four-Tutor dogfood: **PASS**.
- The acceptance deliberately preserved weak learner outcomes: a partial Mathematics independent retest remained `GUIDED` with mastery `0` rather than being promoted for release optics.
- Windows/Ubuntu × Python 3.11/3.13 mainline CI completed successfully for the v1.2 source baseline.

> This changelog entry describes the source baseline. It does not assert that a `v1.2.0` GitHub Release, final tag, PyPI publication, or release assets exist.

## [1.1.0-rc2] - 2026-09 — governed compatibility milestone

- Added evidence-aware Elite Training records and readiness.
- Added the pure `gallop.progression` Progressive Mentorship domain.
- Added architecture governance, explicit Journal/Clock seams, privacy metadata checks, and exact V1 replay protection.
- RC2 was a governance/compatibility milestone and is now historical context for v1.2.

## [1.0.0] - 2026-08-31

- Automation V1: append-only event Journal, deterministic replay, four-subject queue, human-confirmed assessment, conservative mastery, owned Obsidian projections, durable optional DeepTutor jobs, and one-way Reader export.
- Real isolated DeepTutor transport/writeback acceptance completed without changing real learner mastery.

## [0.1.0] - 2026-08-31

- Session, practice manifest, practice result, and mastery protocols.
- Conservative native mastery engine with safety tests.
- Markdown/Obsidian knowledge-store adapter.
- External DeepTutor practice-engine adapter boundary.
- T+1/T+7/T+30 review compatibility.
- Synthetic seven-question mathematics demo and isolated writeback.
- Four optional subject profiles and open-source governance documentation.
