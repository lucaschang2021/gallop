# Current status

**Snapshot: 2026-09-16.** Gallop v1.2.0 is the stable Zero-Touch Learning
Continuity release. The implementation, controlled real four-Tutor dogfood, and
required Windows/Ubuntu Python 3.11/3.13 CI matrix are complete. The stable
commit is `5c5ded1ecf163707fe818cbfea277abaa7b998b5`, tagged `v1.2.0`.

Gallop is headless. The frozen target product definition is:

> GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE

## Current v1.2.0 implementation

Automation V1 provides explicit tutor intake, raw-byte preservation, append-only
SQLite evidence, replayable learning state, four-subject queues, conservative
mastery/confidence rules, human start/assessment gates, Obsidian projections,
the filtered Reader exporter, and the pure advisory Progressive Mentorship
domain. CLI/file operations remain the current operational interface; Gallop
ships no learner UI.

The governed baseline adds a non-destructive exact-commit privacy-debt gate,
Ruff and scoped Mypy gates, a mutation-free construction/composition boundary,
explicit application Clock/Journal seams, and expanded architecture checks.
Its exact counts and drift results are in the
[governed-baseline record](baselines/rc2-governed-baseline.md).

## Stable v1.2 architecture

The first seven sequential v1.2 stages, a versioned bidirectional
[Tutor Protocol](v1.2-tutor-protocol.md) and its transport-neutral Runtime
Bridge plus incremental unconfirmed candidate-evidence admission, are
implemented on the v1.2 branch together with automatic privacy-filtered
Obsidian projection into the existing four subject roots and deterministic,
bounded, journal-derived learning context packets.
It targets four GPT tutor conversations as the complete learner-facing surface,
backed by one Gallop Journal/application. Opening or resuming a Tutor session
automatically returns that context, including across a process restart and an
unfinished prior chat. Four-subject continuity is now covered by an isolated
synthetic Golden E2E over one runtime.
Controlled real dogfood now covers all four Tutors, incremental checkpoints,
exact duplicate recovery, abrupt-close restoration, a no-transcript fresh chat,
owned Obsidian projection, and learner-confirmed mobile Reader visibility. The
[dated acceptance record](audits/v1.2-real-dogfood-acceptance.md) keeps actual
learner outcomes separate from runtime acceptance: in particular, a partial
Mathematics independent retest remained `GUIDED` at mastery level `0`. Synthetic
E2E remains isolated and is not learner evidence.

## Legacy compatibility

DeepTutor is legacy, optional, non-authoritative, and not part of the target
primary workflow. Existing isolated adapter/job compatibility remains to avoid
unnecessary migration risk; v1.2 must require zero DeepTutor runtime
dependencies. Legacy v0.1 commands and their separate state also remain
available but are not the future learner workflow.

## Historical V1 baseline

The following release/repository evidence describes the historical V1 baseline
at [`c8d0dfd`](https://github.com/lucaschang2021/gallop/commit/c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8),
tagged `v1.0.0`. It remains compatibility evidence, not a current health check.

## Release and repository evidence

| Area | Verified snapshot | Meaning / limit |
|---|---|---|
| Package | `gallop-learning` 1.2.0, Python >=3.11, Alpha classifier in [pyproject.toml](../pyproject.toml) | Stable package release; this is not a production-readiness guarantee |
| Releases | [v1.2.0](https://github.com/lucaschang2021/gallop/releases/tag/v1.2.0), [v1.0.0](https://github.com/lucaschang2021/gallop/releases/tag/v1.0.0), [v0.1.0](https://github.com/lucaschang2021/gallop/releases/tag/v0.1.0) | v1.2.0 is the current stable release; CI does not attach wheel/checksum assets |
| Tags | `v0.1.0-rc1`, `v0.1.0`, `v1.0.0`, `v1.2.0` | Release candidates and releases are distinct; no PyPI publication is established here |
| Pull requests | [#1](https://github.com/lucaschang2021/gallop/pull/1) and [#2](https://github.com/lucaschang2021/gallop/pull/2) merged | No open PR at the start of this documentation review; this review's PR is subsequent work |
| Issues | No standalone issues returned by the repository's all-state issue listing at review start | Absence of reported bugs is not proof of absence of defects |
| CI | Stable v1.2.0 verification [run 35064712786](https://github.com/lucaschang2021/gallop/actions/runs/35064712786) passed on all four matrix jobs | Checks the stable release commit; macOS and other Python versions are not covered |

The [CI workflow](../.github/workflows/tests.yml) runs on push and pull request
with Windows/Ubuntu × Python 3.11/3.13. It installs development dependencies,
runs Ruff and the scoped Mypy gate, pytest, examples, architecture and privacy
audits, the offline demo, and a wheel build. It does **not** upload release
artifacts or implement a tag/version release gate. macOS and other Python
versions are not covered by this matrix.

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

1. **Real setup remains technical.** v1.2.0 provides subject-bound local Tutor MCP
   tools, but no daemon, account scraper, automatic notifications, or Gallop UI.
   `learner` mode requires an existing
   Obsidian Vault; `cycle`/`publish` need an existing verified Reader binding.
   The isolated preview works without those external applications. A portable
   first-time real Reader setup is not delivered by the sample configuration.
2. **Human evidence authority is essential.** Legacy DeepTutor choice diagnostics do not establish
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
6. **Distribution can improve.** CI does not upload wheel/checksum assets and no
   PyPI publication is established. Use source installation or the verified tag.
7. **Future capabilities stay future.** Built-in semantic retrieval, a general
   plugin ecosystem, Competition Mathematics, Yau specialization, and a Gallop
   UI are not part of the v1.2 baseline.

See [roadmap](roadmap.md) for proposed priorities. No existing learning data,
cloud account or external provider was changed by this documentation review.
