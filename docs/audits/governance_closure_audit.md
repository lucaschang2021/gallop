# Gallop v1.1 RC2 Governance Closure Audit

Status: G0 COMPLETE — CLASSIFICATION ONLY

Audited candidate: `8bc4dbf7e55f6bbb33f921cf25e2f64e2dafe36b`

Branch: `feat/elite-training-v1.1`

Audit date: 2026-09-13

Execution authority: Codex

## Scope and rules

This audit starts the governance-closure sequence. It does not authorize Gallop
v1.2 feature work and it does not treat architectural preference, file size, or
hypothetical extensibility as a defect. Items classified `DONE` are frozen and
must not be changed unless a later gate demonstrates a concrete regression.

The candidate checkout was clean at the audited SHA. The prior full-candidate
evidence (293 tests, exact frozen V1 replay, examples, offline demo, wheel build,
and `existing = 0` / `introduced = 0`) is reused because the candidate bytes are
unchanged. G0 added only read-only/static verification; it did not touch a real
Vault, mastery store, Reader, iCloud target, or learner evidence.

## Classification

| Area | Status | Current evidence | Remaining governance work |
| --- | --- | --- | --- |
| `ARCHITECTURE.toml` | DONE | Contract v1.0 declares Journal authority, cache/projection derived state, governed layers, policy files, growth review, and an empty accepted-violation baseline. The contract loads successfully. | Freeze unless a demonstrated rule gap requires a minimal contract change. |
| Architecture Gate | PARTIAL | `scripts/check_architecture.py` currently reports `existing = []`, `introduced = []`, and `resolved = []`. It detects core domain/adapter/projection imports, implicit domain time, import-time mutation hazards, policy validity, selected responsibility names, and governed-file growth. | G8 must cover the complete closure contract, notably application-to-CLI, progression-to-automation, projection authority transitions, and responsibility-growth review semantics without weakening the current gate. |
| `gallop.progression` | DONE | Pure package imports only standard-library value utilities and its own modules. Capability, zones, scaffolding, struggle, prerequisites, gains, mentor role, and weekly feedback live here and accept explicit state/context. | No implementation change. Preserve provider/filesystem/network/environment/CLI/automation independence. |
| `gallop.mentorship` | DONE | Compatibility facade delegates decisions to `gallop.progression`; policy/resource loading remains outside the pure progression domain. | Retain as compatibility/policy facade; do not move new domain decisions into it. |
| `automation/service.py` | PARTIAL | Method inventory is predominantly orchestration, validation, persistence coordination, external lifecycle dispatch, projection, and compatibility. The architecture gate finds no forbidden progression decision method. | G3 must record the responsibility classification and test whether concrete store/provider construction prevents the required fake-persistence self-governance check. Move code only for a proven violation. |
| `automation/state.py` | DONE | Owns the historical V1 deterministic reducer, mastery safety gate, queue reconstruction, and compatibility imports. RC2 progression decisions are not implemented here. | Preserve exact V1 replay and queue semantics; no RC2 policy migration into this file. |
| `automation/jobs.py` | DONE | Durable external-provider lifecycle code is explicit runtime behavior and is not imported by the progression domain. Current wall-clock calls describe process submission/poll timing, not replay policy. | Keep as isolated legacy external lifecycle unless a later gate proves a boundary violation. Do not redesign it for v1.2. |
| `mobile.py` | DONE | Filtered one-way export/projection remains separate from the authoritative Journal and has no progression authority. Its date/time and filesystem behavior occur only when runtime operations are called. | Preserve Reader/iCloud safety and do not touch real targets. |
| Bootstrap / composition | PARTIAL | Configuration loading, binding, CLI construction, and execution are callable rather than automatic; importing Gallop is covered by a no-filesystem-side-effect test. There is not yet one clearly documented composition root for the governed application. | G5 must prove construction is mutation-free and establish/document the smallest explicit composition root only if the proof fails or wiring remains ambiguous. |
| Persistence / Journal | DONE | `EventStore` is append-only SQLite with immutable raw inputs, transaction boundaries, stable event IDs, hash chaining, namespace checks, and replay verification. | Preserve authority, idempotency, raw-evidence integrity, and compatibility. |
| Provider abstractions | PARTIAL | DeepTutor is isolated under an adapter and external job lifecycle, but application code still imports and constructs the concrete adapter. No package dependency is declared for DeepTutor. | G4 must document DeepTutor as legacy, optional, non-authoritative, and not required by v1.2; evaluate a minimal tutor-learning port only where required for fake/in-process governance tests. Do not build a new DeepTutor abstraction. |
| Projection boundaries | DONE | Obsidian Markdown, derived state, prepared artifacts, and Reader output are documented and implemented as projections/caches. Projection code is barred from importing authoritative store/service mutation paths. | Add/retain a direct regression proving projections cannot become authority; otherwise do not refactor. |
| Clock / time handling | PARTIAL | Progression chronology and V1 review selection accept explicit timestamps/days; replay does not require the current wall clock. Remaining `date.today()`, `datetime.now()`, and `time.time()` calls are in application/runtime logging, job lifecycle, and export paths. | G6 must classify every call as domain or runtime time and add the smallest explicit clock seam only if domain-relevant scheduling is still implicit. |
| Evidence attribution | PARTIAL | Existing tests cover target/current separation, explicit prerequisites, repair-then-target-retest, AI-generated versus independent work, assistance/hint effects, and evidence-backed gains. | G7 must add any missing direct concept-A/concept-B and shared-dimension attribution regressions. No semantic change unless a failing case demonstrates one. |
| Ruff configuration | NOT_STARTED | `pyproject.toml` has no Ruff dependency/configuration and CI does not run Ruff. | G9 must introduce a meaningful Ruff gate, using an explicit debt baseline only if necessary. |
| Mypy / type configuration | NOT_STARTED | `pyproject.toml` has no Mypy dependency/configuration and CI has no type job/step. | G9 must introduce a no-new-error type gate and document any accepted existing debt; silent suppression growth is forbidden. |
| CI workflows | PARTIAL | Ubuntu/Windows on Python 3.11/3.13 run pytest, examples, architecture, privacy, offline demo, and wheel build. Ruff and type gates are absent. The privacy step is red because reachable history contains non-noreply author metadata. | G1 and G9 must restore all required jobs to green without removing meaningful checks. |
| Repository privacy audit | PARTIAL | `scripts/audit_repository.py` scans all reachable refs/blobs and commit author/committer emails. Current result: 265 blobs scanned; sole finding is `non-noreply-email`. Commit `99c21ce0b38b548b389da6a15d546cfd47314ed7` is reachable from the candidate and `origin/main`; its author metadata contains a non-public address. | G1 must select and document the least-destructive remediation. Disabling the audit, globally accepting private email, or casual history rewriting is forbidden. |
| Documentation | PARTIAL | Architecture, governance, progressive mentorship, and current-status documents accurately describe much of RC2 and Journal authority. They still present DeepTutor as an active integration and do not cleanly separate current implementation, target v1.2, legacy compatibility, and historical V1 baseline. | G11 must update only the four required documents and freeze: `GPT = TEACH`, `GALLOP = GOVERN`, `OBSIDIAN = REMEMBER`, `EVIDENCE = PROVE`; Gallop is headless and the four GPT tutors are the learner-facing surface. |
| V1 replay fixture | DONE | `tests/fixtures/v1-replay.json` exists and the unchanged candidate previously passed exact replay with unchanged queue/projection semantics. | Re-run once in G12 and record exact identity/drift results. |
| RC2 four-subject Golden E2E | DONE | Existing RC2 tests cover Mathematics, Finance, CS/AI, and the Statistics prerequisite-repair/retest path on the unchanged 293-test candidate. | Re-run once in G12. Do not call synthetic coverage Human Production E2E. |

