# Automation V1

Automated learning operations, not automated learning. This is a local,
event-driven CLI. There is no daemon, account scraper, web UI, autonomous
researcher, or automatically completed training.

## Authority and compatibility

For new Automation V1 inputs, the append-only event journal is authoritative.
Learning state, training queues and Markdown are derived views. The legacy
sync-session/import-result workflows and their historical state are preserved;
Automation does not read Markdown to guess mastery and does not silently
import or rewrite legacy mastery. An empty Automation root means no evidence,
not that a person's historical knowledge is zero.

Use the existing Tutor Output Protocol v1. Concepts can be strings or objects
with a name. Optional arrays may be omitted or empty. Original bytes and
extension fields are retained. [Protocol details](tutor-protocol.md).

## Start in an isolated namespace

The example configuration in examples/automation/config.json uses relative
paths resolved against the configuration file, all inside automation-runtime.
The root must initially be empty. Runtime state must not be committed.

~~~bash
python -m gallop --automation-config examples/automation/config.json intake examples/automation/session.json
python -m gallop --automation-config examples/automation/config.json queue
python -m gallop --automation-config examples/automation/config.json cycle
~~~

This example is explicitly synthetic. Its Reader is a local preview, never the
real cloud Reader. An integration configuration cannot target an outside vault
or a bound iCloud Reader, and a bound root cannot switch namespaces.

For real operation, create a private configuration with namespace learner,
an empty private event root outside both vaults, the existing main vault and
Reader paths, and the existing mobile export state and iCloud binding. Do not
create a replacement Reader or reset the export receipt. Optional deeptutor and
deeptutor_home select the already installed engine. No provider credentials
belong in this configuration.

## Normal learning

1. Save the tutor's truthful v1 JSON package. Run intake on that file, or deposit
   it atomically into the private root's pending-intake directory and run cycle.
   Existing 99-Inbox delivery and its legacy synchronizer are not replaced or
   watched by Automation; intake can also read an explicit file from that flow.
2. Inspect queue and explain. prepare creates a stable manifest, a human task
   specification and an incomplete result template. prepare --send explicitly
   submits a durable DeepTutor job and returns its ID. Use poll JOB_ID and
   collect JOB_ID to recover the questions before starting training.
3. Run start QUEUE_ID --confirm when the learner actually starts the work.
4. Save the actual response and have a human assess it. Fill the prepared result
   template honestly; null counts and ungraded outcomes are intentionally invalid
   for assessed import. Run ingest-result FILE --confirm-human.
5. Run cycle to refresh views and publish through the existing Reader exporter.

Raw inputs are retained, even if malformed. Same session ID and normalized
content is idempotent; same ID with changed content fails. Results also bind to
queue, manifest, practice, subject and concept. A new result ID cannot recount an
already accepted practice. Inputs are never deleted or moved automatically.
Pending files remain replay-safe; archive them manually after acceptance if desired.

## Recovery and limitations

The process lock serializes CLI mutations and publishing. SQLite transactions
commit evidence and its transition audit together; derived state is replaced
after commit. A cache left behind after a crash can be rebuilt from a verified
journal prefix. A modified cache fails closed and is backed up before comparison.
The public rules are version 1; changing them requires an explicit migration.

Each projection file is atomic, but all files plus iCloud are not one distributed
transaction. Retry cycle after an I/O or cloud failure. The journal remains the
recovery source. Human edits inside a managed area cause a conflict instead of
being overwritten. The OS releases the new writer lock on process exit. A legacy
operation.lock remains a fail-closed ownership check; it is not deleted automatically.

DeepTutor submissions persist separately from learner evidence. The lifecycle is
prepared -> submitted -> running -> completed / failed / timed_out. A deadline
marks waiting as timed_out; it does not kill the provider or discard its output.
Poll or collect the same job again for a late result. Only a proven stopped failed
attempt can be retried with submit QUEUE_ID --retry; uncertain spawn ownership
fails closed. Each attempt retains its records. Repeated collection and recovery
after journal commit do not invoke the provider or add duplicate evidence.
Prepared files can be restored from their immutable prepared event. Provider
exactly-once execution is not claimed across an indeterminate OS spawn failure.

The journal uses SQLite triggers and a hash chain for accidental modification
detection; it is not a tamper-proof trust boundary against its machine owner.
Human confirmation is an explicit local attestation, not proof of authorship or
proctoring. [Safety rules](automation-safety.md), [CLI](automation-cli.md),
[DeepTutor bridge](deeptutor-integration.md).
