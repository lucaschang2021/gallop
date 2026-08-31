# Mobile reading mirror

`gallop mobile-export --source MAIN --target PATH/Gallop-Reader --state LOCAL_STATE`

Alternatively, `python -m gallop.mobile` supports the same arguments without
loading the backend CLI or its dependencies. Add `--dry-run` to inspect counts
without writing. All three paths are required: no backend configuration is
loaded, no canonical vault is moved, and no mastery store is opened for writing.

For iCloud on Windows, add `--icloud-safe`. This checks Cloud Files metadata
using read-only `CfGetPlaceholderInfo`, waiting at most 20 seconds per directory
for provider acknowledgement before submitting children. Exit 2 means a cloud
directory is not ready; it does not mean the Markdown content was rejected.
The exporter never edits iCloud's database, pin/exclusion flags or account state.
When ready, `--refresh` republishes the reading files even if identical, after
backing up their old mobile bytes locally.

## Reading policy

Only UTF-8 Markdown up to 5 MiB is exported. Allowed roots are the legacy five
numbered subject folders, Mathematics, Statistics, Finance, CS-AI, Practice,
Mistakes, Papers, Research, Research Notes, and Gallop/Sessions,
Gallop/Practice/learner, Gallop/Papers, Gallop/Research. Relative paths are
preserved for note links. Course Sessions are reading material; DeepTutor
backend sessions are excluded. See `gallop/mobile.py:ROOTS` for exact names.

Hidden/internal folders, logs, manifests, integration tests (including spaced
names and content flags), configuration, credentials, OAuth/tokens, mastery,
raw data and backend state are excluded. JSON, scripts, PDFs, images and other
opaque attachments are deliberately not copied in this minimal version.
Papers and Research Markdown notes are supported. Credential-shaped content
and `mobile_export: false` exclude the entire note. Pattern checks are defense
in depth, not a guarantee that every form of sensitive prose will be detected.
Do not put confidential material in these reading roots without opting out.

Today.md is a generated reading index, not a mastery or due-date calculation.
Mobile Sync Check.md is explicitly fictional sync evidence. Main .obsidian
settings/plugins are never copied. The exporter creates no mobile .obsidian
directory. It removes an empty legacy .obsidian directory but preserves any
nonempty settings created by the phone. Files/directories marked hidden or
system by Windows are also excluded even when their names have no leading dot.
Links to excluded system notes or non-exported attachments remain unresolved.

## Safety and ownership

The destination must be named Gallop-Reader and separate from the source.
Local receipt/backups must be outside both vaults and outside cloud storage.
First use requires an empty target except for its own .obsidian directory.
Symlinks and junctions, including ancestors, are rejected; Windows cloud
placeholder reparse points are allowed. Hardlinked source notes are skipped.

Subsequent exports overwrite owned files using Main as source. Previous mobile
content is backed up locally before replacement. Owned files removed from Main
or newly excluded are backed up locally and removed from Reader, preventing
stale sensitive reading copies from persisting there. Unknown files are left
alone unless a new source note uses the same name; that mobile file is backed
up locally before Main replaces it and takes ownership.
The tool does not reconcile iCloud-created conflict copies or unknown phone
notes; keep this vault for reading only. iCloud may retain cloud version history
and deleted files independently of this exporter.

Source scanning and conservative filename/path checks complete before updating
reading files. Reserved Windows names, unsupported characters, .nosync paths
and full paths of 256 or more UTF-16 code units are rejected without renaming
the source or silently breaking links. Each write is atomic;
the whole export is not a filesystem transaction. A local lock prevents two
exporters writing together. Interrupted exports can be rerun; after a crash,
confirm no exporter is active before removing LOCAL_STATE/export.lock.
Receipt ownership is journaled before file writes for replay. Never relocate
the source/state during an active export. File checks are not a security
boundary against a hostile process concurrently replacing filesystem paths.

Temporary reading payloads are now written under LOCAL_STATE/staging outside
the cloud tree, then atomically published under their final .md names. Thus
iCloud does not see transient .mobile-* files. LOCAL_STATE must be outside
cloud storage and on the same filesystem volume as Reader; no unsafe cross-
volume or in-place partial-write fallback is performed.

Read-only is a one-way workflow, not an iOS access-control restriction: phone
edits are possible but never flow back to Main. No scheduled task, watcher,
backend import hook, iCloud login change or network API is installed.

## iCloud and rollback

For a verified iPhone-created vault, use `--icloud-binding LOCAL_BINDING.json`.
The local binding records target path, Apple metadata database path, zone,
object UUID and parent ID. The exporter checks the read-only local/server
metadata, NTFS file ID and Cloud Files placeholder identity before any export
mutation, then repeats the check after scanning Main. A same-name directory or
an InSync icon alone is not enough. Unknown provider identity formats fail
closed. The successful receipt also records the bound cloud identity and
refuses a subsequent unbound run or silent change of object.

This is a safety gate, not a provider repair mechanism or proof of upload.
It never edits Apple's database, forces InSync flags or deletes/recreates a
cloud vault. Keep the old mirror and an outside-iCloud byte backup until E2E
acceptance. If the phone object is present in server metadata but the Windows
placeholder still holds an old object UUID, stop export and resolve the
provider inconsistency before adopting the new target. Do not bypass the
binding gate, remove the receipt, or create another same-name vault.

Use the **existing Obsidian app container** in iCloud Drive (with the app icon),
not an ordinary folder manually named Obsidian. Its Windows physical name may
be `iCloud~md~obsidian`. Confirm the actual container before setting the target.
On iPhone open Gallop-Reader in Obsidian and check Mobile Sync Check.md.

An existing Windows container directory is not proof that its cloud documents
root has been initialized. If iCloud reports `parent not found` when uploading
the Reader root, and children become excluded as orphans, initialize the vault
through iPhone Obsidian with **Store in iCloud** enabled. Merely rewriting
Markdown, removing .obsidian or creating a normal root folder cannot establish
that app-owned cloud parent. Do not manufacture records in iCloud's database.
See [Obsidian's guide](https://help.obsidian.md/sync-notes); it warns that iCloud
on Windows can duplicate or corrupt files. Main remains outside that service.

## Retired vault

Gallop-Reader is the only supported export destination. The former
Gallop-Mobile is retired: even an explicit legacy CLI target or old receipt
is rejected before any export mutation. Its historical migration records and
outside-cloud backups may remain, but must never be restored as active config.

The Reader has passed iPhone acceptance. Do not delete or recreate it to clean
up the former vault. If the old Windows placeholder disagrees with provider
metadata, leave that directory untouched; do not force removal, reset iCloud,
sign out, or edit provider databases/metadata. Keep the final outside-cloud
backup. In iPhone Obsidian vault management, remove only the old Gallop-Mobile
entry after preserving any phone-only notes; never remove Gallop-Reader.

To pause Reader export, stop invoking the Reader launcher. No background
service is installed by this exporter. Keep Main, Reader and local backups.
