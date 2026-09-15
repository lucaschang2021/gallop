# Evidence and Mastery Safety Gate

Gallop's state/evidence engines are deterministic. No imported summary, compliment, target, model grading number, Tutor claim, provider output, or Markdown edit may directly promote a learner.

v1.2 adds an explicit authority split around the existing conservative mastery rules:

- Tutor observations describe what happened.
- Tutor assessments are **candidate evidence**.
- Human attestation is a separate explicit confirmation boundary.
- Confirmed evidence is still subject to assistance, agent provenance, task, timing, and mastery rules.
- Derived state/directives/projections never become evidence merely because Gallop produced them.

## Core mastery transition rules

For the compatible Automation mastery model:

| Evidence available | Maximum eligible level |
| --- | --- |
| Exposure, praise, one attempt, hints only, or one day | No promotion |
| Independent success on at least 2 separate days | 2 |
| At least 3 days and 2 task types | 3 |
| At least 4 days and 3 task types | 4 |
| At least 5 days, 3 types, a 30-day span, oral evidence and transfer | 5 |

Every accepted assessment can increase at most one level even when a higher ceiling is eligible. Passing requires at least 80% human-confirmed success in the compatible Automation rule set. Hinted/dependent work does not count toward independent thresholds.

Failure increases mistake/weakness evidence and can lower confidence, but it does not mechanically erase established mastery. Confidence and mastery are separate; low confidence can coexist with a previously established level.

## v1.2 candidate evidence

Tutor-originated `candidate_assessment` or equivalent evidence is not a human attestation. A valid confirmation must refer to the concrete candidate/attempt and preserve its assistance/provenance facts.

Contradictory disclosures fail closed. Examples:

- nonzero assistance cannot be relabelled `INDEPENDENT`;
- AI-generated code cannot count as independent coding evidence;
- seeing the core solution cannot later become closed-book independent success for that same attempt;
- a target capability cannot initialize current capability;
- a fresh chat cannot infer mastery from model memory.

## Progressive Mentorship safety

Current capability, training zone, scaffolding, prerequisite diagnosis, mentor role, and research-independence state are deterministic derived outputs. They can guide task design but do not bypass mastery/evidence gates.

Prerequisite repair establishes evidence about the repaired prerequisite; it does not automatically certify the original target. Overchallenge/Monster failure is isolated from established capability unless explicit evidence justifies a change.

## Identity and idempotency

Stable event/session identity is part of evidence safety. Exact retries are no-ops; the same identity with different normalized content is a conflict. Duplicate checkpoints, reconnects, or fresh-chat restoration must not multiply evidence.

Each resulting state transition references its causal evidence and is replay-verifiable.

## Subject isolation

The four v1.2 Tutor MCP servers are bound to Mathematics, Statistics & Econometrics, Finance, or CS & AI at launch. Subject/Tutor mismatches fail before authoritative mutation. Evidence from one subject is not silently admitted as another subject's evidence.

## Synthetic / real isolation

Synthetic and integration markers are rejected by learner-mode intake where required. Integration roots use isolated Journal/Vault/Reader state and cannot publish into the real learner Reader. Synthetic Golden E2E demonstrates plumbing and policy behavior; it is never learner performance evidence.

## Projection safety

Markdown is a view. Human text outside Gallop-owned regions is preserved. Edits inside owned regions that break ownership expectations fail closed. Only privacy-filtered Markdown may enter Gallop-Reader; Journal databases, raw inputs, answer keys, private configs, provider runtime, and credentials remain outside it.

Reader is one-way. Phone edits never flow back into mastery or Journal authority.

## Unknown remains unknown

Missing historical evidence means `UNKNOWN`, not zero ability and not permission to invent evidence. Gallop does not silently seed v1.2 capability from legacy scores, model recollections, or prose notes.

See [v1.2 Tutor Protocol](v1.2-tutor-protocol.md), [Progressive Mentorship](progressive-mentorship.md), and [Architecture Governance](architecture-governance.md).
