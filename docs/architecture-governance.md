# Architecture Governance

`ARCHITECTURE.toml` is the executable contract for Gallop's maintained v1.2 architecture.

The protected chain is:

> **Tutor observations / human evidence → append-only Journal → deterministic replay → domain decisions → application orchestration → projections / external adapters**

The product boundary is:

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

Gallop is headless. Four subject-bound GPT Tutor conversations are the primary learner-facing surface in v1.2. The Zero-Touch Tutor Runtime Bridge, bounded context builder, fresh-chat restoration, incremental checkpoints, and owned projections are implemented and have passed controlled real dogfood. RC2 is now a historical governance milestone, not the current product state.

## Authority model

The Journal is authoritative. `derived-state.json`, prepared artifacts, Tutor directives, Obsidian Markdown, and Gallop-Reader are derived or transport data. Editing a projection cannot create an authoritative learning transition.

| Authority class | Meaning | Direct mastery authority? |
|---|---|---|
| Tutor observation | Exposure, mistake, question, attempt, feedback | No |
| Tutor candidate assessment | Tutor-proposed evaluation tied to evidence | No |
| Human attestation | Explicit confirmation of a concrete learner event/result | Only through the applicable evidence/mastery gate |
| Verified independent evidence | Confirmed evidence satisfying assistance/provenance constraints | Only through deterministic policy |
| Provider output | Generated practice/material from an optional external provider | No |
| System-derived state | Replay, queue, readiness, mentorship, directive, projection | No; derived only |

Prepared work is not completed work. Correct output is not automatically independent evidence. AI-generated code is not independent coding evidence. A target never raises current capability.

## Layer responsibilities

| Layer | Owns | Must not own |
|---|---|---|
| Tutor transport (`gallop/tutor/mcp.py`) | Subject-bound MCP surface, tool metadata, server binding | Cross-subject authority, hidden model calls, mastery policy |
| Tutor protocol / bridge (`gallop/tutor/`) | Event validation, stable identity, Journal admission, bounded context, restore | Silent transcript authority, direct mastery promotion |
| Domain (`gallop/progression`) | Pure capability/zone/scaffolding/prerequisite/struggle/gain/mentor decisions | Filesystem, network, adapters, implicit current time |
| Application (`gallop/automation`) | Locks, workflow coordination, Journal operations, replay, queues, projections, legacy jobs | New domain formulas embedded in orchestration |
| Persistence / Journal | Transactions, append-only semantics, hashes, idempotency/conflicts | Learning-policy decisions |
| Projections | Human-readable rendering and Reader publication | Authoritative state mutation |
| Adapters | Optional DeepTutor, legacy Obsidian adapter, external boundaries | Assessment authority or reducer mutation |
| CLI | Explicit developer/legacy operations | Hidden curriculum decisions |
| Schemas / policy catalogs | Versioned contracts and policy parameters | Runtime authority |

## Four-Tutor isolation

The four permanent surfaces are Mathematics, Statistics & Econometrics, Finance, and CS & AI. Subject and Tutor identity are bound at server launch. A call whose event subject, Tutor ID, or recorder conflicts with that binding must fail before the Journal is opened for mutation.

All four Tutors share the same Journal/application/evidence model. They are policies over one Gallop system, not four separate backends.

## Fresh-chat continuity

A fresh Tutor conversation may recover bounded context only from committed Journal state and explicit stable identity. The old transcript, model memory, or an Obsidian note is not a source of authority. Restore failure returns no fabricated context; already committed evidence remains recoverable.

## Progressive Mentorship boundary

`gallop.progression` is deterministic and advisory. It consumes explicit replayed evidence, targets, policy, and time inputs. It has no EventStore, filesystem, provider, Obsidian, CLI, subprocess, network, environment, or implicit clock dependency.

The target ceiling stays fixed. Current capability is evidence-derived. Training difficulty adapts, assistance fades conservatively, prerequisite repair is explicit, and research independence is earned through evidence. Mentorship does not silently mutate the queue.

## Legacy boundaries

DeepTutor is `LEGACY`, `OPTIONAL`, and `NON-AUTHORITATIVE`. It remains available for compatibility and explicit diagnostic generation, but v1.2 has zero required DeepTutor runtime dependency in the primary Tutor workflow.

Automation V1 and v0.1 commands remain supported compatibility paths. Historical V1 state is never silently migrated or reinterpreted; the frozen V1 replay fixture remains an exact compatibility oracle.

## Time and side effects

Domain decisions receive timestamps/dates explicitly. Application code may acquire current time for a new event, records it, and replay never asks the wall clock again. Importing `gallop` must not create state, write a Vault, launch a provider, append an event, or start a process.

`Automation.open()` remains the explicit composition root for the Automation path. Tutor server startup binds validated paths and subject identity; read-only status checks must not initialize learner state.

## Projection governance

Journal commits precede projection refresh. If projection fails, the committed event remains authoritative and recovery retries projection from Journal state. Gallop-owned Markdown regions fail closed on ownership conflicts. Reader publication is one-way and filtered; phone edits never flow back into Journal authority.

## Architecture Gate

Run:

```bash
python scripts/check_architecture.py
```

The report contains `existing`, `introduced`, `resolved`, and soft warnings. CI fails on invalid contract or introduced hard violations. Soft-size warnings require responsibility review; file size alone does not authorize arbitrary splitting.

The gate protects dependency direction, pure-domain behavior, explicit time, policy validity, adapter/reducer separation, projection authority, governed-file responsibility, and V1 compatibility constraints.

## Governance change rule

Any change to authority, replay semantics, persistent event meaning, Tutor subject isolation, Reader direction, or evidence classification requires an explicit design/migration review. Feature work must not obtain authority by bypassing the Journal, repurposing a projection, or treating model output as human evidence.
