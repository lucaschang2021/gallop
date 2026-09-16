# Mastery and capability models

Gallop represents learning state as evidence-backed, replayable state—not as a model opinion or one quiz score.

## Current v1.2 authority model

In v1.2, the append-only Journal is authoritative. Tutor observations and assessments enter as observation/candidate evidence; explicit human attestation is separate. Assistance, agent provenance, task type, timing, transfer, and retention determine what evidence may support mastery/readiness.

Neither GPT output, a target, an Obsidian edit, nor a Reader file can directly promote mastery.

Progressive Mentorship also derives a richer current-capability ladder (`UNKNOWN` through `RESEARCH_USABLE`) for advisory task design. That ladder is related to, but not a silent replacement for, the compatible 0–5 mastery model.

See [Evidence and Mastery Safety Gate](automation-safety.md) and [Progressive Mentorship](progressive-mentorship.md).

## Compatible Automation V1 mastery

Automation V1 uses a conservative 0–5 concept-level model. Its detailed promotion ceilings are maintained in [automation-safety.md](automation-safety.md). Key principles are:

- exposure alone never promotes;
- independent evidence must occur across separate days for higher levels;
- task diversity, delayed retention, transfer, and oral evidence are required at the top end;
- each accepted assessment can raise at most one level;
- failure can lower confidence/add weakness without mechanically erasing established mastery.

## Legacy v0.1 mastery

> **Scope:** `import-result` and the historical offline `demo`. Do not mix this state with Automation/v1.2 state by inference.

| Level | Meaning |
|---:|---|
| 0 | unseen |
| 1 | exposed |
| 2 | basic understanding |
| 3 | guided application |
| 4 | independent application |
| 5 | robust mastery |

The legacy algorithm considers correctness, independence, hints, repetition, delayed recall, transfer, oral explanation, and difficulty. It is deterministic and intentionally conservative.

Distinct committed practice records—not an input claim—supply repetition. Zero hints alone does not prove independence. Easy exercises cannot establish high independent capability. Historical confidence may be uncalibrated/null.

Legacy state remains compatibility data; v1.2 does not silently migrate it into Journal evidence.

## Elite/readiness evidence retained in v1.2

The v1.1 Elite layer introduced explicit assistance, agent provenance, quality, transfer, benchmarks, prerequisite links, and readiness dimensions. Those semantics are retained in v1.2.

Independent evidence requires compatible provenance and actual independent conditions. AI-generated work, solution-seen attempts, or assisted attempts cannot be reclassified as independent merely because the final answer is correct.

Higher readiness requires repeated evidence across days/contexts/task types and, when relevant, novel transfer, delayed retention, oral/closed-book/no-agent evidence, and research components.

## Current capability versus target

An explicit target is a destination, not evidence. The Progressive Mentorship Engine derives current capability only from admitted evidence. Missing evidence remains `UNKNOWN`.

This separation is fundamental: Gallop may keep the target at an elite/research level while adapting the next task to the learner's evidenced frontier.

## Compatibility rule

Historical V1 replay is protected by an exact regression fixture. Any change that would reinterpret old events or persistent mastery semantics requires explicit versioning/migration; a source upgrade does not rewrite the learner's past.
