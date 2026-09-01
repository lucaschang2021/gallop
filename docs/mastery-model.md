# Mastery model

> **Scope: legacy v0.1 pipeline** (`import-result` and the offline `demo`).
> Automation V1 has a separate [Mastery Safety Gate](automation-safety.md):
> course exposure never promotes mastery, confidence is explicit, and failure
> does not mechanically reset an established level. Do not mix the two models.

Gallop represents mastery as evidence-backed state, not a quiz score.

| Level | Meaning |
|---:|---|
| 0 | unseen |
| 1 | exposed |
| 2 | basic understanding |
| 3 | guided application |
| 4 | independent application |
| 5 | robust mastery |

## Evidence considered

1. correctness;
2. independent completion;
3. hint usage;
4. repeated performance;
5. delayed recall;
6. transfer problems;
7. oral explanation;
8. difficulty.

## Safety rules

- No attempt means no transition.
- Weak evidence may lower an overconfident state.
- Guided success can establish basic or guided application.
- One excellent quiz cannot produce level 5.
- Level 5 requires repeated independent performance plus delayed recall,
  transfer, and oral evidence.

The v0.1 algorithm is intentionally conservative and deterministic. Future
versions may improve calibration without changing the protocol's evidence model.

The import pipeline counts repeated success from distinct committed practice
records, not an input claim. Independence defaults to unknown/false; zero hints
alone does not prove independent completion. Easy exercises cannot establish
independent application. Confidence is persisted as null (uncalibrated).
Delayed, transfer and oral flags remain explicit observer-supplied evidence;
Gallop cannot verify a person's behavior or the truth of self-reported results.

## Elite safety gate (v1.1)

Only confirmed, passing, independently performed evidence with zero hints,
recorded agent provenance, response references, explicit assessment context and
distinct attempt/context IDs can enter the Elite gate. Proofs and derivations
also require recorded quality dimensions. Benchmark evidence requires explicit
closed-book and no-AI conditions. Duplicate attempts count once; assistance
disclosed for the same attempt disqualifies it.

Progression requires repeated days, contexts and task types. Higher levels also
require explicit novel transfer, a linked verified benchmark and delayed oral
evidence. One event raises at most one level. Failures add weakness and lower
confidence without mechanically erasing prior mastery. A benchmark record alone
never changes mastery.
