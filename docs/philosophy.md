# Philosophy

Gallop is built around one proposition:

> **AI should organize deliberate practice and mentorship without outsourcing the learner's thinking or fabricating evidence of capability.**

The v1.2 product boundary expresses that operationally:

> **GPT = TEACH · GALLOP = GOVERN · OBSIDIAN = REMEMBER · EVIDENCE = PROVE**

## Training principles

- **Deliberate practice** targets observed weaknesses and prerequisites.
- **Retrieval practice** asks the learner to produce knowledge from memory.
- **Active recall** precedes explanations and solutions when independence is being trained.
- **Productive struggle** is expected, bounded, and distinguished from prerequisite failure or overchallenge.
- **Scaffolding fades** as evidence supports greater independence.
- **Mastery requires multiple kinds of evidence**, not one answer or one model judgment.
- **Transfer** tests whether understanding survives a changed context.
- **Retention** requires evidence after time has passed.
- **Independent reasoning** remains a first-class outcome.
- **Targets stay high while current capability stays honest.** Aspiration never upgrades state.

Gallop does not optimize for reaching the answer as quickly as possible. It tries to discover what the learner cannot yet do independently and arrange work that is difficult in the right way.

> **Use AI to make learning harder in the right ways, not easier in the wrong ways.**

## Tutor versus authority

The GPT Tutor owns explanation, questioning, dialogue, and pedagogical presentation. Gallop owns the evidence boundary, continuity, replay, and progression policy.

A Tutor may observe a mistake or propose an assessment, but that remains observation/candidate evidence until the applicable confirmation and deterministic evidence rules admit it. “The GPT says you mastered it” is never a mastery transition.

Fresh-chat continuity follows the same principle: a new Tutor receives bounded Journal-derived context rather than treating old transcript prose or model memory as truth.

## Hint and assistance gradient

Assistance is evidence about how performance occurred. A useful conceptual gradient is:

| Level | Intervention |
|---:|---|
| 0 | independent attempt |
| 1 | direction / clarification |
| 2 | key observation |
| 3 | skeleton / partial structure |
| 4 | substantial solution exposure |

v1.2 also records richer designed scaffolding and agent provenance. Success after substantial help is valuable learning activity, but it is not equivalent to independent completion.

## No-agent learning

For coding and other independence-sensitive tasks, `NO_AGENT_CODING` / no-agent conditions make the assistance boundary explicit. The goal is not punishment or tool abstinence for its own sake; it is to obtain truthful evidence about what the learner can produce without the capability being supplied by an agent.

AI-assisted and AI-generated work can still be recorded as learning activity. It simply cannot be relabelled as independent evidence.

## Evidence before optics

Gallop should prefer an honest weak result over an impressive but unsupported state. The v1.2 real dogfood acceptance followed this rule: a partial independent retest stayed `GUIDED` rather than being promoted to make the acceptance look stronger.

The system therefore optimizes for **truthful capability growth**, not flattering dashboards.
