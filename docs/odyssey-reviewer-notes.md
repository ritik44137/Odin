# Reviewer-Oriented Self-Check

Use this note before treating a task as ready for submission.

## Questions to ask

- Can a skeptical reviewer explain the task clearly after reading only the draft?
- Does the objective define the real deliverable rather than hinting at it vaguely?
- Would the reference solution actually reach full reward?
- Does the verifier check the true objective through multiple angles?
- Is there a meaningful visible/hidden split?
- Are exploit paths named and actually neutralized?
- Is the task realistic and non-toy?
- Is the novelty conceptual rather than cosmetic?
- Is the declared compute justified and internally consistent?
- Would a frontier agent one-shot this at the full time budget?
- Is remaining work a complete system (>= 40 honest expert hours), or a ticket?
- Have probes V/D/L/A been run, not just described?

## Common authoring defects a reviewer will catch

These are the Terminal-Bench / Harbor failures that still apply after the draft
looks complete. Full catalog: `docs/odyssey-quality-guidelines.md`.

- instruction is a recipe, a detection guide, or a dump of golden values
- paths in the instruction are relative, so the agent has to guess the tree
- `tests/` contains the solver (deleting `solution/` would still produce the artifact)
- `solve.sh` echoes answers instead of patching `/app`
- Dockerfile copies `tests/` or `solution/`, or creates `/tests` / `/oracle`
- oracle and agent are not tested identically
- verifier never writes a reward on the failure path
- environment ships `CLAUDE.md` / `AGENTS.md` / `.cursor/` scaffolding
- family label does not match the work in `/app`
- difficulty is described only as hours, file count, or "frontier models fail"
- remaining work is a ticket (feature, repair, slice) relative to the collection
- visible tests hold most of the reward, so a shallow patch looks solved
- hidden tests copy the visible root cause
- decoys sit on the hot path (patching them passes)
- more pytest was added instead of a new interacting failure mode

## Common final fixes before submission

- tighten the objective
- sharpen the binary success condition
- strengthen hidden checks
- improve exploit analysis
- remove unjustified network assumptions
- align bundle metadata with the draft
- replace relative paths and recipes in `instruction.md`
- move any e2e solver out of `tests/` and into `solution/`