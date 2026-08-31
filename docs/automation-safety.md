# Automation Mastery Safety Gate

The state engine is deterministic and separate from the legacy mastery engine.
No imported summary, compliment, claimed mastery or model grading number is
allowed to promote a learner. Sessions record course exposure, questions and
reported weaknesses. They never become proof of student mastery.

## Evidence and transition rules

Practice events record attempts; separate confirmed assessment events record
outcomes. Every resulting state update has a reason and evidence references in
an immutable state_transition event. A result requires a confirmed start, correct
queue/manifest/practice linkage, actual response references, plausible counts,
valid timezone-aware timestamps and human confirmation.

| Evidence available | Maximum eligible level |
| --- | --- |
| Exposure, praise, one attempt, hints only, or one day | No promotion |
| Independent success on at least 2 separate days | 2 |
| At least 3 days and 2 task types | 3 |
| At least 4 days and 3 task types | 4 |
| At least 5 days, 3 types, a 30-day span, oral evidence and transfer | 5 |

Every accepted assessment can increase at most one level, even if a higher
ceiling is eligible. Passing requires at least 80% human-confirmed success;
hinted or dependent work does not count toward independent evidence thresholds.
Failure increases mistake/weakness evidence and lowers confidence, but does not
mechanically reset mastery. Counts are performance evidence, not proof of truth.

Confidence is low initially, medium after independent success on two separate
days, high after four days across three task types, and low after a failure.
Therefore an established mastery level and low confidence can coexist.

Concept state includes subject, concept, mastery_level, confidence,
evidence_count, last_seen, last_practiced, mistake_count, success_count,
weakness_tags, open_questions, evidence_refs and an explanation history.
Session-level weakness tags and questions are context for the session's concepts;
mistake counts are assigned only to an explicitly matching concept or a session
with one concept. Empty arrays never create invented observations.

## Isolation

Synthetic and integration markers are rejected by learner intake. Results must
explicitly match the bound namespace. Integration roots contain their own vault,
Reader and export state and cannot use an iCloud binding. No integration data is
published to the real Reader. The old mobile vault remains rejected.

Markdown is a view. Free text outside Gallop's managed markers is preserved,
including existing learning-sync regions. Unknown files are never deleted.
Edits inside a managed region fail closed. Only privacy-filtered Markdown views
enter Reader; journals, mastery JSON, raw inputs, answer keys, settings, logs,
backend sessions and credential files stay outside it.

Missing historical evidence means unknown, not permission to invent it.
Automation never silently seeds mastery from legacy JSON or edits old sessions.
