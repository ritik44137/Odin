# Odyssey Bundle Checklist

Use this before requesting an upload URL. Inspection submits a safe bundle
automatically, so there is no later chance to catch a mistake.

Most of this is mechanised:

```bash
scripts/preflight.sh --slug <slug> --with-oracle
python3 scripts/package_task.py --slug <slug> --with-oracle
```

The items below marked *(checked)* are enforced by those commands, and
`package_task.py` will not write `zip/<slug>.zip` while any of them fails. The rest are
judgement calls that no script can make for you.

## Draft and bundle consistency

- *(checked)* Draft is complete and within the schema bounds.
- *(checked)* Draft file and `instruction.md` use only keyboard-accessible ASCII
  (no arrows, superscripts, em/en dashes, or other non-keyboard glyphs).
- *(checked)* `collection_family`, `task_family`, and `verifier_family` agree between
  `task.toml` and the draft.
- *(checked)* `working_slug` matches the draft's `workingSlug`, which matches the
  directory names under `drafts/`, `plans/`, `tasks/`, and `zip/`.
- *(checked)* Draft compute fits the trial sandbox — 8 CPUs, 65536 MB, 40960 MB — since
  a request above it is rejected at intake rather than run starved.
- *(checked)* `[environment]` cpus, memory, storage, and gpus fit inside the draft's
  `resourceEstimate`, and inside the sandbox ceilings of 8 CPUs / 65536 MB / 40960 MB.
- *(checked)* Agent and verifier timeouts fit the 50,400s per-trial pool with room
  left for image build and teardown, and the agent budget is at least 7,200s.
- *(checked)* `[agent] network_mode` matches the draft's network posture, is never
  `open`, and is explicit whenever `open_internet_justification` is present.
- *(checked)* Hosts declared in the bundle are a subset of the draft's allowlist.
- The objective, oracle strategy, verification strategy, and anticipated exploits
  still describe the same task after your last round of edits.

## Required bundle files

- *(checked)* `task.toml`, `instruction.md`, `environment/Dockerfile`,
  `tests/test.sh`, `solution/solve.sh` all present by exact name.
- *(checked)* TOML parses, and `[metadata].name` is non-empty.
- *(checked)* `tests/` and `solution/` are non-empty.
- *(checked)* Paths are safe and unique, and the ZIP is under 512 MiB.
- *(checked)* No file is still template placeholder text.
- *(checked)* The archive was produced by `package_task.py`, so `tests/test.sh` and
  `solution/solve.sh` keep their executable bit and no `__pycache__` was shipped.
- `tasks/<slug>/` contains no notes or planning files, which would be shipped to the
  grader. The bundle plan belongs in `plans/<slug>.md`.

## Oracle and nop

- *(checked)* The image builds.
- *(checked)* `solution/solve.sh` drives the verifier to full reward.
- *(checked)* The untouched starting state sits at its floor.
- *(checked)* There is a real gap between the two.
- The floor you asserted with `--nop-max` is the true baseline. For an optimization
  task the untouched state scores above zero, and the default of 0 is wrong.

## Anti-gaming

- *(checked)* The Dockerfile does not copy `tests/` or `solution/` into the image.
- *(checked)* No held-out file is byte-identical to something in the image.
- *(checked)* The verifier does not grade against a fixture inside `/app`.
- *(checked)* `instruction.md` does not quote held-out expectations verbatim.
- *(checked)* `solution/solve.sh` does not read or edit the verifier.
- *(checked)* `tests/` contains held-out material, not just `test.sh`.
- Every exploit named in `anticipatedExploits` is defeated by something concrete in
  the verifier, not by the agent's good manners.
- A solution that satisfies only the visible checks earns partial credit and still
  fails. Verify this by writing the shallow patch yourself and running the verifier.

## Verification quality

- Grading covers more than one channel: behaviour, invariants, edge cases, and where
  the family calls for it, a performance or quality metric.
- Hidden cases vary inputs rather than restating the visible ones, so memorising the
  visible set does not generalise.
- Partial credit is monotone: real progress always raises the score.
- The binary success condition is a single machine-checkable line.

## Novelty and realism

- *(checked)* Not a near-duplicate of a draft already in `drafts/`.
- *(checked)* Not a byte-identical resubmission, per the ledger.
- The task resembles work an engineer would actually be assigned.
- The novelty is conceptual, not a rename of a known exercise.
- Difficulty comes from engineering reasoning, not from missing information or a
  broken environment.

## Last look

- You would defend every field to a skeptical reviewer.
- A failure upstream would reflect the task's difficulty, not your configuration.
- The draft's `notes` field, if you used one, is not pasted into the form.
