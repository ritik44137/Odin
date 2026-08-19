# Bad Example: Decorative Hardening

## Why this is bad

Terminus measured this failure repeatedly: authors added fields, docs, and
pytest while the bugs stayed sequential. Frontier agents still scored 5/5.
Odyssey's difficulty probe will do the same. Extra tests of the same root
cause are not difficulty.

## Weak revision excerpt

Keep the one-file off-by-one in `/app/export.py`. Add `audit_hash` to the
report, document the hash in `/app/docs/hash.md`, and add four tests that
assert the hash is 64 hex characters. Set the write-up to say the task is
now hard.

## Problems

- The new field is free once export math is fixed. Agents do it in the same
  pass.
- Hidden tests fail for the same operator as visible tests.
- Metadata and prose do not change pass rate.
- A visible-only patch still scores most of the reward if visible weight is
  high.

## Better pattern

Add an independent failure mode that must be correct at the same time:
wrong aggregation vs wrong canonicalization, a decoy module off the hot
path, an almost-correct algorithm that passes visible fixtures, generated
hidden inputs. Run probes V/D/L/A. See `docs/odyssey-difficulty-design.md`.