## Application responsibility inventory

The following is the G0 classification; G3 will verify it against behavior and
tests before any movement is considered.

| Responsibility | Current location/examples | G0 conclusion |
| --- | --- | --- |
| A. Orchestration | `intake`, `refresh_queue`, `prepare`, `start`, `ingest_result`, `cycle` | Allowed application work. |
| B. Persistence coordination | `_mutate`, event append, rebuild/replay coordination | Allowed, subject to a replaceable persistence test. |
| C. Validation | `_read_input`, `_validate_extensions`, `_validate_targets` | Allowed boundary validation. |
| D. External lifecycle | `submit`, `poll`, `collect`, provider dispatch in `prepare` | Allowed orchestration, but concrete DeepTutor coupling requires G4 review. |
| E. Domain decision | Delegations to state/progression/mentorship | No proven new RC2 domain formula in `service.py`; do not move code without a failing proof. |
| F. Projection | `_write_prepared`, `project`, `publish` dispatch | Allowed dispatch; projections must remain non-authoritative. |
| G. Compatibility | V1 queue/state/rebuild paths and optional DeepTutor behavior | Preserve unless a demonstrated P0/P1 defect exists. |

## Immediate gate sequence

1. G1: resolve the reachable historical privacy finding and document the choice.
2. G2-G8: close only the proven contract/test gaps identified above.
3. G9: add Ruff and type no-new-error governance.
4. G10-G11: run self-governance regressions and align the four required docs.
5. G12: run the single full regression, record exact values, and freeze the
   governed baseline only if every acceptance condition passes.

## G0 conclusion

`G0 CURRENT-STATE AUDIT = PASS`

This is not Governance Closure PASS. Gallop v1.2 Zero-Touch work remains
unauthorized until G1-G12 pass and the governed baseline is frozen.
