# Progressive Mentorship Engine — RC2

The engine keeps the summit fixed and builds an evidence-backed path toward it.
Its permanent principles are: ceiling stays fixed, difficulty adapts,
assistance fades, evidence determines progression, and independence is the
destination.

## Current and target capability

A target is explicit and immutable: subject, readiness dimension, target state,
description, North-Star flag and explicit prerequisite link refs. A high target
never initializes current state. Current capability is derived as `UNKNOWN`,
`EXPOSED`, `GUIDED`, `PARTIALLY_INDEPENDENT`, `INDEPENDENT`, `TRANSFERRED`,
`RETAINED`, or `RESEARCH_USABLE`. Output carries confidence, independent and
assisted counts, timestamps and evidence refs. Missing evidence stays UNKNOWN.

## Training zones and task design

- `FOUNDATION` repairs prerequisites and builds components.
- `PRODUCTIVE` is the normal daily growth frontier.
- `STRETCH` introduces unfamiliar contexts above stable capability.
- `MONSTER_BENCHMARK` is low-frequency calibration and exposure.

The derived task-design recommendation increases difficulty, novelty and
ambiguity as capability improves. This is an annotation, not a queue mutation.
Only mathematics policy records the familiar 60-70/20-30/about-10 guidance, and
it is descriptive rather than a universal enforced percentage.

Monster failure is classified as overchallenge when its zone is explicit. It
updates North-Star observations without reducing established current state or
mastery. Foundation, Productive, Stretch and Monster evidence remain separately
counted; they are not collapsed into one score.

## Scaffolding and hints

Designed support is `S5 FULL_INSTRUCTION`, `S4 STRUCTURED_GUIDANCE`, `S3
PARTIAL_SCAFFOLD`, `S2 MINIMAL_GUIDANCE`, `S1 ASSESSMENT_MODE`, and `S0
RESEARCH_INDEPENDENCE`. Hint level remains the assistance actually consumed.
The engine starts at S5 when evidence is absent and fades exactly one level after
a successful observation designed at the currently recommended level. Evidence
at S0 cannot jump an unobserved learner from S5 to assessment. Independent work
designed under S5-S2 cannot count as independent mastery evidence.

## Deterministic progression and repair

Actions are `MAINTAIN`, `REDUCE_SCAFFOLDING`, `INCREASE_NOVELTY`,
`INCREASE_DIFFICULTY`, `ADD_TRANSFER_TEST`, `ADD_RETENTION_TEST`,
`REPAIR_PREREQUISITE`, `RETEST_TARGET`, `REDUCE_TASK_SPAN`,
`MOVE_TO_ASSESSMENT`, or `MOVE_TO_RESEARCH_MODE`. There is no probability or LLM
intuition in the decision.

Prerequisite diagnosis uses only link IDs explicitly named by the target. Two
confirmed target failures plus an unestablished linked prerequisite produce
`POSSIBLE`; missing evidence is `UNKNOWN`. Independent prerequisite repair marks
the gap `CLOSED`, then recommends retesting the original target. Repair never
certifies the target itself.

Struggle is recorded or conservatively classified as `PRODUCTIVE_FAILURE`,
`PREREQUISITE_FAILURE`, `OVERCHALLENGE`, `CARELESS_FAILURE`, or
`CONCEPTUAL_FAILURE`. Milestones on partial Monster work remain visible without
turning the attempt into global failure.

## Gains, mentor role and research independence

Capability gains are emitted only when an evidence prefix crosses a capability
state or fades one scaffold step. Weekly feedback contains those descriptions
and refs; it adds no motivational claim. Mentor roles progress per capability
through Teacher, Coach, Domain Mentor, Research Supervisor and Evaluator, with
subject-specific labels supplied by policy data.

Research independence is `RI0 DEPENDENT`, `RI1 GUIDED`, `RI2 STRUCTURED`, `RI3
SEMI_INDEPENDENT`, `RI4 INDEPENDENT_COMPONENT`, `RI5 INDEPENDENT_PROJECT`, or
`RI6 RESEARCH_READY`. RI6 requires repeated independent research components,
an explicit project, transfer and delayed retention evidence.

## Subject policies and views

One core engine serves mathematics, statistics/econometrics, finance and CS/AI.
`mentorship-policies.json` contains their trajectories, simulation/empirical,
derivation/paper and coding ladders, benchmark labels and mentor labels.

`Development.md` is the normal daily view: current capability, frontier,
scaffolding, next action and evidence-backed weekly gains. `North Star.md` holds
high targets, Monster and benchmark calibration, and unresolved gaps. `Today.md`
is unchanged. Raw events, answers, metadata and integration runtime stay outside
the learner Reader.
