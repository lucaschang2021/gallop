# Data flow

## Session → manifest

Only observed concepts, mistakes, weaknesses, open questions, source references,
and requested practice settings should enter a manifest. Empty session fields
remain explicit arrays. Gallop does not infer achievements or completion.

## Manifest → practice engine

The manifest is validated and sent to a practice adapter. `no_agent` and the hint
gradient tell the engine how much assistance is allowed. The complete Vault is
never an implicit input.

## Result → mastery → knowledge store

A structured result records attempts, correctness, hints, timing, engine, and
metadata. The mastery engine produces a reasoned transition. The knowledge
adapter writes both readable Markdown and machine-readable state.

## Review

The knowledge store owns T+1/T+7/T+30 review state. A practice engine executes
due work but cannot silently replace the canonical schedule.

## Logging contract

Operational logs should include `timestamp`, `event`, `subject`, `source`,
`target`, `manifest_id`, `practice_id`, `success`, and `error`. Do not log note
bodies, answers not needed for recovery, credentials, tokens, or cookies.

