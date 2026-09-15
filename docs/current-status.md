# Current status

**Snapshot: 2026-09-15.** Gallop's current source baseline is **v1.2.0 — Zero-Touch Learning Continuity**. The RC2 governance work is closed, the v1.2 architecture is implemented, and controlled real four-Tutor dogfood has passed. GitHub Release metadata is intentionally not being updated as part of this source refresh.

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

## Product state

Gallop is headless. The four subject-bound GPT Tutor conversations are the learner-facing surface:

- Mathematics Tutor
- Statistics / Econometrics Tutor
- Finance Tutor
- CS / AI Tutor

Gallop owns the local append-only Journal, deterministic replay, evidence authority, mastery state, bounded fresh-chat continuity, incremental checkpoints, and derived Obsidian / Gallop-Reader projections. Obsidian and Reader are views, never learner authority. DeepTutor is optional legacy compatibility and is not on the v1.2 critical path.

## v1.2 implementation

The current implementation includes:

- versioned v1.2 Tutor Protocol and subject-bound native STDIO MCP servers;
- Runtime Bridge between Tutor calls and the authoritative Gallop application/Journal;
- bounded, deterministic learning-context construction from Journal state;
- fresh-chat restoration without access to prior chat transcripts;
- incremental candidate-evidence admission and checkpointing;
- exact duplicate detection and idempotent recovery;
- conservative evidence classes and human-attestation authority;
- Progressive Mentorship logic for current capability, target capability, prerequisites, training zone, productive struggle, scaffolding, and evidence progression;
- automatic owned Obsidian projection;
- fail-closed projection recovery when a managed region disappears;
- validated one-way PC → Vault → Gallop-Reader publication;
- legacy Automation V1 / v0.1 compatibility without silent historical migration.

See [v1.2 Tutor Protocol](v1.2-tutor-protocol.md), [Architecture](architecture.md), and [Architecture Governance](architecture-governance.md).

## Real four-Tutor acceptance

The dated [v1.2 Real Four-Tutor Dogfood Acceptance](audits/v1.2-real-dogfood-acceptance.md) is **PASS** and covers:

- four real subject-bound Tutor sessions;
- Mathematics proof attempt, diagnosed mistake, assisted repair, restart restore, and fresh-chat closed-book retest;
- Statistics simulation reasoning;
- Finance closed-book derivation and a different-task independent retest;
- CS/AI learner-authored No-Agent Coding;
- incremental checkpointing;
- abrupt-close restoration;
- exact duplicate recovery;
- automatic Obsidian projection;
- fail-closed backup-based projection recovery;
- Reader publication recovery and learner-confirmed mobile visibility;
- four-subject isolation and conservative evidence authority.

The acceptance did not promote weak evidence for presentation purposes. The Mathematics independent retest remained `PARTIAL`, so its state remained `GUIDED` with mastery `0`. That is expected safety behavior, not a release exception.

The learner runtime recorded 91 append-only events and 5 concepts after dogfood, with no synthetic fixture admitted into learner authority state.

## Engineering gates

The v1.2 governed baseline requires:

- full pytest regression;
- Ruff;
- scoped Mypy;
- architecture hard violations `existing=0 / introduced=0`;
- repository privacy audit;
- Tutor protocol example validation;
- isolated offline demo;
- wheel build;
- V1 replay EXACT;
- mastery / queue / evidence drift NONE.

Local pre-freeze Windows / Python 3.13 verification completed with 374 tests, Ruff PASS, Mypy PASS across 20 source files, architecture hard violations `0 / 0`, protocol examples PASS, and isolated offline demo PASS. The frozen V1 replay source remains `c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8`.

A later stable-version promotion exposed one response-order-sensitive MCP STDIO integration assertion on Ubuntu / Python 3.13. Runtime behavior was not the failing invariant: the test assumed JSON-RPC response ordering. The integration test has been hardened to select responses by JSON-RPC request ID so initialization and tool responses may legally arrive in either order. Main promotion is gated on the resulting cross-platform CI matrix.

## Daily-use readiness

**Controlled daily use is accepted.** The core question is no longer whether Gallop can be used as the learner's daily system; it can. The normal workflow is:

1. learn directly in one of the four GPT Tutor conversations;
2. let the Tutor Bridge open or resume the subject session;
3. commit meaningful learning events and checkpoints to the Journal;
4. preserve evidence authority and conservative mastery updates;
5. project the resulting state into Obsidian and one-way Gallop-Reader views;
6. open a fresh chat when needed and restore from Gallop rather than relying on transcript memory.

Further engineering should be driven by real daily-use evidence, reproducible bugs, or clearly justified new scope—not by redesigning the core architecture.

## Distribution and Release boundary

The repository source identifies `gallop-learning` as version `1.2.0`. GitHub Release records are deliberately left unchanged in this update; no new Release page, release asset upload, or release tag is implied here. Source state, controlled acceptance, and GitHub Release publication are separate governance decisions.

## Known limits

1. Gallop has no learner-facing UI or hosted service; the four GPT Tutors are the intended front end.
2. Human attestation is not identity verification or proctoring.
3. Mastery heuristics are conservative software rules, not validated educational measurement.
4. Reader publication is one-way; phone-to-Vault writes are outside the accepted architecture.
5. Local ownership and privacy still require the user not to commit real answers, private paths, credentials, or runtime state.
6. macOS and environments outside the configured Windows/Ubuntu × Python 3.11/3.13 matrix are not part of current CI evidence.
7. Competition Mathematics / Yau specialization, semantic retrieval, broader plugin ecosystems, and a Gallop UI are outside the v1.2 baseline.

See the [roadmap](roadmap.md) for post-v1.2 priorities.
