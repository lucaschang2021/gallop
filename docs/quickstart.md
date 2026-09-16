# Quickstart

Gallop requires Python 3.11+. CI covers Python 3.11 and 3.13 on Windows and Ubuntu.

There are now **three distinct paths**:

1. **v1.2 daily use:** learn directly in one of the four subject-bound GPT Tutor conversations; Gallop runs underneath through the local MCP bridge.
2. **isolated developer validation:** run synthetic/offline examples without touching real learner state.
3. **legacy Automation V1 / v0.1:** keep the CLI workflows for compatibility, testing, migration boundaries, and optional DeepTutor generation.

Do not confuse these paths. v1.2 Zero-Touch does not require DeepTutor and does not require a separate Gallop learner UI.

## 1. Clone and install

```bash
git clone https://github.com/lucaschang2021/gallop.git
cd gallop
python -m venv .venv
```

Activate the environment:

- PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Then install:

```bash
python -m pip install -e ".[dev]"
```

Use `python -m pip install -e .` if you do not need developer/test dependencies.

## 2. Run the public offline checks first

Before connecting any real Vault or Reader, verify the isolated repository path:

```bash
python -m pytest
python scripts/verify_v1_replay.py
python scripts/validate_examples.py
python scripts/check_architecture.py
python -m gallop demo --output demo-output
```

The demo is synthetic. Its output is not learner evidence and must never be imported into real mastery merely to prove that a workflow runs.

## 3. Understand the v1.2 daily-use path

The normal v1.2 shape is:

```text
Learner
  ↕
Mathematics / Statistics / Finance / CS-AI GPT Tutor
  ↕ subject-bound STDIO MCP
Gallop Tutor Bridge
  ↕
Append-only Journal
  ↓
Evidence / mastery / mentorship / bounded context
  ↓
Obsidian → filtered Gallop-Reader
```

The MCP entry points are:

| Subject | Server command | Bound Tutor ID |
|---|---|---|
| Mathematics | `gallop-mathematics-tutor` | `mathematics-tutor` |
| Statistics & Econometrics | `gallop-statistics-tutor` | `statistics-econometrics-tutor` |
| Finance | `gallop-finance-tutor` | `finance-tutor` |
| CS & AI | `gallop-cs-ai-tutor` | `cs-ai-tutor` |

Each process is bound to one subject. A caller cannot use a Mathematics server to write Finance evidence. The transport contains no model call; it exposes Gallop state/governance tools to the Tutor host.

## 4. Real learner configuration is intentionally explicit

Do **not** point the bundled synthetic config at your real data.

Real learner mode requires all of the following to already exist and be verified:

- a private Gallop runtime root outside cloud storage;
- the real Obsidian Vault;
- the existing Gallop-Reader target;
- a separate export-state directory;
- the validated Reader/cloud binding used by the current machine.

The Journal is authoritative and must remain private. Obsidian and Reader are projections. Do not create a replacement Reader, reset export receipts, or bypass ownership markers simply to make validation pass.

Before first write, read [Real Tutor Integration](v1.2-real-tutor-integration.md), [Current Status](current-status.md), [Tutor Protocol](v1.2-tutor-protocol.md), and the [real dogfood acceptance](audits/v1.2-real-dogfood-acceptance.md).

## 5. How a real Tutor session behaves

A Tutor should:

1. open or resume a stable session;
2. receive bounded Journal-derived context;
3. teach normally;
4. record meaningful learning events with stable IDs;
5. checkpoint meaningful progress incrementally;
6. keep Tutor assessments as candidate evidence;
7. use the explicit human/authority flow when confirmation is required;
8. finalize the session without treating finalization itself as the only durability boundary.

If the desktop/process exits unexpectedly, the next `open_or_resume_session` rebuilds the prior session from the Journal. A fresh chat may use only the stable session identity and still recover current context without access to the earlier transcript.

## 6. Evidence rules to preserve

- A target is not current capability.
- A correct answer with assistance is not independent evidence.
- AI-generated code cannot become independent coding evidence.
- Tutor assessment is candidate evidence, not mastery authority.
- Human confirmation does not magically prove correctness; it records the configured attestation boundary.
- Obsidian edits never directly mutate mastery/progression.
- Synthetic fixtures never enter learner authority state.

The real dogfood deliberately preserved a partial Mathematics retest at `GUIDED`, mastery `0`, proving that acceptance does not require inflating learner outcomes.

## 7. Automation V1 developer workflow (still supported)

For the isolated Automation example:

```bash
python -m gallop --automation-config examples/automation/config.json intake examples/automation/session.json
python -m gallop --automation-config examples/automation/config.json queue
python -m gallop --automation-config examples/automation/config.json cycle
python -m gallop --automation-config examples/automation/config.json status
python -m gallop --automation-config examples/automation/config.json explain Continuity --subject mathematics
```

Expect synthetic state only. The example runtime lives under the ignored `automation-runtime/integration_tests/` tree and is not a real Vault/Reader deployment.

To inspect a prepared local task:

```bash
python -m gallop --automation-config examples/automation/config.json prepare QUEUE_ID
```

`QUEUE_ID` must be copied from actual queue output. Preparing a task does not mean the learner started or completed it.

## 8. Optional legacy DeepTutor generation

DeepTutor is an optional compatibility adapter. If intentionally configured, external generation remains explicit:

```bash
python -m gallop --automation-config CONFIG prepare QUEUE_ID --send
python -m gallop --automation-config CONFIG poll JOB_ID
python -m gallop --automation-config CONFIG collect JOB_ID
```

A provider timeout is not permission to start a duplicate uncertain job. Provider output is generated material, not learner performance. See [DeepTutor integration](deeptutor-integration.md).

## 9. Legacy v0.1 commands

The older file/CLI path remains available:

```bash
python -m gallop sync-session examples/mathematics/session.json --vault demo-vault
python -m gallop manifest examples/mathematics/session.json --output demo-output/session-manifest.json
python -m gallop import-result examples/mathematics/practice-result.json --vault demo-vault
```

Its state model is separate. No legacy score or Markdown state is silently promoted into v1.2 authority.

## 10. Recovery rule

When something fails, preserve the strongest durable boundary instead of fabricating success:

- Journal commit succeeded, projection failed → recover projection; do not duplicate the event.
- exact event retry → idempotent duplicate result.
- same event ID with different content → conflict.
- Reader/cloud uncertain → verify identity/state before publication; do not repair provider/cloud state blindly.
- legacy provider job uncertain → inspect existing job/session before retry.

## 11. Daily-use stop rule

Once the four Tutors, Journal, Vault projection, and Reader are healthy, **stop configuring Gallop and study**. v1.2 is intended to disappear underneath the learning workflow rather than become another dashboard to manage.