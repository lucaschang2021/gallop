# Architecture

Automation V1 adds a local event-driven path beside the compatible legacy
adapters. It changes the authority model for new Automation inputs only.

~~~mermaid
flowchart TD
    T[Tutor v1 package] --> I[Validated intake]
    I --> E[(Append-only event journal + raw bytes)]
    E --> S[Deterministic learning state]
    S --> Q[Four-subject training queue]
    Q --> M[Stable manifest]
    M --> D[Existing DeepTutor preparation]
    D --> H[Human start, actual work, human assessment]
    H --> R[Validated practice + assessment events]
    R --> E
    S --> V[Owned Obsidian projections]
    V --> P[Existing filtered mobile export]
    P --> G[Gallop-Reader]
    E --> A[Replay, explain, provenance]
~~~

## Boundaries

- Tutor observations are data, not tool commands or verified mastery.
- Raw inputs live separately from validated session, practice, assessment and
  state_transition events. Queue lifecycle and preparation also have events.
- SQLite transactions and append-only triggers protect journal batches.
  Every event has a stable ID, timestamp, source, namespace and hash-chain link.
- Derived state carries its journal cursor and head hash. Replay verifies every
  transition against its causal evidence, not just a final number.
- A local operation lock serializes state and projection changes. Provider calls
  are explicitly requested and never performed by cycle.
- Markdown projections update only owned regions. Their receipt detects manual
  changes; I/O interruption can be retried without replacing user notes.
- The existing DeepTutor and mobile-export adapters remain the integration
  boundaries. Old commands and their historical state are not migrated implicitly.

The state rules, policy data, application service, store, views and CLI live in
separate small modules under gallop/automation. There is no daemon, extra web
framework, LLM grader, swarm, or retrieval platform in V1.

See [Automation workflow](automation-v1.md), [safety](automation-safety.md),
[CLI](automation-cli.md), and [DeepTutor bridge](deeptutor-integration.md).

DeepTutor preparation now uses durable submit/poll/collect jobs. The caller does
not hold the journal lock while waiting on a provider. Final acceptance is
**PASS**: a real generated task and user-confirmed response completed collection,
practice/assessment events, isolated state transitions and Obsidian projection.
The actual learner journal and mastery remain untouched.
