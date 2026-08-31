# Dependency and license boundary

Gallop's own code is Apache-2.0, chosen for an explicit patent grant and clear
contribution terms. DeepTutor 1.6.1 is an external Apache-2.0 application invoked
through its CLI; no DeepTutor source, assets, models or private runtime data
are redistributed with Gallop.

Runtime Python dependencies:

| Package | License |
|---|---|
| jsonschema | MIT |
| attrs | MIT |
| jsonschema-specifications | MIT |
| referencing | MIT |
| rpds-py | MIT |

pytest is a development dependency under MIT. Python's standard library follows
the Python Software Foundation license. Third-party packages retain their own
licenses; installing Gallop does not relicense them. Package metadata for the
installed validation/test stack was inspected during release preparation.

DeepTutor model-provider terms, account eligibility and model outputs remain
outside Gallop's license. This file describes dependency boundaries, not a
promise of legal compatibility for every future integration.
