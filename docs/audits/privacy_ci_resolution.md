# Privacy CI Resolution

Status: IMPLEMENTED — OPTION B

Candidate: `8bc4dbf7e55f6bbb33f921cf25e2f64e2dafe36b`

Resolution date: 2026-09-13

## Finding and reachability

The repository privacy audit found one category of violation:
`non-noreply-email` in historical commit
`99c21ce0b38b548b389da6a15d546cfd47314ed7`.

That commit is the merge of documentation PR #3. It is an ancestor of the RC2
candidate and is reachable from `main` and `feat/elite-training-v1.1`, so a
full-history audit correctly sees it. No tracked blob, secret, private key,
machine path, large/unexpected binary, or private learning-data directory was
reported in the current 265-blob scan.

## Selected remediation

Option B is selected: an immutable accepted-debt baseline contains only the
offending commit object ID. The baseline deliberately does not copy the private
email address into a current file.

History is not rewritten because the offending merge is already shared and
reachable from `main`. Rewriting would change all descendant SHAs, require a
coordinated force push, invalidate the frozen RC2 candidate, and create more
delivery risk than the historical metadata item itself.

## Gate behavior

The privacy audit now evaluates every commit reachable from the selected audit
revision as an `(object ID, author email, committer email)` record. CI supplies
the exact push SHA or pull-request head SHA, so GitHub's synthetic PR merge
commit is not mistaken for repository-owned history; the rest of the PR suite
still exercises the normal merge checkout.

- A non-public email on the one exact accepted historical object is classified
  as accepted existing debt.
- A non-public email on any other commit remains a failing
  `non-noreply-email` finding.
- An invalid or duplicated baseline entry fails the audit.
- If the accepted commit disappears or its metadata is repaired, the obsolete
  entry fails as `stale-accepted-metadata-debt` until the baseline is removed.
- Blob and private-data scanning is unchanged and has no accepted-debt bypass.

This keeps the privacy/security implication explicit: the old address remains
in already-published Git metadata, but no future private commit metadata is
permitted and no content-scanning rule is weakened.

## Rejected alternatives

- Disabling or removing the audit would make future regressions invisible.
- Globally allowing private email metadata would turn a one-object exception
  into an open-ended bypass.
- Rewriting shared history is disproportionate for this closure and would
  destroy the candidate-SHA continuity required by the governance task.
