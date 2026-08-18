# Bad Example: Easy for the Wrong Reasons

## Why this is bad

The difficulty probe runs independent frontier-agent trials at the full time
budget. A task the agent saturates immediately fails, and nothing in this repo can
predict that for you — it is the one funnel stage with no local substitute. So it
has to be designed for at the idea stage.

## Weak draft excerpt

**Objective:**
Implement an LRU cache class with `get` and `put` methods, both O(1). Capacity is
fixed at construction; evict the least recently used entry when full.

**Difficulty explanation:**
This is difficult because it requires understanding both a hash map and a doubly
linked list, and the pointer manipulation during eviction is error-prone. Getting
all the edge cases right takes care.

**Expert time estimate:** 3 hours

## Problems

- It is a canonical interview exercise. A frontier model has seen thousands of
  correct implementations and will emit one on the first attempt, so the trial
  measures recall rather than engineering.
- The difficulty explanation describes what makes the problem *fiddly for a human*,
  not what makes it hard for a model. Those are different, and the probe measures
  the second.
- The expert estimate is inflated relative to the actual work, which reads as
  padding rather than an honest figure.
- Every edge case is enumerable from the problem statement alone, so hidden tests
  add coverage but no resistance.

## Why "add more requirements" does not fix it

Bolting on thread-safety, a TTL, and metrics makes the task longer without making
it harder: each addition is independently well-known, so the agent solves four easy
problems in sequence. Scale is not difficulty.

## Better pattern

Put the difficulty somewhere a model cannot retrieve an answer from:

- behaviour that must be inferred from an existing codebase rather than a spec,
  where the surrounding conventions constrain what a correct fix looks like
- an interface ambiguity that is only resolvable by reading how callers depend on it
- a real invariant that a natural-looking implementation violates under a case the
  visible tests do not cover
- a performance target that is reachable only after understanding *why* the current
  implementation is slow, where the obvious optimization is not the effective one

A useful test of the idea: if you can imagine the correct solution appearing in a
textbook, the probe will treat it as recall. State in `difficultyExplanation` what a
strong model gets *wrong* on the first attempt, and why.
