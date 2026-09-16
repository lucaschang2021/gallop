# Elite Training and Evidence Protocol

Elite evidence records **how** a learner performed. The semantics introduced during v1.1 are retained in the accepted v1.2 evidence architecture and feed readiness and Progressive Mentorship without becoming a separate learner-facing product.

The system preserves distinct views:

- **Mastery:** conservative concept state from diverse confirmed performance.
- **Readiness:** capability dimensions with status, confidence, counts, and evidence refs.
- **Benchmark performance:** chronological observations under stated conditions.
- **Progressive Mentorship:** deterministic advisory interpretation of current capability versus explicit targets.

There is no single overall ability score and no competition-award prediction.

## Performance semantics

`INDEPENDENT` requires no performance hint and compatible assistance/provenance. `HINT_1`, `HINT_2`, `ASSISTED`, `SOLUTION_SEEN`, and `UNSOLVED` preserve the actual help/result boundary. Contradictory combinations fail closed.

Agent provenance includes `NONE`, `REFERENCE_ONLY`, `HINT_ONLY`, `AI_ASSISTED`, `AI_GENERATED`, or `UNKNOWN`. Working code with `AI_GENERATED` provenance does not establish coding independence.

Quality dimensions remain ordinal (`POOR`, `DEVELOPING`, `SOLID`, `STRONG`, `EXCEPTIONAL`, `UNKNOWN`) and are not inferred mechanically from score.

Transfer is explicit. `SUCCESS` requires a genuinely distinct target context plus compatible independent provenance; a familiar replay is not novel transfer.

## Task types and failure modes

Supported evidence can cover concept work, proof, derivation, hard/long problems, simulation, oral examination, coding, `NO_AGENT_CODING`, systems work, empirical work, paper reading, replication, research, benchmarks, and mini contests.

Recording a task type never implies success.

Failure modes use versioned/validated labels. Historical events replay using their recorded semantics; changing a current registry does not rewrite old evidence.

## Readiness

Readiness dimensions exist for Mathematics, Statistics & Econometrics, Finance, and CS & AI. Missing evidence stays `UNKNOWN` with low confidence and zero refs.

Assisted work can support familiarity but cannot be silently promoted into independence. Higher readiness requires repeated independent work across days/contexts and, where applicable, transfer, retention, closed-book/no-agent, oral, or research evidence.

Every readiness transition is replayable and tied to evidence refs.

## Candidate evidence and human attestation in v1.2

The v1.2 Tutor Protocol admits Tutor assessments only as **candidate evidence**. Explicit human attestation is separate and preserves assistance/agent provenance. A Tutor cannot declare `MASTERED` authority into existence.

This is the main integration change from the v1.1 introduction: Elite evidence is now part of the live four-Tutor continuity model while keeping the same conservative authority boundary.

## Benchmarks

Benchmarks may record closed-book, oral, no-agent, course-exam, Yau/competition, custom, or other defined contexts. Scores/counts/duration are optional and remain observations under stated conditions rather than forecasts.

Rolling summaries combine only comparable conditions and retain unknown/null data. Gallop does not convert sparse benchmark observations into award probabilities.

## Explicit links

`PREREQUISITE`, `SUPPORTS`, `TRANSFER`, and `RELATED` links carry explicit provenance. Only a prerequisite relation represents a prerequisite gap. Links do not silently mutate curriculum or certify the target.

## Progressive Mentorship integration

`gallop.progression` consumes confirmed evidence/readiness plus explicit targets to derive current capability, training zone, scaffolding, prerequisite focus, next action, gains, mentor role, and research independence.

Those outputs are advisory. The four GPT Tutors can receive them through bounded v1.2 context, but GPT wording or acceptance does not add authority.

## Projections

Readable projections may include Elite Training, Benchmarks, Readiness, Development, North Star, and subject summaries. Raw Journal events, answers, local metadata, response refs, backend sessions, credentials, and integration runtime do not belong in Gallop-Reader.

## Compatibility

Historical V1-only Journals replay to the frozen V1 shape under the exact compatibility fixture. No v1.1/v1.2 source upgrade silently seeds evidence or rewrites historical mastery.

The historical v1.1 RC reports remain audit records of how these semantics were introduced. Current status is documented in [Current Status](current-status.md), [Progressive Mentorship](progressive-mentorship.md), and [v1.2 Tutor Protocol](v1.2-tutor-protocol.md).
