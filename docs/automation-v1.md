# Automation V1 — compatible event/CLI subsystem

> **Current v1.2 daily-use path:** learners interact with the four subject-bound GPT Tutors. Gallop runs underneath through the Tutor Bridge and Journal. Automation V1 remains a supported event/CLI subsystem for explicit queue operations, compatibility, diagnostics, and legacy integrations; it is not the required learner-facing workflow.

Automation V1 automates learning operations, not learning itself. It has no autonomous learner, automatic completion, or hidden mastery promotion.

## Authority and compatibility

For Automation inputs, the append-only Journal is authoritative. Learning state, queues, prepared artifacts, and Markdown are derived. The legacy v0.1 `sync-session` / `import-result` path remains separate and is not silently migrated.

The v1.2 Tutor Bridge writes into the same authority model while adding per-event identity, incremental checkpointing, bounded context, and fresh-chat continuity. Automation V1 batch intake remains compatible through [Tutor Output Protocol v1](tutor-protocol.md).

## Isolated example

The public example stays entirely inside `automation-runtime` and uses synthetic evidence:

```bash
python -m gallop --automation-config examples/automation/config.json intake examples/automation/session.json
python -m gallop --automation-config examples/automation/config.json queue
python -m gallop --automation-config examples/automation/config.json cycle
```

The example Reader is a local preview. It must not target the real learner Vault, real Reader, or cloud binding.

## Explicit Automation workflow

For users/developers who intentionally use the CLI path:

1. `intake` a truthful Tutor v1 package or explicitly process a compatible pending file.
2. Inspect `queue` / `explain`.
3. `prepare QUEUE_ID` creates a stable task and incomplete result template.
4. Optionally use the legacy DeepTutor path with `prepare --send`, then `poll` / `collect` the same durable job.
5. `start QUEUE_ID --confirm` only when the learner actually starts.
6. Record real work and an explicit human-confirmed assessment.
7. `ingest-result FILE --confirm-human` admits the result through deterministic evidence/mastery rules.
8. `cycle` refreshes derived views and, when configured, publishes through the existing Reader exporter.

This workflow is compatible with v1.2 evidence authority. It does not supersede the primary Tutor MCP path.

## Idempotency and recovery

Raw intake bytes are retained. Same session identity/content is idempotent; conflicting reuse fails. Results bind to queue/manifest/practice/subject/concept and cannot recount already accepted work by changing only the result ID.

SQLite transactions commit authoritative events before derived-state replacement. A stale/corrupt cache can be rebuilt from a verified Journal prefix. Managed projection conflicts fail closed rather than overwriting learner-owned text.

Each projection file write is atomic, but Journal + all Markdown + iCloud are not one distributed transaction. After an I/O/cloud failure, retry projection/publication from the committed Journal.

## Legacy DeepTutor jobs

DeepTutor is optional and off the v1.2 critical path. Automation V1 retains durable `submitted/running/completed/failed/timed_out` job state for explicit external diagnostic generation.

A caller deadline is not proof the provider stopped. Late results may be collected from the same attempt. Retry is allowed only when prior work is proven stopped; uncertain spawn ownership fails closed. Repeated collection/recovery must not resubmit provider work or create duplicate learner evidence.

See [DeepTutor legacy adapter](deeptutor-integration.md).

## Evidence boundary

Human confirmation is a local attestation, not proctoring. Tutor/model/provider output is not verified learner performance. Assistance, hint usage, and agent provenance constrain independence. Synthetic/integration activity cannot become learner evidence.

## Real learner runtime

The primary v1.2 learner setup uses an existing Obsidian Vault, private Journal root outside cloud storage, existing validated Gallop-Reader binding, and four subject-bound Tutor MCP server entries. See [Quickstart](quickstart.md) and [Real Tutor Integration](v1.2-real-tutor-integration.md).

## Compatibility guarantee

The frozen V1 replay fixture remains exact. Changes to historical event meaning or mastery semantics require an explicit migration; source upgrades never silently reinterpret old evidence.
