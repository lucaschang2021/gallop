# Quickstart

Requires Python 3.11+; CI covers 3.11 and 3.13 on Windows and Ubuntu. DeepTutor
must be installed and authorized separately only for live generation.

Choose a path: **Automation V1** below is the current event-driven workflow.
The **legacy walkthrough** later on this page preserves the v0.1 commands and
their separate mastery rules. Neither example needs private learner data.

## 1. Clone and install

```bash
git clone https://github.com/lucaschang2021/gallop.git
cd gallop
python -m venv .venv
```

Activate the environment before installing:

- PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

```bash
python -m pip install -e ".[dev]"
```

Use `python -m pip install -e .` instead if you do not need development tests.

## 2. Try Automation V1 offline

Run these from the repository root, leaving the example configuration unchanged:

```bash
python -m gallop --automation-config examples/automation/config.json intake examples/automation/session.json
python -m gallop --automation-config examples/automation/config.json queue
python -m gallop --automation-config examples/automation/config.json cycle
python -m gallop --automation-config examples/automation/config.json status
python -m gallop --automation-config examples/automation/config.json explain Continuity --subject mathematics
```

Expect one synthetic session/concept, a queued task, mastery 0 and confidence
low. `cycle` reports `training_started: false`; it neither calls DeepTutor nor
fabricates a response. Inspect `automation-runtime/integration_tests/vault/Today.md`
and `vault/Gallop/Automation/Training Queue.md` under the same runtime root.
The Reader directory there is an isolated local preview, not your cloud Reader.
Re-running intake with the identical session does not duplicate evidence.

To inspect a prepared human task, copy a `queue_id` from the queue output:

```bash
python -m gallop --automation-config examples/automation/config.json prepare QUEUE_ID
```

Replace `QUEUE_ID` with the actual ID; do not paste it literally. This writes
`prepared/QUEUE_ID/manifest.json`, `practice.json`, `instructor.answer-key.json`
and `result-template.json` below the runtime root. The task becomes `ready`,
not completed. Default preparation is local: questions/answers can be empty,
and the result template is intentionally incomplete. Never fill it with
invented performance just to make an import pass.

Configuration paths resolve relative to the JSON file, not the shell directory.
Automation does not read `.env`. The root must initially be empty and is then
bound to its namespace and targets. Do not repoint a bound root or remove its
marker to bypass validation.

## 3. Move toward real use deliberately

Read [Automation V1](automation-v1.md), the [CLI reference](automation-cli.md),
and [safety rules](automation-safety.md) before using namespace `learner`.
Real intake requires an existing Obsidian Vault. `publish` and `cycle` additionally
require the existing verified Gallop-Reader binding; a new user without that
setup should stay in the isolated preview. This release does not provide a
general first-run Reader provisioning wizard. Never recreate a Reader or reset
an existing export receipt to make validation pass.

External practice generation is opt-in: configure the separate DeepTutor
executable/runtime, inspect the manifest, then use `prepare QUEUE_ID --send`,
`poll JOB_ID` and `collect JOB_ID`. Supply `--automation-config FILE` before
each subcommand. A timeout is not permission to start a duplicate provider job.
See [DeepTutor bridge](deeptutor-integration.md) for recovery and human assessment.

## Legacy v0.1 walkthrough (still supported)

The following commands use the older file/CLI pipeline. Their demo's 1 → 2
transition is synthetic and does not describe Automation promotion behavior.

### L1. Run the complete synthetic demo

```bash
python -m gallop demo --output demo-output
python -m pytest
python scripts/validate_examples.py
```

The demo writes a synthetic manifest, practice, result, log and Markdown into
`demo-output`. Its first run produces 7 questions, 5/7, mastery 1 → 2. Replaying
the exact result is a no-op; it cannot count as another independent success.

