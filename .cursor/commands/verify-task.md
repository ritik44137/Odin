# verify-task

Oracle and NOP for an existing slug.

This command is **ENGINE_5**. Read `.cursor/rules/engines/ENGINE_5_verify.mdc`.

## Run

```bash
scripts/preflight.sh --slug <slug> --with-oracle
```

Needs Docker. Exit 3 (daemon down) is infra, not a task fail. Quote
`run_oracle_nop.py` output. Do not claim 1.0 from a skipped run.

## Contract

- Oracle: full reward 1.0 via `solution/solve.sh` editing `/app`
- NOP: declared floor (often 0.0)
- Real gap between them

If oracle fails: fix derive-path, Dockerfile, or pins. Do not weaken hidden
tests. Do not switch to ENGINE_8.

If NOP is too high: the grader is not measuring the work. Fix tests or the
starting state.

After oracle/nop pass, still confirm probes V/D/L/A. Solvable and easy is
ENGINE_8, not a ready zip.

## Required reply

Engine 5 block: oracle score, NOP score, infra, probes, ready for ENGINE_6.
