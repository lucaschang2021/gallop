# DeepTutor Bridge — legacy optional adapter

> **Current v1.2 role:** DeepTutor is a compatibility adapter, not part of the Zero-Touch critical path. Normal daily learning uses the four subject-bound GPT Tutor MCP surfaces and the Journal-backed Tutor Bridge. This document remains the technical reference for explicit legacy DeepTutor generation.

Gallop decides what to train. The external DeepTutor adapter can prepare diagnostic questions for the compatible Automation V1 queue without owning mastery, readiness, progression, or Tutor continuity.

The four subject policies are data in `gallop/schemas/training-policies.json`:

| Subject | Preferred training |
| --- | --- |
| Mathematics | Proof, hard problems, counterexamples, definition reconstruction |
| Statistics / Econometrics | Derivation, simulation, DGP reasoning, identification, empirical design |
| Finance | Assumptions, intuition, quantitative problems, empirical evidence, cases, institutions/accounting |
| CS / AI | No-agent coding, algorithms, systems, from-scratch implementation, debugging |

## Automation V1 queue boundary

Queue items include stable `queue_id`, subject, concept, type, P0-P4 priority, reason, evidence refs, creation date, and status. Priority is deterministic:

- P0: severe/prerequisite weakness;
- P1: repeated mistakes or demanding-assessment failure;
- P2: low confidence;
- P3: spaced reinforcement;
- P4: extension.

`prepare` maps an item into the compatible practice-manifest schema:

```text
queue_id -> manifest_id -> practice_id -> result_id -> evidence events
```

Default preparation is local and writes a human task plus an incomplete result template. `prepare --send` explicitly submits the selected context to the separately installed DeepTutor runtime. It does not send a whole Vault, Journal, local paths, or Gallop credentials by implication.

## Evidence authority

Generated questions are **provider output**, not learner evidence. Generation does not start learning, complete a task, or raise mastery.

Choice diagnostics cannot substitute for proof, oral, coding, simulation, or research performance. The learner must perform the assigned work; an explicit human-confirmed assessment is required before Automation V1 can admit the result through its evidence gate.

The v1.2 Tutor path has a stronger explicit distinction: Tutor assessments are candidate evidence and human attestation is separate. DeepTutor output never bypasses that model.

## Durable submit / poll / collect

The asynchronous bridge records a stable job ID, queue ID, manifest ID, and per-attempt process/provider identity. stdout/stderr are redirected to private runtime files and stdin is closed. The CLI returns immediately; callers use `poll` and `collect`.

The default caller deadline does not prove provider termination. Late output can be collected from the same attempt. A result must match the invocation correlation data and completed provider terminal event. Gallop never recovers by taking an unrelated provider "latest result".

Retries preserve prior attempts and are refused while work is live or spawn ownership is uncertain. A second collection cannot create another prepared event. Journal replay recovers application state without resubmitting provider work after a committed event.

Provider exactly-once execution is not claimed across an indeterminate OS spawn failure.

## Privacy

DeepTutor model/provider credentials and account state stay in the external runtime. Gallop stores job metadata and generated material under private runtime storage; answer keys, logs, provider IDs, and raw output do not belong in Gallop-Reader.

## Historical acceptance

The v1.0 Automation acceptance exercised a real DeepTutor generation/collection and a user-confirmed isolated response while preserving real mastery. That remains historical transport evidence, not a current provider-health guarantee. See [Automation V1 final gate](automation-final-gate.md).

The current v1.2 acceptance is the separate [four-Tutor real dogfood record](audits/v1.2-real-dogfood-acceptance.md); it does **not** require DeepTutor.
