# Architecture

[Home](../README.en.md) · [Current status](current-status.md) · [Quickstart](quickstart.md)

Gallop is a Python CLI connecting structured tutor records, local learning
evidence, human practice, and readable notes. This document maps responsibilities
and storage ownership; command syntax lives in the [CLI reference](automation-cli.md).

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

That PASS is historical v1.0.0 acceptance, not a live health indicator or a
guarantee for another user's provider, vault, or cloud setup. See the dated
[status snapshot](current-status.md).

## Module responsibilities

| Area | Responsibility |
|---|---|
| `gallop/cli.py`, `automation/cli.py` | Public command parsing and explicit configuration |
| `automation/protocol.py`, `schemas/` | Validate intake/results; retain truthful empty or unknown data |
| `automation/store.py` | SQLite raw inputs, append-only events, stable IDs, hash chain, transactions |
| `automation/state.py` | Replay evidence, apply mastery rules, select training candidates |
| `schemas/training-policies.json` | Four supported subject policies |
| `automation/service.py` | Coordinate intake, preparation, human confirmation, projection and replay |
| `automation/jobs.py`, `adapters/deeptutor/` | Explicit external generation, durable job lifecycle and collection |
| `automation/views.py` | Derive Markdown; preserve user text outside managed regions |
| `mobile.py`, `mobile_icloud.py` | Filtered one-way Reader export and optional existing cloud-binding checks |
| `core/`, `adapters/obsidian/` | Compatible legacy session/practice/mastery pipeline |

Paths in this table are relative to `gallop/` unless already prefixed with it.

## Storage ownership

| Storage | Role | Recovery / privacy boundary |
|---|---|---|
| Automation root: `events.sqlite3` | Raw input bytes and authoritative new Automation events | Keep private and outside cloud storage; replay verifies evidence and transitions |
| `derived-state.json` | Cached state with journal cursor and hash | Rebuild from verified journal; never seed by editing the cache |
| `prepared/`, `jobs/` | Manifests, human task/result templates, private provider records and answer keys | Not learner results; excluded from Reader |
| Obsidian Vault | Human-readable projections and user notes | Only owned regions updated; conflicts fail closed |
| Gallop-Reader and export receipt | Filtered reading mirror plus local ownership/backups | One-way publication; no phone-to-main merge or atomic cloud transaction |

For `integration_tests`, vault, Reader and export state stay inside the isolated
root. For `learner`, the root must be outside the existing Obsidian vault and
Reader. Publishing requires the existing verified Reader binding; the example
preview does not provision a real cloud setup. See [mobile export](mobile-export.md).

## Two compatible but separate workflows

| | Automation V1 | Legacy v0.1 commands |
|---|---|---|
| Entry | `intake`, `queue`, `prepare`, `ingest-result`, `cycle` | `sync-session`, `manifest`, `generate`, `import-result`, `demo` |
| Configuration | Explicit `--automation-config FILE`, paths relative to that file | `.env` / environment and command options |
| State | Event journal plus replayed derived state | Vault-local `.gallop/mastery.json` plus Markdown |
| Mastery | [Automation safety rules](automation-safety.md); exposure does not promote | [Legacy rules](mastery-model.md); synthetic demo can show 1 → 2 |
| Migration | No implicit ingestion of historical legacy state | Preserved for compatibility |

The old five-layer Teacher / Knowledge / Practice / Mastery / Integration model
still describes responsibilities. Automation adds explicit event authority;
do not treat Markdown or a legacy score as new Automation evidence.

## Trust and extension boundaries

Tutor text and provider output are untrusted data, not commands or proof of
mastery. Human assessment remains an explicit local attestation, not proctoring.
SQLite triggers and hashes detect accidental corruption, not a hostile owner.
No daemon, UI, autonomous grader, or built-in semantic retrieval is shipped.

Extend subject policies, schemas and focused adapters with rejection cases and
synthetic fixtures. Changes to replay rules or persistent formats need explicit
versioning and migration design; never silently reinterpret old evidence.
