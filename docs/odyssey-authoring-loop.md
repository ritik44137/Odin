# Odyssey Authoring Loop

The operating loop for this repository. Each step names the artifact it produces and
the gate that proves it. `docs/odyssey-repo-layout.md` describes the slug contract
these steps depend on.

Every step runs every time. The platform submits a bundle automatically once
inspection passes it, so there is no later point at which a mistake can be caught.

## Step 1: Normalize the idea and choose the slug

Run the `create-task` workflow (ENGINE_1 then ENGINE_3) on a raw concept.
ENGINE_1 must name the first-attempt trap **and** collection-scale remaining
work (complete system, >= 40 honest expert hours) before `new_task.py` runs.
Ticket-sized ideas fail Automated Difficulty as too short even when models
fail them. Then classify the task honestly, sharpen the objective into a
concrete deliverable, and derive a lowercase-kebab slug from the core
engineering problem. The slug is chosen once and is then fixed. Router:
`.cursor/rules/09-engine-router.mdc`. Horizon: `docs/odyssey-long-horizon.md`.

## Step 2: Scaffold

```bash
python3 scripts/new_task.py --slug <slug> --title "<title>"
```

This creates `drafts/<slug>.md`, `plans/<slug>.md`, and the `tasks/<slug>/`
skeleton together, so the three locations cannot drift apart. The scaffold is
deliberately invalid until filled in: the validator rejects placeholder content.

## Step 3: Write the draft

Fill `drafts/<slug>.md` to the standard the draft form expects. Treat the character
minimums as a floor. A reviewer should be able to understand and trust the task from
the draft alone. Every pasted field, and `instruction.md`, must use only keyboard
ASCII (`->`, `^2`, `--`, `<=`); the validator rejects arrows, superscripts, and
typographic dashes.

## Step 4: Check novelty before investing

```bash
python3 scripts/check_novelty.py --slug <slug>
```

Cheap, and it runs before you build anything. A high score against your own earlier
work means changing the problem, not the wording. It cannot see other authors' tasks,
so also ask whether the idea is a well-known exercise a model has seen a thousand
times.

## Step 5: Validate the draft

```bash
python3 scripts/validate_odyssey_task.py --slug <slug>
```

Bounds come from `schemas/odyssey-task-draft.schema.json`. Treat warnings about the
visible/hidden split and the resource envelope as design feedback rather than
formatting nits.

## Step 6: Review the first pass

Check realism, verifier strength, exploit coverage, and family fit against
`examples/bad/` and `docs/odyssey-reviewer-notes.md`. Weak verification is the most
common reason a task that "works" is still not keepable, and being easy for the wrong
reasons is the most common reason a well-built task is rejected.

## Step 7: Plan the bundle

Fill `plans/<slug>.md` before implementing: what goes in each required file, the
visible/hidden split, the oracle path, the expected nop floor, the anti-gaming
measures, and how the draft's resources and network posture map into `task.toml`.
`docs/odyssey-bundle-plan-rubric.md` is the bar.

## Step 8: Implement the bundle

Build out `tasks/<slug>/` in Harbor authoring order, documented in
`docs/harbor-task-anatomy.md`:

1. `instruction.md` -- requirements and absolute paths, no recipes
2. `task.toml` -- families, resources, and network matching the draft
3. `environment/` -- starting state plus a Dockerfile that copies only that state
4. `solution/solve.sh` -- a command sequence that derives the answer in `/app`
5. `tests/` -- visible group, then hidden groups, with a reward written on every exit

Start from `examples/reference-bundle/`, which already demonstrates the required
paths, the visible/hidden split, the scoring convention, and a Dockerfile that
keeps `tests/` and `solution/` out of the image. Apply
`docs/odyssey-quality-guidelines.md` as you write each file: the verifier must
not contain the solver, the oracle must not echo goldens, and the image must not
touch Harbor's reserved paths.

## Step 9: Revise against feedback

Run the `revise-task` workflow (ENGINE_7). Keep the slug and revise in
place. Lane order: oracle, fairness, too-easy (ENGINE_8), reviewer. Apply
the requested changes while preserving repo rules; when feedback would
weaken verification or bounce the probe to easy, keep its intent and
adjust the implementation.

## Step 10: Run every local gate

```bash
scripts/preflight.sh --slug <slug> --with-oracle
```

This runs structure and consistency validation, the anti-gaming leak scan, the
difficulty-design heuristic, the novelty check, and -- with Docker available --
the oracle and nop runs. The oracle and nop pair is the one to insist on: it is
the most expensive stage to fail upstream and the most reproducible locally.
The difficulty probe itself cannot be run here; `check_difficulty_design.py`
only catches shapes that almost always saturate.

Expect a real gap between the two runs. An oracle that reaches full reward while the
untouched state also scores well means the verifier is not measuring the work.

## Step 11: Prove probes V/D/L/A

Write the shallowest patch that satisfies every visible check, run the verifier
against it, and confirm it earns partial credit and still fails (probe V). If
decoys exist, patch only those (D). Patch one module or stage (L). Apply the
plausible wrong algorithm (A). Hidden groups must still fail. Details:
`docs/odyssey-difficulty-design.md`.

## Step 12: Verify everything, then package

```bash
python3 scripts/package_task.py --slug <slug> --with-oracle
```

Every gate runs again before anything is written. `zip/<slug>.zip` appears only if they
all pass, and it is validated after being written — path safety and the 512 MiB limit
are properties of the archive, not of the directory — and deleted if that fails.

## Step 13: Record, then upload

```bash
python3 scripts/ledger.py add --slug <slug>
```

The ledger stores the archive's SHA-256 and refuses a hash it has already seen, which
is what the platform would reject on resubmission. Upload only when the draft, bundle,
oracle path, and verifier story all agree.

## Step 14: Close the loop on the outcome

```bash
python3 scripts/ledger.py set-status --slug <slug> --status rejected --reason "..."
```

Keeping rejections in the repo is what stops the next task from repeating the same
mistake, and keeping every draft under `drafts/` is what gives the novelty check
signal.

## Operating principle

At every stage, prefer an explicit, defensible, review-ready artifact over a vague but
optimistic one. When a check cannot run, say so — a silent pass is worse than a loud
failure.
