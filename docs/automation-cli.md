# Automation CLI

All commands join the existing Gallop parser. Place --automation-config FILE
before the subcommand. Paths in the JSON configuration resolve relative to that
file. Automation does not load the legacy .env file.

## Elite Training Protocol commands (v1.1 RC)

```text
gallop --automation-config CONFIG evidence add RECORD --confirm-human
gallop --automation-config CONFIG evidence show [EVIDENCE_ID] [--subject SUBJECT]
gallop --automation-config CONFIG benchmark add RECORD --confirm-human
gallop --automation-config CONFIG benchmark show [BENCHMARK_ID] [--subject SUBJECT]
gallop --automation-config CONFIG readiness [--subject SUBJECT]
gallop --automation-config CONFIG readiness explain DIMENSION --subject SUBJECT
gallop --automation-config CONFIG prerequisite add RECORD
gallop --automation-config CONFIG prerequisite show [LINK_ID]
gallop --automation-config CONFIG target add TARGET
gallop --automation-config CONFIG target show [TARGET_ID]
gallop --automation-config CONFIG mentorship [TARGET_ID]
```

Without `--confirm-human`, evidence remains visible but cannot establish
independent performance. `prepare` and `submit` accept optional `--elite-policy
FILE`; it requests conditions and never reports actual performance.

`mentorship` reports current capability, explicit target, training zone,
recommended task design, scaffolding, deterministic action, prerequisite gaps,
struggle records, capability gains, mentor role and research independence. It
also states `scheduler_changed: false`.

| Command | Behavior |
| --- | --- |
| intake FILE | Validate truthful v1 input, retain raw bytes, append session and transitions, refresh queue |
| queue | Refresh deterministic candidates and list every status |
| prepare QUEUE_ID | Create manifest and human task; mark ready, never started |
| prepare QUEUE_ID --send | Submit a durable DeepTutor job; return its ID, not ready training |
| submit QUEUE_ID --questions N | Submit diagnostics (default 7; use 1 for minimal validation) |
| poll JOB_ID | Show lifecycle, elapsed time, timeout reason and process status without answer keys |
| collect JOB_ID | Recover correlated output and mark preparation ready; replay is idempotent |
| submit QUEUE_ID --questions N --retry | Retry a proven stopped failed attempt; never overlap live/uncertain work |
| start QUEUE_ID --confirm | Explicit learner start; enter in_progress |
| cancel QUEUE_ID | Cancel unfinished work without mastery evidence |
| retry QUEUE_ID | Put failed preparation back in queued |
| ingest-result FILE --confirm-human | Validate linked actual performance and human grading |
| status | Namespace, event/session/concept counts and training statuses |
| publish --dry-run | Verify existing Reader target and preview filtering without changing notes |
| publish | Refresh owned projections and invoke the existing Reader exporter |
| cycle | Process pending intake, replay, refresh queue/views, publish; never start/complete training |
| rebuild-state | Back up derived state, verify/replay, compare, atomically replace or fail closed |
| explain CONCEPT --subject SUBJECT | Mastery, confidence, reasons, mistakes, evidence refs and next work |

Statuses: queued, ready, in_progress, completed, failed, cancelled. Completed
means the learner attempted and a human assessed the task, not necessarily a
successful answer or mastered concept. An ungraded/ambiguous result remains raw
and does not mark completion. Research judgement stays with a human.

The prepared directory contains manifest.json, practice.json,
instructor.answer-key.json and result-template.json. The answer key is private,
not a learner response and never a grading authority. Fill the result template
from actual activity; do not convert unknown values into invented scores.

Automation errors return a nonzero exit status without printing private input
or provider stderr. Correct the source and retry; event IDs preserve idempotency.
Existing demo, sync-session, manifest, generate, import-result, live-demo and
mobile-export commands remain supported.

Job completion means generated material is available. It is distinct from training
completion. Logs, manifests, provider IDs and instructor answers stay under the
private root/jobs directory, outside Obsidian and cloud export. A timeout is a
soft caller deadline (240 seconds), not permission to submit a duplicate.
