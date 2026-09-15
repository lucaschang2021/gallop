# RC2 Human Production Run — historical procedure

> **Superseded acceptance status:** RC2 originally required a later human production run. Gallop v1.2 has since completed controlled real learner dogfood across all four subject-bound Tutors, including fresh-chat restoration, incremental checkpoints, abrupt-close recovery, duplicate recovery, owned Obsidian projection, and learner-confirmed Reader visibility. See the [v1.2 real dogfood acceptance](audits/v1.2-real-dogfood-acceptance.md).

This file is retained to document the earlier RC2 acceptance procedure and the governance intent behind it. It is not the current daily-use checklist.

## Historical RC2 procedure

1. Record one real lesson through Tutor Protocol v1. Optional mentorship data may state an explicit target but must not claim current capability.
2. Confirm Gallop ingests the session and keeps target separate from evidence-backed current capability.
3. Review recommended zone/scaffold; learner decides whether to accept work.
4. Prepare/submit the existing queue item; provider request is not performance telemetry.
5. Learner completes real work and records actual hints, agent use, zone, designed scaffold, response refs, and assessment context.
6. Human reviews the response and explicitly confirms ingestion. Correctness alone does not establish independence.
7. Verify immutable evidence, mastery transition, readiness, and mentorship decision; one success fades at most one scaffold level.
8. Project/publish through the one-way Reader path while keeping raw events and answers private.
9. On a later day, perform transfer and delayed closed-book retention checks before expecting higher progression.

At RC2, completing all nine steps was the intended Human E2E boundary.

## Current v1.2 procedure

Normal real use now happens through the corresponding subject-bound GPT Tutor MCP surface:

`open/resume → bounded Journal context → incremental learning events/checkpoints → candidate assessment/human attestation → deterministic replay/mentorship → owned Obsidian projection → one-way Reader publication`.

The real dogfood acceptance record is authoritative for what was actually exercised. Historical RC2 steps remain useful background but should not be cited as an outstanding blocker.
