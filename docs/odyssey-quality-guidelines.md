# Odyssey Quality Guidelines

File-level quality bar for a Harbor bundle, adapted from Terminal-Bench Edition 2
and from Terminus verifier-integrity rules. These sit on top of the draft funnel
in `source-of-truth.txt`. A task can pass structure checks and still fail here.

The matching Cursor rules are `05-instruction-writing.mdc`,
`06-environment-and-docker.mdc`, `07-oracle-verifier-and-quality.mdc`, and
`08-difficulty-design.mdc`. Difficulty (decoys, grader weights, probes V/D/L/A)
is `docs/odyssey-difficulty-design.md`.
Mechanical pieces are enforced by `scripts/scan_bundle_leaks.py`,
`scripts/check_difficulty_design.py`, and `scripts/validate_odyssey_task.py`.
The rest is author judgement, checked in probes V/D/L/A and the oracle/nop pair.

## What a good task is

A good task is one an expert human can solve from the materials in `/app` and
`instruction.md`, but that challenges a frontier coding agent. Difficulty comes
from multi-step reasoning, interface ambiguities that must be resolved from
code, compounding failure modes, or invariants a natural-looking implementation
violates. It does not come from trivia, missing information, or a broken image.

Hard requirements:

1. **Multi-step.** Intermediate state, more than a single command or a one-liner.
2. **Clear.** Fully specified with absolute paths and checkable outputs. No guessing.
3. **Testable.** Deterministic tests on the final environment state.
4. **Sealed.** The agent cannot peek at tests, edit golden data in `/app` to pass,
   delete tests, or hard-code held-out outputs.
5. **Solvable.** `solution/solve.sh` reaches full reward under the same conditions
   the agent will get.
6. **Floor.** The untouched state sits at the declared nop floor, with a real gap.

## QG1 to QG8 (adapted)

Terminal-Bench Edition 2 used these as pack-fail rules. Odyssey keeps the intent
and drops the parts that conflict with Odyssey families (especially algorithmic
optimization, which may grade a stable performance metric).

| Id | Rule | Odyssey reading |
|---|---|---|
| **QG1** | No flaky latency tests | Do not assert p50/p95/p99 or raw wall-clock milliseconds. A performance family task may grade a stable metric (ops under a fixed workload, memory ceiling, complexity bound) but not a noisy timer. |
| **QG2** | Identical testing for oracle and agent | No `EVAL_IS_ORACLE`, no `/oracle`-only chmod, no oracle-only env in `test.sh`. Same checks, same files, same permissions. |
| **QG3** | Compose is explicit | If you ship `docker-compose.yml`, the task is multi-container and the instruction and `task.toml` must say so. Prefer a single Dockerfile unless the objective requires several services. |
| **QG4** | No runtime web fetch | No `curl`/`wget`/`requests.get` in `solution/`, `tests/`, or runtime scripts under `environment/app/`. Bake data and packages at image build. |
| **QG5** | No Harbor reserved dirs in the image | Do not `mkdir`/`COPY`/`chown` `/tests`, `/solution`, `/oracle`, or `/logs/verifier`. Harbor mounts those. |
| **QG6** | Always write a reward | `tests/test.sh` writes `/logs/verifier/reward.txt` (or `reward.json`) on success and on failure. Never `exit` before the write. An `EXIT` trap is the reliable pattern. |
| **QG7** | Default the env vars you use | If the verifier reads `TEST_DIR`, default it (`TEST_DIR="${TEST_DIR:-/tests}"`) or locate the suite via `$0`. Do not require the harness to set a custom variable. |
| **QG8** | No oracle-replication thresholds | Do not pass the agent for scoring within 95% of the oracle. Thresholds describe meaningful completion of the objective, not mimicry of `solve.sh`. |

## Verifier integrity

End-to-end solution generation lives in `solution/` only.

Legitimate in `tests/`:

- run the agent's binary, CLI, or public API and parse its output
- precomputed golden fixtures and hashes that the agent cannot see
- spec-derived invariants (sortedness, budgets, digests, schema)
- sealed held-out truth
- perturbation / holdout re-runs (output must change when input changes)

Forbidden in `tests/`:

- a callable that maps task inputs to the complete expected artifact
- re-declaring config values the instruction says must be read from a varying file
- grepping the agent's source for implementation tokens
- installing packages at grade time

Rule of thumb: if deleting `solution/` still lets the test compute the expected
answer in full, the test is doing the solving.

## Common errors

### Instruction

| Anti-pattern | Fix |
|---|---|
| "make it better", "fix the issues", "optimize the code" | Concrete metrics, absolute paths, error codes, complexity bounds |
| Relative paths (`config/settings.json`) | Absolute (`/app/config/settings.json`) |
| "save the results" with no destination | Named path plus schema |
| "use vim" / unverifiable tools | Verifiable outcome on a file or process |
| Stepwise recipe, detection guide, golden numbers | Requirements only; contracts in `/app` |

### Tests

| Anti-pattern | Fix |
|---|---|
| Whole-file string equality | Key fields / structured asserts |
| `assert "sorted(" in source` | Behavior via CLI or public API |
| Order-dependent shared globals | Independent setup per test |
| Hardcoded random outputs | Seeds or property checks |
| Runtime `apt`/`pip`/`npm`/`curl` in `test.sh` | Bake deps in the Dockerfile |

### Oracle

| Anti-pattern | Fix |
|---|---|
| `echo` of hardcoded goldens | Patch `/app` and run real logic |
| Unordered `ls` dumps | Stable sort / canonicalization |
| Continues after errors | `set -euo pipefail`; fail fast |
| Fetches at runtime | Bake whatever `solve.sh` needs |

### Environment

| Anti-pattern | Fix |
|---|---|
| `COPY tests/` or `COPY solution/` | Harbor mounts those trees; copy only `app/` |
| AI scaffolding (`CLAUDE.md`, `AGENTS.md`, `.cursor/`, `skills.md`) | Delete from `environment/` |
| `privileged`, `SYS_ADMIN`, `docker.sock` | Standard sandbox |
| Heredoc-inlined source or opaque archives in the Dockerfile | Real files plus `COPY` |
| Unpinned `FROM ...:latest` or unpinned pip/npm | Exact versions |
| Runtime network install in `test.sh` | Bake verifier deps |

## Anti-examples (too broken to submit)

These fail before family or novelty even matter:

- "Write a function that reverses a string." -- one-liner; recall, not engineering.
- "Build a web scraper." -- vague; unverifiable.
- "Query Twitter for today's trends." -- secrets plus nondeterministic live data.
- "Make this code better." -- no success condition.

Inspiration that still has to be made specific: concurrency with stated
invariants, constrained algorithms, a measurable refactor, a security find-and-fix
with a behavioral test, performance that preserves correctness under hidden cases.

## Author checklist before zip

1. Instruction uses absolute `/app/...` paths and does not contain a recipe.
2. Dockerfile copies only the starting state; reserved Harbor dirs are untouched.
3. No AI scaffolding under `environment/`.
4. `solve.sh` derives the answer; `test.sh` does not.
5. Visible and hidden groups both exist; a visible-only patch still fails.
6. Reward file is written on success and on failure.
7. Oracle 1.0, NOP at the declared floor, real gap.
8. No runtime fetches in solve or tests.
9. Oracle and agent face identical tests.
10. `scripts/preflight.sh --slug <slug> --with-oracle` has actually been run.
