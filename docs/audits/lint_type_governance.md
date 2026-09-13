# Lint and Type Governance

Status: IMPLEMENTED

Scope: Gallop v1.1 RC2 governance closure

## Ruff gate

Ruff is a required development and CI dependency. RC2 enforces the zero-debt
correctness families `E9`, `F63`, `F7`, and `F82` across `gallop`, `tests`, and
`scripts`. These detect syntax/runtime-name defects without forcing a broad
formatting or style migration during closure.

A diagnostic run of Ruff's broader current rule set reported 262 findings,
mostly import formatting, modernization, complexity/style, and pytest-fixture
name patterns. That debt is explicitly outside RC2 closure. Expanding the
selected rule families requires its own reviewed change; existing selected
errors remain zero and no selected error may be introduced.

## Type gate

Mypy is a required development and CI dependency. The initial no-new-error
boundary covers the pure `gallop.progression` domain and the minimal application
ports in `gallop/automation/ports.py`. These are the highest-authority boundary
for current capability/progression decisions and the construction/time seams
added by governance closure.

Gallop v1.2 expands the boundary to `gallop.tutor`, beginning with its pure
protocol validator. Mypy consequently follows the typed Gallop validation
wrapper; the installed `jsonschema` package does not expose typed interfaces,
so a package-specific `jsonschema`/`jsonschema.*` missing-import override is
declared in `pyproject.toml`. It does not suppress findings in Gallop code.

The legacy application, adapters, CLI, and projection modules remain outside
this type boundary. Broad annotation churn in those modules is not required.
The configured type scope must remain green; expansion is allowed only by an
explicit reviewed configuration change, and suppressions may not grow silently.
