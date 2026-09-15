# Security policy

## Supported source state

Security fixes target the latest maintained source baseline. Source version, GitHub Release/tag state, PyPI publication, and release assets are separate facts; consult [Current Status](docs/current-status.md) before assuming a published release contains a fix.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting when available. Do not attach real learning data, learner answers, Journal databases, complete Vault/Reader files, cloud metadata, credentials, or provider runtime output to a public issue. Provide a synthetic reproduction and only the minimum diagnostic metadata required.

## v1.2 trust boundaries

Gallop v1.2 is local-first and headless, but it crosses several trust boundaries:

- **Tutor MCP:** four subject-bound local MCP servers accept structured learning events. Subject/Tutor identity mismatches must fail before Journal mutation.
- **Journal:** the append-only Journal is authoritative. SQLite triggers and hash chains detect accidental corruption; they are not a hostile-owner tamper-proof system.
- **Evidence:** Tutor assessment is candidate evidence. Human attestation is separate. Model output, provider output, or an Obsidian edit must not directly promote mastery.
- **Obsidian:** managed Markdown is a projection. Ownership conflicts fail closed; user text outside managed regions is preserved.
- **Gallop-Reader:** the Reader is a filtered, one-way reading mirror. Phone edits never flow back as authority.
- **Legacy providers:** DeepTutor is optional/legacy. Any external generation sends only explicitly selected context to the separately configured provider.

## User responsibilities

- Never commit API keys, OAuth tokens, cookies, credentials, private configuration, or `.env`.
- Keep the real Journal root outside cloud storage and outside the Obsidian/Reader trees.
- Treat every Obsidian Vault and Reader as potentially private.
- Review external-provider manifests/context before sending them.
- Keep real learner answers, raw evidence, provider logs, answer keys, and iCloud metadata outside this repository.
- Use only the existing verified Reader binding for real publication; do not bypass identity/ownership checks by recreating a same-name directory or resetting receipts.
- Run synthetic/integration tests only in isolated namespaces and paths.
- Inspect Git history and commit metadata, not only the current tree, before publication.
- Use a public GitHub noreply commit identity; CI audits author/committer metadata.

## Data minimization

The v1.2 Tutor Protocol intentionally uses bounded structured payloads instead of whole chat transcripts. Large artifacts should be referenced, not embedded. Fresh-chat continuity is reconstructed from bounded Journal-derived context; hidden model memory is not an authority channel.

## Secret or private-data exposure

If a secret reaches Git history, revoke or rotate it immediately and identify the affected commits. Deleting the current file is not sufficient. If private learner data reaches a public branch, treat the published history and any forks/caches as potentially persistent and follow the provider's removal procedures in addition to repository remediation.

## Security limits

Privacy filtering, schema validation, path checks, hash chains, and Reader ownership checks are defense in depth. They do not prove that arbitrary sensitive prose will always be detected, that a local machine owner cannot modify state, or that a cloud provider will never retain deleted/versioned files.
