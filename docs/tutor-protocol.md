# Tutor Output Protocol v1

A tutor session is an observation record. Record what actually occurred and
never invent scores, completed work, mastery, confidence or research output.

Automation intake is compatible with the existing lesson-sync protocol:
tutor, title, occurred_at and summary are required; schema_version is 1.0.
Provide a stable session_id in normal use. If omitted, a deterministic ID is
derived from normalized content. Tutor is exactly mathematics, statistics,
finance or cs-ai. occurred_at must include a timezone and cannot be in the future.

The supported arrays are concepts, proofs_derivations, hard_problem_sessions,
oral_exams, simulation_labs, mistakes, weakness_tags, open_questions, connections,
research_ideas and artifacts. Empty arrays are valid. Omitted optional arrays
normalize to empty without fabricating content. Concepts support either strings
or objects with a name; original definitions and extension fields are retained.

Use UTF-8 JSON, or one fenced JSON block with no other text. Write a .tmp file,
close it, then atomically rename to .json/.md before intake or pending delivery.
Malformed JSON, duplicate JSON keys, wrong tutor, invalid timestamps and schema
violations are rejected. Raw bytes remain separate from validated events.

Same session_id and normalized content is idempotent. Same ID with changed
content fails; a correction must use a new ID and explain the relationship.
Historical sessions are never overwritten. Tutor claims are not executed or
used as proof of human performance.

Automation's normative intake boundary is
gallop/schemas/tutor-intake.schema.json. The original
gallop/schemas/session.schema.json remains the strict legacy string-concept
protocol for sync-session/manifest and is not changed by Automation.

See the entirely synthetic [example](../examples/automation/session.json).
