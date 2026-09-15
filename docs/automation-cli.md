# Automation CLI

The Automation CLI remains a supported **developer, compatibility, inspection, and legacy operations surface** in Gallop v1.2. It is not the primary learner-facing interface: normal v1.2 learning happens in the four subject-bound GPT Tutor conversations through the local MCP bridge.

All Automation commands join the existing Gallop parser. Place `--automation-config FILE` before the subcommand. Paths in the JSON configuration resolve relative to that file. Automation does not load the legacy `.env` file.

## v1.2 Tutor runtime vs Automation CLI

| Surface | Primary purpose | Learner-facing? |
|---|---|---|
| subject-bound Tutor MCP | normal v1.2 teaching, continuity, events, checkpoints, context | **Yes — through GPT Tutor dialogue** |
| Automation CLI | inspect/replay/test/manage journal-backed Automation state and compatibility workflows | No, developer/operator surface |
| legacy v0.1 CLI | backward compatibility and old pipeline validation | No |
| optional DeepTutor jobs | explicit external diagnostic generation | No; generated material is not learner evidence |

The CLI and Tutor runtime share Gallop authority principles: Journal-backed state, conservative evidence, explicit identity, deterministic replay, and no automatic promotion from generated material.

## Evidence / Progressive Mentorship commands

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

Without the required authority confirmation, evidence cannot establish independent performance merely because it is present. `mentorship` reports current capability, explicit target, training zone, task-design guidance, scaffolding, prerequisite gaps, productive struggle, gains, mentor role, and research-independence signals. Mentorship remains advisory and does not silently replace the scheduler.

## Automation commands

| Command | Behavior |
|---|---|
| `intake FILE` | Validate truthful V1 input, retain raw bytes, append session/transitions, refresh queue |
| `queue` | Refresh deterministic candidates and list every status |
| `prepare QUEUE_ID` | Create local manifest/human task; mark ready, never started |
| `prepare QUEUE_ID --send` | Submit an optional durable DeepTutor job; generated material is not learner performance |
| `submit QUEUE_ID --questions N` | Submit optional diagnostics |
| `poll JOB_ID` | Inspect provider-job lifecycle without exposing private answer material |
| `collect JOB_ID` | Recover correlated provider output; collection is idempotent |
| `submit QUEUE_ID --questions N --retry` | Retry only a proven stopped/failed attempt; never overlap live/uncertain work |
| `start QUEUE_ID --confirm` | Explicitly record that the learner started the task |
| `cancel QUEUE_ID` | Cancel unfinished work without mastery evidence |
| `retry QUEUE_ID` | Move failed preparation back to queued |
| `ingest-result FILE --confirm-human` | Validate linked observed performance and configured human assessment |
| `status` | Show namespace/event/session/concept counts and training statuses |
| `publish --dry-run` | Verify existing Reader target and preview filtering without mutation |
| `publish` | Refresh owned projections and invoke existing Reader export |
| `cycle` | Process pending Automation work/replay/views/publication; never fabricate training completion |
| `rebuild-state` | Back up derived state, verify/replay, compare, atomically replace or fail closed |
| `explain CONCEPT --subject SUBJECT` | Show mastery/confidence reasons, mistakes, evidence refs, and next work |

Statuses remain `queued`, `ready`, `in_progress`, `completed`, `failed`, and `cancelled`. `completed` means an actual task was attempted and the configured assessment boundary was satisfied; it does not necessarily mean success or mastery.

## v1.2 Tutor MCP tool surface

The Tutor MCP is intentionally not replicated as ordinary learner CLI commands. Each subject-bound server exposes a small tool set to the Tutor host:

- `get_runtime_status`
- `open_or_resume_session`
- `get_learning_context`
- `record_learning_event`
- `checkpoint_session`
- `finalize_session`
- `get_session`

Read operations are marked read-only in MCP metadata. Write operations validate subject/Tutor identity and append durable Journal events before projection refresh.

## Prepared/private material

The legacy Automation prepared/job directories can contain manifests, provider IDs, answer keys, result templates, and provider outputs. They are private operational data, not learner mastery evidence, and must remain outside Reader/cloud publication.

Never invent missing scores, assistance state, authorship, or assessment outcomes just to make an import pass.

## DeepTutor compatibility

DeepTutor is optional in v1.2. If used, submit/poll/collect remains durable and explicit. A timeout is a soft caller deadline, not proof that the provider job stopped and not permission to submit a duplicate uncertain job.

Job completion means generated material became available. It is distinct from training completion, independent evidence, and mastery.

## Errors and retries

Automation errors return nonzero exit status and should avoid printing private input/provider stderr. Stable event/job IDs provide replay/idempotency boundaries. Correct the source condition and retry the same identity when appropriate; do not create a new identity to escape a conflict or uncertainty.

## Legacy commands

`demo`, `sync-session`, `manifest`, `generate`, `import-result`, `live-demo`, and related v0.1 paths remain supported separately. Their state/mastery model is not silently migrated into v1.2 authority state.

For normal learning, prefer the Four-Tutor v1.2 path described in [Quickstart](quickstart.md), [Tutor Protocol](v1.2-tutor-protocol.md), and [Real Tutor Integration](v1.2-real-tutor-integration.md).