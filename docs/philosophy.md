# Philosophy

Gallop is designed around one proposition: AI should organize deliberate
practice, not outsource thinking.

## Training principles

- **Deliberate practice** targets specific observed weaknesses.
- **Retrieval practice** asks the learner to produce knowledge from memory.
- **Spaced review** revisits evidence after time has passed.
- **Active recall** precedes explanations and solutions.
- **Productive struggle** is expected, bounded, and sustainable.
- **Hint gradient** reveals only as much structure as needed.
- **Mastery learning** requires multiple kinds of evidence.
- **Transfer** tests whether understanding survives a changed context.
- **Independent reasoning** remains a first-class outcome.

Gallop does not try to help learners reach answers as quickly as possible. It
tries to discover what they cannot yet do and arrange training that is difficult
in the right way.

> Use AI to make learning harder in the right ways, not easier in the wrong ways.

## Hint gradient

| Level | Intervention |
|---:|---|
| 0 | independent attempt |
| 1 | direction only |
| 2 | key observation |
| 3 | skeleton or partial structure |
| 4 | full solution |

Hint use is evidence. Success after a full solution is not equivalent to
independent completion.

## No-agent learning

A practice manifest can set `no_agent: true`. In this mode the practice engine
must not immediately produce a complete solution; it should advance through the
hint gradient only when requested. This is particularly useful for proofs,
derivations, algorithms, coding, and statistical reasoning.

