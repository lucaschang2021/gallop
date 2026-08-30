# Quickstart

Gallop v0.1 provides a complete offline demo and explicit manual steps for real
Obsidian and DeepTutor usage. It does not claim one-command setup.

## 1. Install Gallop

```bash
git clone https://github.com/OWNER/gallop.git
cd gallop
python -m venv .venv
python -m pip install -e ".[dev]"
```

Activate the virtual environment using the command appropriate for your shell.

## 2. Run the isolated demo

```bash
python -m gallop demo --output demo-output
```

The command generates seven deterministic questions, submits a fictional 5/7
result, updates mastery from 1 to 2, and writes Markdown. It never calls a model.

## 3. Prepare a real Markdown or Obsidian directory

Create or select a Vault. Copy `.env.example` to `.env` and set paths for your
machine. `.env` is ignored by Git. Gallop's Python API accepts `pathlib.Path`
objects; v0.1 does not automatically load `.env`.

## 4. Configure DeepTutor separately

Install DeepTutor by following its own documentation and configure a supported
model. Record only the path to its executable in Gallop configuration. Never
copy DeepTutor's private data directory, OAuth state, or credentials into this
repository or your Vault.

## 5. Generate practice

Validate a session against `gallop/schemas/session.schema.json`, then create a
minimal manifest matching `practice-manifest.schema.json`. Call
`DeepTutorAdapter.generate(manifest)` or another `PracticeEngine` implementation.

## 6. Import a result

Construct `PracticeResult` only from observed attempts. Pass it to
`GallopPipeline.import_result`. Set `integration_test=True` for every automated
or synthetic acceptance run.

## 7. Observe state

The default adapter writes:

```text
<vault>/Gallop/Practice/<namespace>/*.md
<vault>/.gallop/mastery.json
```

The `learner` and `integration_tests` namespaces are separate. The knowledge
store remains the review source of truth.

## 8. Run verification

```bash
pytest
python scripts/validate_examples.py
```

Real DeepTutor E2E requires a local installation and model authorization, so CI
uses a mock transport. Run real E2E only against an isolated test Vault.
