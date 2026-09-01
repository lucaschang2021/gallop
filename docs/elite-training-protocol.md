# Elite Training Protocol 1.1

Elite evidence records **how** a learner performed. It preserves three views:

- **Mastery** is conservative concept state from diverse confirmed performance.
- **Readiness** is a capability profile with status, confidence, count and refs.
- **Benchmark performance** is a chronological record under stated conditions.

There is no overall ability score and no competition award prediction.

## Performance semantics

`INDEPENDENT` means no performance hint and hint level 0. `HINT_1` is a
clarification at level 1. `HINT_2` is direction or structure at levels 2-3.
`ASSISTED` is substantial help at level 4. `SOLUTION_SEEN` means the core
solution was exposed and cannot establish mastery. `UNSOLVED` records weakness
without reducing mastery. Clearly contradictory combinations fail closed.

Agent provenance is `NONE`, `REFERENCE_ONLY`, `HINT_ONLY`, `AI_ASSISTED`,
`AI_GENERATED`, or `UNKNOWN`. Missing provenance remains absent. Working code
plus `AI_GENERATED` does not establish Coding Independence.

Quality is recorded by ordinal dimensions: `POOR`, `DEVELOPING`, `SOLID`,
`STRONG`, `EXCEPTIONAL`, or `UNKNOWN`. It is never inferred from score. Transfer
is `NOT_TESTED`, `FAILED`, `PARTIAL`, or `SUCCESS`; success requires distinct
source and target contexts, independent provenance and explicit `NEW_CONTEXT`.
Durations and `time_spent` use seconds.

## Failure modes and task types

Failure modes use `namespace:MODE`. A configuration may point to a validated
registry that adds namespaces or modes. Historical modes replay without current
registry validation, so configuration changes never rewrite the journal.

Task types are `CONCEPT`, `PROOF`, `DERIVATION`, `HARD_PROBLEM`, `LONG_PROBLEM`,
`SIMULATION`, `ORAL_EXAM`, `CODING`, `NO_AGENT_CODING`, `SYSTEMS_PROBLEM`,
`EMPIRICAL`, `PAPER_READING`, `REPLICATION`, `RESEARCH`, `BENCHMARK`, and
`MINI_CONTEST`. Recording a type never implies success.

## Readiness and provenance

Profiles contain every documented mathematics, statistics/econometrics,
finance and CS/AI dimension. An untouched profile is `UNKNOWN`, low confidence,
zero evidence and no refs. Assisted work can support only foundational
familiarity in a non-independence dimension. Repeated independent performances
across distinct days and contexts progress conservatively. `ADVANCED` requires
at least six diverse delayed performances, explicit novel transfer and a
verified closed-book/no-AI benchmark. One event can never produce Advanced.

Every change is an immutable `readiness_transition` verified on replay.
`readiness explain` exposes independent, assisted, benchmark and transfer refs,
failure modes and explicit prerequisite gaps.

## Benchmarks and explicit links

Benchmark types cover IMC, Yau Undergraduate Mathematics Contest, mini contest,
closed-book, oral, no-agent, course exam and custom contexts. Scores, counts and
duration are optional. Rates appear only with explicit denominators and complete
evidence coverage. Rolling observations combine only the same subject, type,
source and conditions, retain nulls, and are descriptions rather than forecasts.

`PREREQUISITE`, `SUPPORTS`, `TRANSFER`, and `RELATED` links carry explicit source,
target and provenance. Only `PREREQUISITE` is described as a gap. Every link is
informational with `curriculum_action: NONE`; v1.1 does not infer edges or alter
curriculum.

## System boundaries and migration

Native events are `elite_evidence`, `benchmark`, `prerequisite_link` and audited
readiness transitions. IDs are stable and conflicting reuse fails. Tutor v1 may
add unconfirmed evidence. A DeepTutor manifest may request conditions, but a
request is not outcome telemetry and missing telemetry is never fabricated.

Projections are concise `Elite Training.md`, `Benchmarks.md`, `Readiness.md` and
small subject Home summaries; `Today.md` remains operational. The existing
one-way Reader exporter applies privacy filters. Raw events, SQLite, metadata,
response refs, answers and integration data are not projected to a learner Reader.

There is no v1 migration. A frozen synthetic journal produced by immutable
v1.0.0, including legacy mastery transitions, is replayed against its exact
expected state. A v1-only journal has no `elite` key and unchanged projections.
Missing fields display `UNKNOWN` or `NOT_RECORDED`; history is not rewritten.

Adaptive scheduling, ML mastery prediction, graph inference, automatic
curriculum selection, award prediction and agent swarms remain outside v1.1.
