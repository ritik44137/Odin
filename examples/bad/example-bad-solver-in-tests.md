# Bad Example: Solver Lives in tests/

## Why this is bad

The verifier must measure the agent's artifact, not regenerate it. If deleting
`solution/` still lets `tests/` compute the complete expected output, the
oracle is decorative and a capable agent can import the test helper instead of
doing the work.

## Weak verifier excerpt

```python
# tests/hidden/test_edge_cases.py
from task_lib.oracle import parse_spec_reference  # full solver

def test_matches_reference():
    for spec in HELD_OUT_SPECS:
        assert agent_parse(spec) == parse_spec_reference(spec)
```

`parse_spec_reference` is the complete implementation. Shipping it under
`tests/` means the hidden suite *is* the answer key.

## Problems

- The test contains an end-to-end solver. That callable belongs in `solution/`.
- An agent that can see or reconstruct the helper gets full reward without
  implementing the library.
- Oracle 1.0 no longer proves solvability of the *task*; it only proves the
  helper agrees with itself.
- Property checks that reimplement the spec in the test file have the same
  failure mode when the reimplementation is a drop-in replacement.

## Better pattern

Grade through the public API against sealed fixtures, hashes, and invariants
the test can state without producing the artifact (sorted, unique, union of
segments, `ParseError` on invalid input). Generate held-out specs; do not
ship a second implementation next to them. `solution/solve.sh` is where the
real parser rewrite lives.
