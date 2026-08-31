# DeepTutor Bridge V1

Gallop decides what to train. The existing external DeepTutor adapter prepares
diagnostic questions. No DeepTutor code or Learning Space is restructured.

The four subject policies are data in gallop/schemas/training-policies.json:

| Subject | Preferred training |
| --- | --- |
| Mathematics | Proof, hard problems, counterexamples, definition reconstruction |
| Statistics / Econometrics | Derivation, simulation, DGP reasoning, identification, empirical design |
| Finance | Assumptions, intuition, quantitative problems, empirical evidence, cases, institutions/accounting |
| CS / AI | No-agent coding, algorithms, systems, from-scratch implementation, debugging |

Queue items include stable queue_id, subject, concept, type, P0-P4 priority,
reason, evidence refs, creation date and status. Priority is deterministic:
P0 severe/prerequisite weakness; P1 repeated mistakes or demanding assessment
failure; P2 low confidence; P3 spaced reinforcement; P4 extension.

prepare maps an item into the existing practice-manifest schema. The chain is:

queue_id -> manifest_id -> practice_id -> result_id -> evidence events

The provider's practice ID is retained separately. Default prepare is local:
it writes a human task and an incomplete result template. prepare --send asynchronously submits
DeepTutor's existing deep_question transport with selected context, not a whole
vault, file paths or credentials.

The installed transport produces choice diagnostics. They supplement preparation
but do not count as proof, oral, coding or simulation performance. For those
types, the learner must perform the assigned task and a human must evaluate
actual response references. Gallop does not present choice-question success as
proof completion or allow an LLM score to be the sole truth.

Generation does not start learning. start --confirm is required, and
ingest-result --confirm-human validates the Automation result envelope in
gallop/schemas/automation-result.schema.json. It is a separate boundary from
legacy practice-result JSON: old CLI commands and schemas remain unchanged.
Provider output alone is never an accepted learner result.

The asynchronous bridge records a stable job ID, queue ID, manifest ID and
per-attempt worker/provider PID plus birth time. It redirects stdout/stderr to
private files and closes stdin. The CLI returns immediately; use poll/collect.
The default 240-second deadline does not terminate work. Late results can be
collected from the same attempt, including after the caller exits or crashes.
A result must match the invocation's turn ID and include a completed DeepTutor
terminal event. Never query an unrelated latest result from the provider database.
Retries preserve prior attempts and are refused while work is live or its spawn
outcome is uncertain. A second collection cannot create another prepared event.
OS file locks release automatically on crash; journal replay handles a cache
write interrupted after the event transaction commits.

The automated Golden test uses synthetic results in its isolated namespace.
Such results demonstrate plumbing only and make no claim about a real learner.

Real generation and full isolated Automation acceptance are PASS. The user
supplied and confirmed an actual response; it was recorded conservatively as
non-independent validation, without changing real mastery. No synthetic provider
output or invented response was substituted. See [final gate](automation-final-gate.md).
