---
name: Bug report
about: Report a reproducible Gallop problem using synthetic/sanitized data
title: ''
labels: ''
assignees: ''
---

Do not post private learner notes/answers, Journal data, Vault/Reader paths, credentials, cloud metadata, or provider logs. For vulnerabilities, follow `SECURITY.md` instead of opening a public issue.

## Environment

- Gallop source version or exact commit:
- OS and Python version:
- Surface: Tutor MCP / Runtime Bridge / Journal / Progressive Mentorship / Obsidian projection / Gallop-Reader / Automation V1 / legacy adapter:
- Subject, if relevant: Mathematics / Statistics & Econometrics / Finance / CS & AI:

## Synthetic reproduction

Provide the smallest fictional reproduction. Remove private configuration and machine-specific paths.

## Expected and actual behavior

What should have happened? What happened instead?

## Authority / recovery impact

- Was an event committed to the Journal?
- Did replay remain valid?
- Did projection/Reader fail after a successful commit?
- Was duplicate/idempotent behavior involved?
- Did the bug risk treating candidate/assisted/generated work as independent evidence?

## Validation details

Include sanitized error codes and relevant test names. State clearly whether evidence came from a synthetic test, isolated real integration, or real learner workflow, and whether an external provider/cloud service was involved.
