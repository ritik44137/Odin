# Bad Example: Too Short for the Collection

## Why this is bad

Automated Difficulty can fail a well-built, oracle-passing, model-failing
task with "Too short for the collection -- not long-horizon". That verdict
is about remaining expert work, not about frontier-model trials and not
about whether agentTimeoutSec is already 7200.

Odyssey's families are collection-scale Harbor work (complete library
reproductions, full-stack product clones, training-under-cap, custom-ISA
or solver optimization). Ticket-sized Terminal-Bench 2 work is the wrong
caliber. Raising hours or the clock on the same module does not pass.

## Weak draft excerpt

**Title:** Implement support for nested inline tables

**Objective:**
Update an existing TOML parser so nested inline tables parse and reject
duplicate keys. Done means visible regression tests pass.

**Difficulty explanation:**
Frontier coding agents fail the hidden duplicate-key cases on the first
attempt, so the task is long-horizon.

**Expert time estimate:** 8 hours (later padded to 32 without adding subsystems)

**Agent timeout:** 7200s, then 28800s on the same /app

## Problems

- Remaining work is a parser feature, not a complete library, protocol,
  compiler, or product.
- The difficulty explanation uses model failure as a substitute for
  horizon. The judge can see the /app surface.
- Padding expert hours and agent timeout on the same three functions
  (or even on a fuller merge module) still reads as a ticket.
- SWE-Marathon-scale peers are "rebuild the framework", "multi-pass
  compiler with codegen", "clone the full product", not "add nested tables".

## Why "the model failed it" does not fix it

The probe runs frontier agents. That does not mean every task those agents
fail is in-collection. A sitting's worth of remaining work is out even when
the agent scores 0.0.

## Better pattern

Name a complete system the oracle still has to build (>= 40 honest expert
hours, 4-10 hour agent budget): reimplement a wire protocol and planner,
clone a full-stack product, train under a hard cap with a multi-dataset
harness, or beat a conflict/cycle target on a real solver with proof
logging. Then add traps on that surface.

See `docs/odyssey-long-horizon.md`.