### L2. Configure a legacy knowledge store

Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`;
Linux/macOS: `cp .env.example .env`). For an isolated trial, set:

```dotenv
GALLOP_VAULT_PATH=demo-vault
GALLOP_STATE_PATH=
GALLOP_LOG_PATH=
GALLOP_DEEPTUTOR_PATH=
GALLOP_DEEPTUTOR_HOME=
```

The CLI loads literal values from `.env`; existing environment variables win.
Values are never executed as shell code. Paths are relative to the current
working directory, or explicitly chosen absolute paths in your ignored config.
State defaults to `<vault>/.gallop/mastery.json`; overrides must stay inside the
Vault. Logs default to `<vault>/.gallop/sync.jsonl`.

Open `demo-vault` as an Obsidian Vault if desired. Obsidian itself is not needed
for Markdown operations.

### L3. Sync a structured session and build a manifest

```bash
python -m gallop sync-session examples/mathematics/session.json --vault demo-vault
python -m gallop manifest examples/mathematics/session.json --output demo-output/session-manifest.json
```

The session schema requires all arrays, including empty arrays. Session IDs are
immutable: conflicting content under the same ID is rejected. No score or
mastery is inferred from session text.

### L4. Configure DeepTutor separately

Use [DeepTutor's installation instructions](https://github.com/HKUDS/DeepTutor).
The supported transport was checked against 1.6.1. Set
`GALLOP_DEEPTUTOR_PATH` to the executable and `GALLOP_DEEPTUTOR_HOME` to its
runtime workspace. Configure the model in DeepTutor, not Gallop. Keep OAuth and
provider credentials in DeepTutor's private settings, never in this repository.

Embedding is optional. It affects semantic retrieval over large collections,
not the basic session/practice/mastery/writeback loop.

### L5. Generate live practice (external model call)

Review the selected manifest first. This command sends its learning context to
the provider configured in DeepTutor:

```bash
python -m gallop generate examples/mathematics/practice-manifest.json --output demo-output/live-practice.json
```

The learner-facing file has questions only. The sibling
`live-practice.answer-key.json` is instructor-only. `no_agent` requests a
hint-first workflow; it is not a guarantee that an external model never leaks
an answer, nor a proctoring/security boundary. v0.1 generates diagnostic choice
questions; actual proof and oral assessment remain tutor-led.

### L6. Import an example result

```bash
python -m gallop import-result examples/mathematics/practice-result.json --vault demo-vault
```

This is explicitly synthetic and writes only to `integration_tests`.
Real users must create a result from observed attempts, using the generated
`practice_id` and `manifest_id`. Gallop re-evaluates mastery; it does not trust
the supplied `mastery_after`. Independence and delayed/transfer/oral evidence
are explicit observations, never inferred from a score.

Inspect:

```text
demo-vault/Gallop/Sessions/
demo-vault/Gallop/Practice/integration_tests/
demo-vault/.gallop/mastery.json
demo-vault/.gallop/sync.jsonl
```

Each practice note includes unchecked T+1/T+7/T+30 review entries. Check them in
the knowledge store; Gallop does not start another background scheduler.

### L7. Opt-in real transport acceptance

```bash
python -m gallop live-demo --output live-demo-output --send
```

This sends only the bundled fictional manifest. DeepTutor generates seven real
questions; the test actor then supplies a deliberately synthetic 5/7 summary.
The result is not a learner score and does not assess question quality.

If practice generation completed but writeback failed, repeat the same command
without `--send`: it reuses `practice.json`. If the transport timed out before
saving it, inspect DeepTutor's own session before authorizing another call.
There is no unsafe automatic “latest session” recovery.

### L8. Legacy recovery and limitations

- Result failures preserve the input file; writeback also stages a recoverable
  protocol file under `<vault>/.gallop/pending/<namespace>/`.
- Re-import that file after fixing the error; matching practice IDs are replay-safe.
- One writer per knowledge store is supported. A crash can leave a `.lock`
  beside the state file: verify no Gallop process is active before removing it.
- Markdown is written before the atomic state commit. A crash can leave a note
  ahead of state; replay reconciles it. This is not a distributed transaction.
- Out-of-order results and conflicting IDs are rejected, not silently merged.
- There is no native ChatGPT account scraper: structured packages are imported
  by file/CLI. The tutor protocol works with any compatible producer.
