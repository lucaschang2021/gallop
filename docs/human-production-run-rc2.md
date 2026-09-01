# RC2 Human Production Run procedure

Automated RC2 PASS is not Human E2E PASS. Run this only after reviewing and
committing the candidate, with the existing learner configuration and verified
Reader binding.

1. Record one real lesson through Tutor Protocol v1. Optional mentorship data
   may state an explicit target, but must not claim current capability.
2. Confirm Gallop ingests the session and shows the target separately from an
   evidence-backed current capability.
3. Review the recommended zone and scaffold. The learner decides whether to
   accept the task; Gallop does not auto-start it.
4. Prepare or submit the existing queue item and open it in the real DeepTutor
   UI. A manifest request is not performance telemetry.
5. The learner completes the work and records actual hints, agent use, zone,
   designed scaffold, response refs and assessment context.
6. A human reviews the response and explicitly confirms ingestion. Do not mark
   independent performance merely because code runs or an answer is correct.
7. Verify the immutable evidence, mastery transition, readiness and mentorship
   decision. Check that one success fades at most one scaffold level.
8. Project and publish through the existing one-way Reader path. Verify
   `Development.md` and `North Star.md` while keeping raw events and answers out.
9. On a later day, perform transfer and delayed closed-book retention checks
   before expecting higher progression.

Record command outputs, event IDs, timings and screenshots as private acceptance
evidence. Do not add real learner work, local paths or DeepTutor private state to
the public repository. Human E2E is PASS only after all nine steps occur with
real learner work.
