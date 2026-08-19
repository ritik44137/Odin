# harden-task

Use when a solvable Odyssey task is too easy: agents one-shot it, a
visible-only patch would pass, or audit found decorative hardness.

This command is **ENGINE_8**. Read `.cursor/rules/engines/ENGINE_8_harden.mdc`
before editing. Policy: `docs/odyssey-difficulty-design.md`.

## Inputs

- the slug
- why it is too easy (probe scores, visible-only would pass, reviewer "trivial")
- current `tasks/<slug>/` and `drafts/<slug>.md`

## Hard-first rule

The task must already be solvable (oracle 1.0). If it is not, stop and use
ENGINE_7 lane F or ENGINE_5. Do not "harden" a broken oracle.

## Required structural change

Implement at least two family-native mechanisms from ENGINE_8:

1. interaction (one-layer patch still fails later hidden)
2. decoy off the hot path (decoy-only patch fails hidden)
3. independent hidden trap (different root cause than visible)
4. almost-correct trap
5. generated / property hidden group

Keep visible `run_group` weight a minority (~30%).

## Forbidden

More pytest on the same path. New hash fields on the same bugs. Instruction
recipes. Relabeling `difficultyExplanation` without changing `/app` or tests.
Stamping ingest -> staging -> export on every slug. Secret rules that exist
only in `tests/hidden/`.

## After edits

```bash
python3 scripts/check_difficulty_design.py --slug <slug>
python3 scripts/scan_bundle_leaks.py --slug <slug>
scripts/preflight.sh --slug <slug> --with-oracle
```

Run probes V/D/L/A. If V fully passes, the harden failed.

## Required reply

Engine 8 block from ENGINE_8_harden.mdc, including structural paths and
probe outcomes.
