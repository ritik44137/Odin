# Bad Example: Ambiguous Objective

## Why this is bad

This example looks plausible at first glance, but it would create major review and verifier problems because the actual deliverable is underspecified.

## Weak draft excerpt

**Title:** Improve the parser

**Objective:**
Make the parser better and more robust. It should handle more cases and generally work like users expect. Update the implementation as needed and make sure it passes the tests.

## Problems

- The core deliverable is unclear.
- There is no bounded definition of what "better" means.
- It depends on unspecified user expectations.
- The objective offloads too much meaning into hidden tests.
- A reviewer cannot infer the intended bundle or acceptance criteria.

## Better pattern

Replace vague improvement language with concrete behavioral scope, preserved invariants, explicit success conditions, and a verifier strategy that measures the real target behavior.