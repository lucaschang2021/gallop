# Current status

**Snapshot: 2026-08-31.** Implementation baseline:
[`c8d0dfd`](https://github.com/lucaschang2021/gallop/commit/c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8),
the main commit tagged `v1.0.0`. This is a dated review, not a live status page.
Documentation changes after that commit do not imply new runtime capabilities.

## Release and repository evidence

| Area | Verified snapshot | Meaning / limit |
|---|---|---|
| Package | `gallop-learning` 1.0.0, Python >=3.11, Alpha classifier in [pyproject.toml](../pyproject.toml) | v1.0.0 names the Automation milestone; it is not a production-readiness guarantee |
| Releases | [v1.0.0](https://github.com/lucaschang2021/gallop/releases/tag/v1.0.0), [v0.1.0](https://github.com/lucaschang2021/gallop/releases/tag/v0.1.0) | v1.0.0 has GitHub source archives but no attached wheel/checksum assets; v0.1.0 has a source ZIP, wheel and checksums |
| Tags | `v0.1.0-rc1`, `v0.1.0`, `v1.0.0` | Release candidates and releases are distinct; no PyPI publication is established here |
| Pull requests | [#1](https://github.com/lucaschang2021/gallop/pull/1) and [#2](https://github.com/lucaschang2021/gallop/pull/2) merged | No open PR at the start of this documentation review; this review's PR is subsequent work |
| Issues | No standalone issues returned by the repository's all-state issue listing at review start | Absence of reported bugs is not proof of absence of defects |
| CI | Main [run 33401439397](https://github.com/lucaschang2021/gallop/actions/runs/33401439397) and tag [run 33401773433](https://github.com/lucaschang2021/gallop/actions/runs/33401773433) succeeded at the baseline SHA | Historical checks, not results for future commits |

The [CI workflow](../.github/workflows/tests.yml) runs on push and pull request
with Windows/Ubuntu × Python 3.11/3.13. It installs development dependencies,
runs pytest, validates examples, audits reachable Git history, runs the offline
demo and builds a wheel. It does **not** upload release artifacts or implement
a tag/version release gate. macOS and other Python versions are not covered by
this matrix.

## What is implemented

Automation V1 provides explicit tutor intake, raw-byte preservation, append-only
SQLite evidence, replayable learning state, four-subject queues, conservative
mastery/confidence rules, human start/assessment gates, durable DeepTutor jobs,
Obsidian projections and the existing filtered Reader exporter. Legacy CLI
commands and their separate state remain available. See [architecture](architecture.md)
for code ownership and [Automation](automation-v1.md) for the actual workflow.

## Evidence strength

- **Public reproducible checks:** the source tree contains offline synthetic
  unit/integration tests, protocol examples and demos; CI runs without private
  model credentials. They verify contracts and failure/recovery behavior.
- **Historical real acceptance:** the [v1.0.0 final gate](automation-final-gate.md)
  reports 177/177 local tests, one real DeepTutor generation/collection, a
  user-confirmed non-independent response, isolated projection, unchanged real
  mastery, and 7/7 Reader files synced. Private evidence was deliberately not
  published. These are release-record claims, not a new live rerun here.
- **Not established:** broad provider compatibility, learning efficacy, validated
  mastery calibration, independent authorship, or general production readiness.
  Synthetic results must never be described as real learner performance.

## Known limitations and remaining work

1. **Onboarding is technical.** CLI/file intake only; no chat UI, daemon, account
   scraper or automatic notifications. `learner` mode requires an existing
   Obsidian Vault; `cycle`/`publish` need an existing verified Reader binding.
   The isolated preview works without those external applications. A portable
   first-time real Reader setup is not delivered by the sample configuration.
2. **Human work is essential.** DeepTutor choice diagnostics do not establish
   proof, oral, coding or simulation performance. Gallop accepts human-confirmed
   evidence; it does not independently verify the person or replace an examiner.
3. **Two state models coexist.** Automation never silently migrates legacy
   mastery. The legacy demo's synthetic 1 → 2 result is not the Automation rule.
4. **Privacy needs user review.** Raw input and answers remain private. External
   generation sends selected context to a configured provider; Reader filtering
   is defense in depth, not complete sensitive-text detection.
5. **Recovery has limits.** No provider exactly-once claim across uncertain OS
   spawning; no atomic transaction across all Markdown files and cloud sync.
   Existing live/uncertain jobs must not be duplicated to escape a timeout.
6. **Distribution can improve.** v1.0.0 artifact uploads, checksums and release
   version checks are missing from the current workflow. Use source installation.
7. **Future capabilities stay future.** Built-in semantic retrieval, adaptive
   difficulty and a general plugin ecosystem are not shipped features.

See [roadmap](roadmap.md) for proposed priorities. No existing learning data,
cloud account or external provider was changed by this documentation review.
