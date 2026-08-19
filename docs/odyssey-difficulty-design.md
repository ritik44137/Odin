# Odyssey Difficulty Design

Difficulty is the funnel stage that rejects a well-built task. Structure,
oracle, and anti-gaming can all pass while the probe still fails.

Two independent failures:

- **Too short / not long-horizon.** Remaining expert work is a ticket
  (feature, repair, slice, stubbed module). Frontier-model failure does not
  rescue this. Collection bar: `docs/odyssey-long-horizon.md`.
- **Too easy.** Remaining work is large, but a frontier agent saturates it
  in one rollout (recall, recipe, visible-majority scoring, one-file fix).

The Odyssey guide is explicit: there is no local substitute for the
difficulty probe. This page is bar 2 (traps). Horizon is bar 1.

Adapted from Terminal-Bench / Terminus hardness research (probes, decoys,
chained failure modes, decorative hardening). Snorkel-only policy is not
copied: no mandatory ingest-staging-export shape, no `difficulty = "hard"`
metadata, no 18-test quota, no Case 6 ritual. Those would make every Odyssey
task look the same and would fail similarity.

Runtime context: `docs/harbor-task-anatomy.md`. File-level quality:
`docs/odyssey-quality-guidelines.md`. Local heuristic gate:
`scripts/check_difficulty_design.py`.

## What the probe actually measures

After structure, similarity, oracle/nop, and quality, Odyssey runs independent
frontier-agent trials at the full agent time budget (at least 7200s, collection
target 4-10h). Failure modes:

- **Too short / not long-horizon.** The remaining `/app` work is ticket-sized
  relative to this collection (SWE-Marathon-scale system clones). Agents
  scoring 0.0 does not change that verdict.
- **Too easy.** The agent saturates the reward. A one-shot or a shallow patch
  that scores well is a fail, even if a human would call the problem "fiddly".
- **Too hard / unsolvable.** No fair path exists: missing spec, contradictory
  tests, broken image, hidden rules that are not in `/app`. That is not
  difficulty; it is a broken task.

`expertTimeEstimateHours` is unconstrained on the form. Locally, remaining
work below 40 honest expert hours is treated as too short. Padding the
number, or the agent clock, on the same module does not pass. Hours also
do not replace a first-attempt trap.

Terminus published numeric bands (Hard <= 20% on best or worst, reject if
worst > 80%). Odyssey does not publish those numbers in the authoring guide.
Design as if a frontier coding agent must not one-shot the task and must not
be blocked by unfairness. Local heuristics cannot certify that; they only
catch shapes that almost always saturate.

## Where difficulty actually lives

Difficulty is a property of the *interaction* between starting state,
instruction, decoys, and the grader. It is not a property of word count,
file count, or pytest count.

| Lever | Makes it harder for a model | Does not |
|---|---|---|
| Starting state | Real incomplete or wrong code whose conventions must be inferred | Empty `/app` plus "implement LRU" |
| Instruction | Scenario + absolute paths + cited contracts in `/app` | Numbered fix recipe, bug file names, golden values |
| Decoys | Obvious files/docs that look like the work but are off the graded path | Fake files the tests require (those are not decoys) |
| Visible tests | Enough to aim; a minority of the score | A checklist that is the whole grader |
| Hidden tests | Different failure mode, generated/property cases | The same bug as visible, restated |
| Scoring | Hidden groups hold the majority of reward | Visible weight >= 50% (shallow patch looks "almost done") |
| Oracle | Derives by editing several interacting modules | Echo goldens; one-file tutorial |
| Domain | Bespoke rules among common patterns | Textbook exercises, saturated interview problems |

## Mechanisms (use these; do not clone a template pipeline)

Terminus learned that agents pass when every task is the same ingest ->
staging -> export CLI with checksum bugs. Do not copy that shape. Copy the
*mechanisms*:

### 1. Interaction, not a list of independent bugs

Bugs or incomplete parts must compose. Fixing module A still fails hidden
checks until B and the A-B interaction are correct. Sequential bugs (fix A,
then B, all green) are one easy problem repeated.

Prefer wrong order, wrong aggregation, wrong canonicalization, wrong scope,
wrong binding, over a typo in one string.

### 2. Decoys (off the hot path)

A decoy is a file, helper, or doc that *looks* like the fix target and is
not on the graded hot path.

- The instruction may say to ignore it, or it may sit as realistic clutter.
- Patching **only** the decoy must leave hidden groups failing. If that patch
  passes, the export/hot path still uses the decoy: it is not a decoy.
- Dual decoy: two obvious files; the real work is a third stage.
- Decoy docs that give plausible wrong advice (sort vs merge order, count vs
  sum) are useful when tests grade the contract, not the decoy.
- A decoy the tests require is part of the solution, not a decoy.
- Decoy count is not a CREATE ritual. Zero is valid for a tight library
  whose difficulty is in the spec. When `/app` has several plausible
  modules, at least one decoy is the default.

### 3. Independent hidden traps

Hidden tests must fail for a **different root cause** than the visible set.
If one operator fix turns both visible and hidden green, the split is
decorative.

Fairness limit: hidden traps stay inside the stated contract in `instruction.md`
and `/app` docs. Vary inputs and check invariants. Do not invent secret
requirements that exist only in `tests/hidden/`.

### 4. Almost-correct traps

