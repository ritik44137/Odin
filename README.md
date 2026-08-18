# Odyssey Cursor-Native Authoring Repo

This repository turns the Odyssey authoring guide into an *operational system* for
Cursor rather than a passive document dump. Give Cursor a task idea and it should
expand that idea into a compliant draft, a credible bundle plan, and a set of local
checks that fail before you spend a submission finding out.

See `REPO_MAP.md` for the full tree and `docs/odyssey-repo-layout.md` for the layout
contract.

## One slug, four locations

A task is identified by a single slug, chosen once when the draft is created and never
changed. It names the task everywhere it appears:

```
drafts/<slug>.md       the draft, and nothing else
plans/<slug>.md        the pre-implementation bundle plan
tasks/<slug>/          the bundle root: exactly the files that get zipped
zip/<slug>.zip         the archive that gets uploaded, and nothing else
```

Every script takes `--slug` and resolves those paths itself, so no command needs a
path typed by hand and the directories cannot drift apart. The submission ledger sits
at the root as `LEDGER.json`, since it belongs to no single task.

## Why local gates matter

Odyssey submission is two-phase: you author a versioned draft, then upload a ZIP
through a quarantined channel. Once inspection marks the bundle safe it is
submitted **automatically** — there is no final confirmation step where you can
catch a mistake. Everything you want to know must therefore be known before the
upload, and each funnel stage has a local counterpart here:

| Funnel stage | Local counterpart |
|---|---|
| Structure | `scripts/validate_odyssey_task.py` |
| Similarity / dedup | `scripts/check_novelty.py`, `scripts/ledger.py` |
| Oracle & nop | `scripts/run_oracle_nop.py` |
| Quality check | `scripts/validate_odyssey_task.py`, `scripts/scan_bundle_leaks.py` |
| Difficulty probe | no local substitute — this is a judgement call |
| Synthesis | nothing to check: it confirms earlier stages and adds no judgement |
| Human review | `docs/odyssey-reviewer-notes.md` |

The difficulty probe is the one gating stage nothing here can simulate. Everything
else is reproducible locally, and failing it locally costs minutes instead of a
submission.

## Workflow

```bash
# 1. Scaffold all three locations at once from the slug you chose
python3 scripts/new_task.py --slug <slug> --title "<title>"

# 2. Write drafts/<slug>.md, then check it before investing in a bundle
python3 scripts/check_novelty.py --slug <slug>
python3 scripts/validate_odyssey_task.py --slug <slug>
# Optional: print one form field to paste
# python3 scripts/print_draft.py --slug <slug> --field objective

# 3. Fill plans/<slug>.md, then implement tasks/<slug>/
#    starting from examples/reference-bundle/

# 4. Run every local gate
scripts/preflight.sh --slug <slug> --with-oracle

# 5. Verify everything and package in one step
python3 scripts/package_task.py --slug <slug> --with-oracle
python3 scripts/ledger.py add --slug <slug>
```

Steps 4 and 5 need Docker for the oracle and nop runs; drop `--with-oracle` to skip
them, but do not upload until they have passed at least once.

`package_task.py` is the only thing that should produce an archive. It re-runs every
gate, writes `zip/<slug>.zip` only if they all pass, preserves the executable bit on
`tests/test.sh` and `solution/solve.sh`, and validates the archive afterwards —
deleting it if that fails. Both accepted layouts validate: a ZIP whose contents sit at
the root, and one nested under a single top-level directory (`--nested-root <name>`).

In Cursor, the `create-task` and `revise-task` commands drive this sequence and are
required to follow every step.

## What this repo encodes

1. **Rules** in `.cursor/rules/` that Cursor always obeys while authoring.
2. **Commands** in `.cursor/commands/` for creating and revising tasks.
3. **Schema** in `schemas/`, the single source of truth for draft bounds — the
   validator reads its limits from there rather than duplicating them.
4. **Templates** for the draft, `task.toml`, instructions, verifier, reference
   solution, and bundle plan.
5. **Examples**: strong drafts per collection family, weak-authoring
   counterexamples, and a complete working bundle in
   `examples/reference-bundle/`.
6. **Tooling** in `scripts/`, one script per funnel stage that can be reproduced
   locally, plus `preflight.sh` to run them in order and `package_task.py` to gate the
   archive behind them.
7. **Process docs** in `docs/`, including `odyssey-repo-layout.md` for the slug
   contract and mandatory sequence, and `odyssey-open-questions.md` for the places
   where this repo had to guess.

## Design choices baked in

- **Objective grading over prose quality.** A draft that reads well but grades
  weakly is the most common rejection, so the tooling checks grading structure.
- **Anti-gaming as a first-class requirement.** `scan_bundle_leaks.py` exists
  because "the held-out data is sealed" is a claim that can be checked mechanically.
- **The visible/hidden split as an obligation.** Both the verifier template and the
  reference bundle demonstrate it; the scanner warns when it is missing.
- **Consistency between draft and bundle.** Resources, network posture, families,
  and slug are compared across the two, in both directions.
- **Fail loudly, never silently.** When a check cannot run, it is reported as
  `SKIPPED` rather than omitted, so a quiet pass is never mistaken for a real one.

## Conventions this repo chose

Drafts are Markdown so each form field is a heading you can copy into the Odyssey
form; the validator parses them against `schemas/odyssey-task-draft.schema.json`.
Process docs are Markdown too. Verifiers
report partial credit by printing a single `ODYSSEY_SCORE=<float between 0 and 1>`
line, which `run_oracle_nop.py` reads; if a verifier prints no such line, exit
status alone is used. That marker is a local convention, not a documented platform
interface — see `docs/odyssey-open-questions.md` before relying on it.

## Running the tooling tests

```bash
python3 -m pytest
```

Requires Python 3.11+, or Python 3.9+ with `tomli` installed.
