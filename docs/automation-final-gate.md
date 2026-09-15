# Automation V1 final gate — historical acceptance record

> **Historical status:** this record documents the v1.0.0 Automation/DeepTutor acceptance completed before the v1.2 Zero-Touch architecture. It remains compatibility evidence. Current acceptance is the [v1.2 real four-Tutor dogfood record](audits/v1.2-real-dogfood-acceptance.md).

Original gate status: **PASS** (real online DeepTutor output and user-confirmed isolated response).

Online DeepTutor output and Gallop collection succeeded with the configured provider/model. One isolated question was generated without retrieval tools or embedding. Submission took 0.09 seconds, the result arrived at 41.10 seconds and the process exited normally at 44.93 seconds. Queue, manifest, job and provider turn were correlated; the generated practice was recovered into Gallop.

The earlier 240-second attempt did not preserve stage output. Its exact stall cannot be reconstructed honestly. The confirmed bridge defect was synchronous waiting with no durable job tracking and a generic error that discarded timing/output context. Durable submit/poll/collect addressed that recovery/observability class; the record did not claim a reconstructed historical provider/network cause.

Prepared → submitted → running → completed / failed / timed_out was retained through per-attempt records. Late collection, duplicate safety, retry refusal for active/uncertain jobs, process identity and crash recovery were covered by regression tests. No provider credentials were copied into the repository.

The user supplied an actual free-response explanation and explicitly confirmed its use only for isolated validation. The record did not claim a separate examiner or independent performance because a worked choice was already visible. One practice and one assessment event were accepted, three state transitions replayed, and the completed exercise projected to the isolated Obsidian Vault. Duplicate import/collection and repeated cycle were idempotent.

Historical regression result: **177/177 tests passed**. Main Vault: 56/56 historical hashes unchanged. Real mastery unchanged. The isolated validation did not become general proof/oral/coding evidence.

## Relationship to v1.2

v1.2 retains the durable DeepTutor adapter only as optional legacy compatibility. Normal learner continuity now uses four subject-bound GPT Tutor MCP servers, incremental Journal checkpoints, bounded context, fresh-chat restoration, Progressive Mentorship, owned Obsidian projections, and Gallop-Reader publication.

The v1.0 acceptance therefore demonstrates historical transport/writeback reliability; it is **not** a current provider-health check and is not the current learner workflow.

Source/package state, GitHub Release/tag state, and current real dogfood are tracked separately in [Current Status](current-status.md).
