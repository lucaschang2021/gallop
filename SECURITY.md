# Security policy

## Supported versions

Gallop is an early release. Security fixes target the latest published version.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting when available. Do not attach
private learning data, credentials, or complete Vault files to a public issue.
Provide a synthetic reproduction and the minimum diagnostic metadata required.

## User responsibilities

- Never commit API keys, OAuth tokens, cookies, credentials, or `.env`.
- Treat every Obsidian Vault as potentially private.
- Keep practice-engine account state and private data outside this repository.
- Review manifests before sending them to an external model or service.
- Run integration tests only in an isolated directory and namespace.
- Inspect Git history, not only the current tree, before making a repository public.

Gallop is local-first, but adapters may invoke separately configured external
services. Local-first does not mean that every selected manifest remains offline.

## Secret exposure

If a secret reaches Git history, revoke or rotate it immediately and report the
affected commits. Deleting the current file is not sufficient remediation.