At least one hidden case where a plausible wrong fix (numeric sort instead of
merge order; LCS instead of Myers; whitespace-normalized shrink) passes some
visible asserts and fails the hidden reference.

### 5. Generated / property hidden cases

Enumerated fixtures can be memorized. Property checks over generated input
(sortedness, round-trip, union, idempotence, SES-minimality) are a separate
channel. Perturb the input: the output must change.

### 6. Persistence and cross-run (when the domain has state)

If the product has a ledger, journal, or restart, an export-only fix must
still fail replay/idempotency/cross-run hidden tests. If the domain has no
state, do not bolt on a fake database to look hard.

### 7. Doc discovery, not prompt recipes

Put algorithms, field order, and edge semantics in `/app` contracts the
instruction cites. Agents that only read `instruction.md` should miss
something the hidden tests grade. One doc that spells the entire fix is a
spec leak.

### 8. Behavior, not grep, not test inflation

35 tests of the same root bug still saturate. Keep independent channels:
behavior, invariants, edge cases, family metric. Drop duplicates.

## How tests, verifiers, and graders set difficulty

Harbor runs `tests/test.sh`, which must write a float reward in `[0,1]`. The
difficulty probe sees that float. A visible-only patch that scores 0.70 looks
like a mostly-solved task even if the binary gate fails.

Rules for `tests/test.sh` groups:

- **Visible** states what "done" means. Weight it as a minority (this repo's
  exemplar uses 0.30). Never give visible >= 0.50 of total weight.
- **Hidden enumerated** uses cases the visible set does not contain.
- **Hidden invariants / generated** is a separate group so a hard-coded table
  for the enumerated hidden cases still fails.
- Binary success still requires every group. Partial credit must rise only
  with real progress.
- Grade from a directory the agent does not control, through the public API.
- Oracle and agent face identical tests. No `EVAL_IS_ORACLE`.
- Do not put an end-to-end solver in `tests/`.
- Do not assert p50/p95 wall-clock as fake hardness, and do not pass the
  agent for scoring within 95% of the oracle.

The local proof that still has to be run by hand:

| Probe | What you do | PASS |
|---|---|---|
| V -- visible-only | Smallest patch that satisfies `tests/visible` | Partial credit, binary fail, hidden groups red |
| D -- decoy-only | Fix only the obvious decoy file(s) | Hidden / hot-path groups still fail |
| L -- one layer | Fix only the first stage or one module | Later hidden groups still fail |
| A -- almost-correct | Apply the plausible wrong algorithm | Some visible pass, hidden fail |

If probe V passes fully, the hidden split is decorative. If D or L pass
fully, interaction depth is missing.

## Decorative hardening (do not ship)

These look like "we made it harder" and still saturate:

- New output field / hash column + matching tests, same root bugs
- Longer docs that spell the algorithm; instruction unchanged
- More pytest on the same code path
- Relabeling difficulty in prose without changing `/app` or tests
- Hidden tests that fail for the same operator as visible
- Reviewer nits answered by putting the recipe into `instruction.md`

## Unfair (not difficulty)

Do not "harden" by:

- omitting a rule the tests require
- making output time-dependent or networked
- contradicting `/app` docs
- requiring a tool that is not in the image
- listing bug file names in the instruction (that eases, it does not harden)

Fairness fixes (docs match tests, oracle 1.0, NOP at floor) are mandatory.
Hint injection is forbidden even when a reviewer asks for "more guidance".

## Family-shaped hardness

Instruction, `/app`, and tests must all look like the declared family, and
the difficulty must live where that family is actually hard:

- **Library clone** -- reimplement a complete protocol, compiler, decoder,
  LSP, or control plane; generated hidden cases over that surface; not a
  nested-syntax ticket or a textbook algorithm.
- **Product clone** -- full application clone (API, persistence, jobs,
  product surface); decoy services; not one workflow slice.
- **ML engineering** -- train/post-train/port/kernel under a hard cap, or a
  multi-dataset harness; a dummy artifact cannot fake the metric.
- **Algorithmic optimization** -- correctness-preserving speedup of a
  substantial solver or custom-ISA kernel; the obvious flag-flip is not
  the speedup.

## Draft field: `difficultyExplanation`

Write what a strong model gets *wrong* on the first attempt, **and** the
subsystems still to build. Do not write only "it is complex", only "it takes
many hours", or only "frontier models fail". Name remaining-work surface,
traps, decoys, almost-correct algorithms, and the independent hidden failure
modes.

## What this repo will not copy from Terminus

- Mandatory ingest -> staging -> export for every slug (similarity poison)
- `difficulty = "hard"` in `task.toml` (Odyssey has no such key)
- Quotas such as ">= 18 tests" or ">= 5 modules" as a substitute for
  interaction (test inflation)
- Asking `decoys: N` before build (decoys are a design choice, not a prompt)
- Treating unsolvable tests as hardness

Use Terminus as evidence of which *shapes* saturate frontier agents, not as
a second platform.

Workflow: ENGINE_1 refuses ideas with no first-attempt trap **or** ticket-sized
remaining work; ENGINE_3 implements the mechanisms on a collection-scale
system; ENGINE_8 hardens a solvable-but-easy task without cloning Case 6.
Router: `.cursor/rules/09-engine-router.mdc`.
Map: `docs/odyssey-engines.md`. Horizon: `docs/odyssey-long-horizon.md`.
