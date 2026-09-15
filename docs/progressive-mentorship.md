# Progressive Mentorship Engine

The pure `gallop.progression` domain keeps the summit fixed and builds an evidence-backed path toward it. `gallop.mentorship` remains the compatibility/policy-loading facade; v1.2 also exposes the resulting guidance to the four GPT Tutors as bounded advisory context.

Its permanent principles are:

> **ceiling stays fixed · difficulty adapts · assistance fades · evidence determines progression · independence is the destination**

## v1.2 role

Progressive Mentorship is part of the accepted v1.2 architecture, not a future RC2 target. The Runtime Bridge and Context Builder can surface current capability, target, training zone, scaffolding, prerequisite focus, review/retest signals, unfinished work, and next action to the subject-bound Tutor.

The engine remains advisory. Tutor wording and teaching interaction are not authority. A target never raises current capability, and a Tutor directive never directly promotes mastery.

## Current capability and target

A target is explicit and immutable: subject, readiness dimension, target state, description, North-Star flag, and explicit prerequisite refs. Missing evidence stays `UNKNOWN`.

Current capability is evidence-derived as:

`UNKNOWN` → `EXPOSED` → `GUIDED` → `PARTIALLY_INDEPENDENT` → `INDEPENDENT` → `TRANSFERRED` → `RETAINED` → `RESEARCH_USABLE`.

Outputs carry confidence, independent/assisted counts, timestamps, and evidence refs. The engine cannot infer achieved capability from aspiration, Tutor praise, or a target record.

## Training zones

- `FOUNDATION`: repair prerequisites and build components.
- `PRODUCTIVE`: normal daily growth frontier.
- `STRETCH`: unfamiliar contexts above stable capability.
- `MONSTER_BENCHMARK`: low-frequency calibration/exposure.

Task-design recommendations increase difficulty, novelty, and ambiguity as evidence supports higher capability. These are annotations/directives, not hidden queue mutations.

Monster failure is isolated as overchallenge when appropriate. It can inform North-Star calibration without erasing established mastery or current capability.

## Scaffolding

Designed support is:

`S5 FULL_INSTRUCTION` → `S4 STRUCTURED_GUIDANCE` → `S3 PARTIAL_SCAFFOLD` → `S2 MINIMAL_GUIDANCE` → `S1 ASSESSMENT_MODE` → `S0 RESEARCH_INDEPENDENCE`.

Hint level records assistance actually consumed. Scaffolding fades conservatively, one step at a time after qualifying evidence. Evidence produced under heavy designed support cannot be relabelled as independent merely because the final answer is correct.

## Deterministic progression and repair

Available actions include `MAINTAIN`, `REDUCE_SCAFFOLDING`, `INCREASE_NOVELTY`, `INCREASE_DIFFICULTY`, `ADD_TRANSFER_TEST`, `ADD_RETENTION_TEST`, `REPAIR_PREREQUISITE`, `RETEST_TARGET`, `REDUCE_TASK_SPAN`, `MOVE_TO_ASSESSMENT`, and `MOVE_TO_RESEARCH_MODE`.

Prerequisite diagnosis uses explicit links. Repairing a prerequisite closes that gap; it does not certify the original target. The target must be retested.

Struggle can be classified as `PRODUCTIVE_FAILURE`, `PREREQUISITE_FAILURE`, `OVERCHALLENGE`, `CARELESS_FAILURE`, or `CONCEPTUAL_FAILURE` when evidence supports the classification.

## Evidence authority

Tutor-originated assessments enter as candidate evidence. Explicit human attestation is distinct. Agent provenance and assistance constrain independence classification; AI-generated code cannot become independent coding evidence.

Readiness and concept evidence remain scoped to their subject/concept. Evidence for Concept A does not become Concept B evidence merely because they share a readiness dimension.

## Gains, mentor role, and research independence

Capability gains are emitted only when evidence crosses a real capability boundary or justifies a scaffold reduction. Weekly feedback is evidence-backed rather than motivationally fabricated.

Mentor roles progress from Teacher through Coach, Domain Mentor, Research Supervisor, and Evaluator, with subject-specific labels supplied by policy data.

Research independence uses `RI0 DEPENDENT` through `RI6 RESEARCH_READY`. Higher levels require repeated independent components, explicit project work, transfer, and delayed retention—not one successful event.

## Four-subject policy

One core engine serves Mathematics, Statistics & Econometrics, Finance, and CS & AI. `mentorship-policies.json` contains trajectories, simulation/empirical ladders, derivation/paper ladders, coding ladders, benchmark labels, and mentor labels.

## Tutor integration and fresh-chat continuity

The v1.2 Context Builder converts replayed Journal state into bounded advisory context for the correct subject Tutor. A stable Journal head produces deterministic directive identity/content. A fresh chat restores from Journal state, not from the prior transcript or model memory.

If restoration fails, Gallop returns no fabricated context; committed evidence remains authoritative.

## Projections

`Development.md` and related Tutor/subject projections show current capability, frontier, scaffolding, next action, evidence-backed gains, and unresolved gaps. `North Star.md` can hold high targets and benchmark calibration. These Markdown files are readable projections; edits do not mutate authority.

## Compatibility

The RC2 implementation and gates remain historical evidence for how the engine was introduced. Historical V1 replay remains exact. DeepTutor, when used through the legacy adapter, supplies provider material—not progression authority.

See [v1.2 Tutor Protocol](v1.2-tutor-protocol.md), [Architecture](architecture.md), and [Current Status](current-status.md).
