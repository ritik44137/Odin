# Reference bundle

A complete, working bundle whose purpose is to demonstrate the *plumbing* every
Odyssey task needs. It passes every local gate in this repo, so it is the thing to
copy when starting a real task and the thing to diff against when a gate fails.

**This is not a submittable task.** It is deliberately far too easy — an hour of
work at most, and a frontier model would one-shot it. It would be rejected by the
difficulty probe, and correctly so. What it demonstrates is structure, not
difficulty.

## What it shows

- the exact required paths, and a Dockerfile that copies *only* the starting state
  into `/app`, leaving `tests/` and `solution/` outside the image
- a real visible/hidden split: `tests/visible/` states what done means, while
  `tests/hidden/` holds enumerated edge cases and property checks
- monotone partial scoring: three weighted groups (30/40/30) reduced to a single
  `ODYSSEY_SCORE` line, with a binary gate that still requires all three
- a verifier that grades from `/tmp` through the public import surface, so a
  solution cannot pass by shadowing the module or editing the grader
- a reference solution that drives the score to 1.0 and self-checks before exiting

## Measured behaviour

Measured by `scripts/run_oracle_nop.py` in the built image, not estimated:

| state | score | exit |
|---|---|---|
| untouched starting state | 0.0000 | 1 |
| patched to satisfy only `tests/visible` | 0.3000 | 1 |
| reference solution applied | 1.0000 | 0 |

That middle row is the point of the hidden split: the shallow fix looks correct
against everything the agent can see, and still earns only partial credit.

The rollout is genuinely sealed. `[agent] network_mode` is `no-network`, so the harness runs
the container with `--network none`, and the verifier still passes because every
dependency is baked into the image at build time.

## Reproducing

```bash
python3 scripts/validate_odyssey_task.py \
  --draft examples/reference-bundle/draft.md --bundle examples/reference-bundle
python3 scripts/scan_bundle_leaks.py examples/reference-bundle
python3 scripts/run_oracle_nop.py examples/reference-bundle   # needs Docker
```

To reproduce the middle row, copy the bundle, replace
`environment/app/rangespec/parser.py` with the shallowest implementation that passes
`tests/visible`, and run `run_oracle_nop.py <copy> --nop-only --nop-max 0.30`.

`draft.md` is the matching draft. Its Notes section flags it as an exemplar;
do not paste that section into the real form.
