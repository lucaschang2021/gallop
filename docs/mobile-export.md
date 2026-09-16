# Gallop-Reader — one-way mobile reading mirror

Gallop-Reader is the v1.2 mobile/read-only projection surface. It is **not** a learner authority store, not bidirectional sync, and not a replacement for the private Journal.

The current accepted flow is:

```text
Journal → owned Obsidian projections → privacy filter → Gallop-Reader → iPhone reading
```

Controlled v1.2 real dogfood has exercised Reader publication, republish recovery, and learner-confirmed mobile visibility. The Journal remained authoritative throughout.

## Export command

The compatible standalone exporter remains:

```bash
gallop mobile-export --source MAIN --target PATH/Gallop-Reader --state LOCAL_STATE
```

`python -m gallop.mobile` exposes the same arguments without loading the full backend CLI. Use `--dry-run` to inspect the export without writing.

v1.2 Tutor sessions can also refresh the same Reader through the configured learner projection/publication path after Journal commits.

## Reading policy

Only allowed UTF-8 Markdown roots are eligible. Gallop excludes hidden/internal state, raw Journal data, JSON state, answer keys, provider runtime, configuration, credentials, tokens, logs, integration fixtures, and other backend artifacts.

Papers/research Markdown and Gallop-owned learner projections can be included when they pass the export policy. Credential-shaped content and `mobile_export: false` exclude a note. Filtering is defense in depth, not a guarantee that arbitrary sensitive prose will always be detected.

`Today.md` and other generated pages are readable projections. They do not acquire authority because they are visible on mobile.

## Ownership and direction

The destination must be the verified `Gallop-Reader` and remain separate from the main Vault and private Journal root. Local export receipts/backups stay outside both Vault/Reader cloud trees.

The direction is one-way:

> **PC/Main → Gallop-Reader**

Phone edits are possible at the filesystem/app level, but Gallop never imports them as Journal evidence, mastery, readiness, or Tutor context. Keep the Reader as a reading mirror.

Unknown mobile files are not silently interpreted as learning state. Gallop-owned files can be refreshed from Main/Journal-derived projections; ownership conflicts and unsafe path conditions fail closed.

## Atomicity and recovery

Source scanning and path checks complete before publication. Each final Markdown write is atomic; the whole Journal + Vault + cloud publication chain is not one distributed transaction.

The durability order is:

> **Journal commit first → projection refresh → Reader publication**

If projection or cloud publication fails, committed evidence is not rolled back. Fix the projection/export condition and republish from authoritative Journal state.

Temporary payloads are staged outside the cloud tree before final publication. A local lock prevents concurrent exporters. Interrupted exports can be rerun after confirming no exporter remains active.

## iCloud on Windows

For the validated iPhone Reader path, Gallop can use read-only Cloud Files/provider metadata checks before publication. The binding identifies the expected Reader object/path and helps prevent accidental writes to a same-name but different directory.

The exporter does **not** edit Apple's provider database, force sync flags, reset an account, or manufacture cloud object metadata. A same-name folder or sync icon is not sufficient proof of identity.

If provider metadata and the Windows placeholder disagree, stop and resolve the provider inconsistency instead of bypassing the binding, deleting receipts, recreating a same-name Reader, editing provider databases, or signing out/resetting iCloud as a workaround.

Use the existing Obsidian app container in iCloud Drive for the Reader. Main and the private Journal stay outside that cloud service.

## Backup and conflict behavior

Existing Gallop-owned mobile content is backed up according to the exporter state before replacement/removal. Files that cease to be eligible are removed from the Reader only through the ownership/receipt path so stale sensitive copies are not deliberately retained by Gallop.

Cloud providers may independently retain deleted files, conflict copies, or version history. Gallop's local deletion cannot guarantee remote erasure.

## Retired Gallop-Mobile

`Gallop-Reader` is the supported destination. The former `Gallop-Mobile` path is retired and must not be restored as the active export target merely to bypass validation.

Historical backups can remain outside cloud storage. Do not delete/recreate the accepted Reader to clean up the retired path.

## Security boundary

Path validation, Cloud Files checks, filtering, receipts, backups, and atomic writes reduce accidental damage. They are not a security boundary against a hostile local process or machine owner.

See [Security](../SECURITY.md), [Real Tutor Integration](v1.2-real-tutor-integration.md), and the [real dogfood acceptance record](audits/v1.2-real-dogfood-acceptance.md).
