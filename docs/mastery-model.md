# Mastery model

Gallop represents mastery as evidence-backed state, not a quiz score.

| Level | Meaning |
|---:|---|
| 0 | unseen |
| 1 | exposed |
| 2 | basic understanding |
| 3 | guided application |
| 4 | independent application |
| 5 | robust mastery |

## Evidence considered

1. correctness;
2. independent completion;
3. hint usage;
4. repeated performance;
5. delayed recall;
6. transfer problems;
7. oral explanation;
8. difficulty.

## Safety rules

- No attempt means no transition.
- Weak evidence may lower an overconfident state.
- Guided success can establish basic or guided application.
- One excellent quiz cannot produce level 5.
- Level 5 requires repeated independent performance plus delayed recall,
  transfer, and oral evidence.

The v0.1 algorithm is intentionally conservative and deterministic. Future
versions may improve calibration without changing the protocol's evidence model.

