# Quickstart

Requires Python 3.11–3.13. DeepTutor is optional for the offline demo and must
be installed and authorized separately for live practice.

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
python -m gallop demo --output demo-output
python -m pytest
python scripts/validate_examples.py
```

The demo writes a synthetic manifest, practice, result, log and Markdown into
`demo-output`. Its first run produces 7 questions, 5/7, mastery 1 → 2. Replaying
the exact result is a no-op; it cannot count as another independent success.

## 2. Configure a knowledge store

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

## 3. Sync a structured session and build a manifest

```bash
python -m gallop sync-session examples/mathematics/session.json --vault demo-vault
python -m gallop manifest examples/mathematics/session.json --output demo-output/session-manifest.json
```

The session schema requires all arrays, including empty arrays. Session IDs are
immutable: conflicting content under the same ID is rejected. No score or
mastery is inferred from session text.

## 4. Configure DeepTutor separately

Use [DeepTutor's installation instructions](https://github.com/HKUDS/DeepTutor).
The supported transport was checked against 1.6.1. Set
`GALLOP_DEEPTUTOR_PATH` to the executable and `GALLOP_DEEPTUTOR_HOME` to its
runtime workspace. Configure the model in DeepTutor, not Gallop. Keep OAuth and
provider credentials in DeepTutor's private settings, never in this repository.

Embedding is optional. It affects semantic retrieval over large collections,
not the basic session/practice/mastery/writeback loop.

## 5. Generate live practice (external model call)

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

## 6. Import an example result

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

## 7. Opt-in real transport acceptance

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

## 8. Recovery and limitations

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
