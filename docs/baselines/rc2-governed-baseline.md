# GALLOP v1.1 RC2 — GOVERNED BASELINE

Record date: 2026-09-13

Governed code SHA: `d2c4d9357c2553824cf44cc29c8961286e244a46`

Baseline record commit: the commit containing this file. The record does not
self-reference an object ID because that would make the commit hash impossible
to stabilize.

Acceptance condition: this record is valid only if the commit containing this
file completes the required GitHub Actions matrix successfully. Once that exact
commit is green, this record is the frozen v1.1 RC2 governance boundary.

## Closure result

- Governance closure G0-G11: PASS at the governed code SHA.
- Product boundary: Gallop remains headless. The four GPT tutor chats are the
  planned v1.2 user-facing surface, not part of this baseline.
- DeepTutor: legacy and optional; non-authoritative and not the future primary
  workflow.
- v1.2 implementation: NOT STARTED by this closure.

## Required evidence

- Tests: 298 passed locally; GitHub Actions exercises Ubuntu and Windows on
  Python 3.11 and 3.13.
- Pull-request CI for the governed code SHA: PASS, run
  `https://github.com/lucaschang2021/gallop/actions/runs/34747391949`.
- Ruff: PASS for the configured zero-debt correctness rules.
- Mypy: PASS for the frozen progression and application-port boundary (13
  source files).
- Architecture contract: PASS with no introduced or existing hard violations.
  Review warnings remain for the documented service/state/mobile/jobs growth
  thresholds; none crosses its hard limit.
- Repository privacy audit: PASS for history reachable from the exact governed
  SHA. The sole accepted historical metadata debt remains exact commit
  `99c21ce0b38b548b389da6a15d546cfd47314ed7`; future non-public commit metadata
  remains fail-closed.
- Protocol examples, offline demo, and wheel build: PASS.
- Local wheel: `gallop_learning-1.1.0rc2-py3-none-any.whl`, SHA-256
  `84a680f1e780175950eb1263f9ed341724411073f22d490b9d6b26d01b49fe27`.

## Replay and semantic invariants

Frozen v1 replay source commit:
`c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8`.

- Events replayed: 38.
- State exact: true.
- State SHA-256:
  `9f70585b0454dcf00ddcbb14b616a34c285ede6394e913846719e959a382fba3`.
- Projection exact: true.
- Projection SHA-256:
  `0fb261f68c2650e95b07642a33e70886e7302a8988f3973768108cbbe1e8d8f3`.
- Mastery drift: none.
- Queue drift: none.
- Evidence drift: none; shared readiness-dimension evidence cannot become
  concept evidence for another concept.
- Journal remains authoritative; Reader/Markdown remain projections.
- `queue_mutation=NONE` remains non-mutating.

## Compatibility and known debt

- Public v1 behavior, deterministic replay, mastery, queue, evidence, CLI demo,
  schemas, and wheel construction remain covered by the required matrix.
- Broader Ruff style/modernization findings are recorded debt, not silently
  grandfathered correctness violations.
- Mypy coverage is intentionally scoped; expanding it is future governed work.
- File-size review warnings are recorded in architecture governance and remain
  below their fail-closed hard limits.
- The historical non-public Git metadata item remains published accepted debt;
  its exception is commit-specific and contains no copied private address.
- Synthetic demo or integration evidence is not Human Production E2E and does
  not change real learner mastery.

## Freeze rule

Once the baseline record commit's required CI is green, governance closure is
PASS and the decision is GO FOR ZERO-TOUCH AUTOMATION. Execution stops here.
Starting v1.2, merging the pull request, changing real learner data, or treating
DeepTutor as the primary interface requires separate explicit authorization.
