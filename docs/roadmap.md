# Roadmap

This roadmap distinguishes shipped capabilities from proposed priorities.
It supersedes the old v0.2/v0.3/v0.4 sequence now that Automation V1 is released.
There are no promised dates or assigned future version numbers. See
[current status](current-status.md) for dated evidence and limitations.

## Shipped baseline

- **v0.1.0:** structured session/practice protocols, Obsidian/Markdown adapter,
  external DeepTutor boundary, conservative legacy mastery, replay-safe result
  import, review entries and an isolated synthetic demo.
- **v1.0.0 / Automation V1:** raw intake and append-only events, deterministic
  replay, four-subject training queues, human-confirmed practice/assessment,
  mastery safety rules, durable DeepTutor jobs, owned Obsidian projections and
  filtered Gallop-Reader publication.

These releases establish executable workflows, not validated learning outcomes.
Legacy commands remain supported; historical state is not migrated implicitly.

## Release candidate

**v1.1.0rc2** implements Elite Training Protocol evidence and Progressive
Mentorship support. It remains unreleased until its final gate is reviewed and
release is explicitly authorized. Stable v1.0.0 remains immutable. The candidate
does not add a new scheduler or silently reinterpret historical v1 evidence.

## Near-term priorities

| Priority | Work to pursue | Evidence needed before calling it complete |
|---|---|---|
| Reproducible distribution | Version/tag checks, repeatable wheel/source builds, release assets and checksums | Install from a tagged artifact in a clean environment and run the offline examples |
| First-time onboarding | Public synthetic real-mode configuration guidance; clarify existing Reader binding prerequisites and recovery | A new user can identify required setup without copying maintainer paths or resetting receipts |
| Evidence quality | More subject-specific human-assessment examples and mastery calibration fixtures | Known weak evidence is rejected; rule changes include replay/version compatibility |
| Integration reliability | Expand provider-unavailable, late-result and device/cloud acceptance coverage | Separate mocked regressions from dated, opt-in real acceptance; no private evidence published |
| Contributor experience | Keep bilingual entry docs and executable examples aligned with implementation | Fresh-clone reproduction, useful issue reports and focused external PRs |

## Later exploration, not implemented promises

- Adaptive difficulty and review scheduling beyond the current deterministic policies.
- Optional semantic retrieval/embeddings for larger material collections.
- Richer tutor pre-class context and research-oriented learning workflows.
- Additional focused practice/knowledge adapters and a clearer public Python API.

Any new model integration should specify what data leaves the machine, its
failure behavior, and how human learning evidence stays separate from generated
material. Discuss broad API, migration or adapter changes in an issue first.

## Enduring constraints

- Automate learning operations, never fabricate learner work or assessment.
- Preserve local ownership and explicit migration decisions.
- Keep synthetic validation isolated from real mastery and cloud Reader data.
- Prefer reproducible evidence and small useful interfaces over feature counts.
