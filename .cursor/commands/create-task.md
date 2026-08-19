# create-task

Use this command when the user provides a raw Odyssey task idea and wants it turned
into a repository-compliant authoring package.

This command is **ENGINE_1 then ENGINE_3**. Read
`.cursor/rules/engines/ENGINE_1_ideas.mdc` first. If the idea cannot name
what a frontier model gets wrong on the first attempt, stop. If remaining
work is a ticket rather than a collection-scale system (>= 40 honest expert
hours), stop; do not run `new_task.py`. "Frontier models fail" does not
make a ticket long-horizon. Only then Read
`.cursor/rules/engines/ENGINE_3_create.mdc` and follow the sequence below.
Router: `.cursor/rules/09-engine-router.mdc`. Collection bar:
`docs/odyssey-long-horizon.md`.

## Inputs

The user should provide:

- the raw task idea
- any preferred collection family or constraints if already known
- any special environment, compute, model, or network assumptions

## Mandatory sequence

Work through every step, in order, every time. Do not skip a step because the idea
looks simple, and do not reorder them: each step depends on the one before it, and
the platform submits a bundle automatically once inspection passes it, so there is no
later point at which a mistake can be caught.

### 1. Normalize the idea

- restate the engineering problem in concrete delivery terms
- identify the collectionFamily, taskFamily, and verifierFamily honestly
- call out missing assumptions and risks rather than inventing answers

### 2. Choose the slug

Derive a lowercase-kebab slug of 3 to 80 characters from the core engineering
problem, not the domain dressing. Confirm it with the user if the idea is ambiguous.
This slug is final: it becomes `drafts/<slug>.md`, `plans/<slug>.md`,
`tasks/<slug>/`, and `zip/<slug>.zip`, and it must equal the draft's `workingSlug`
and `[metadata] working_slug` in `task.toml`.

### 3. Scaffold

```bash
python3 scripts/new_task.py --slug <slug> --title "<title>" \
    --collection-family "<family>" --task-family <family> --verifier-family <family>
```

This creates the draft, the plan, and the task skeleton together, so the three
directories cannot drift apart.

### 4. Write the draft

Fill `drafts/<slug>.md` completely, following the draft authoring rules. Write it as
Markdown with one `##` heading per Odyssey form field so each section body can be
pasted into the form. Use only keyboard-accessible ASCII in every draft field and
in `instruction.md`: `->` not arrows, `^2` not superscripts, `--` not em dashes,
straight quotes, `<=` / `>=` / `!=`. Every field must be specific enough that a
reviewer can understand and trust the task from the draft alone. Treat the character
minimums as a floor, not a target. In particular:

- **objective**: the concrete deliverable and what done looks like
- **motivation**: the real scenario this stands in for
- **difficultyExplanation**: remaining-work surface plus what a strong model gets *wrong* on the first attempt. Model failure is not a horizon argument.
- **expertTimeEstimateHours**: honest remaining expert work, locally >= 40
- **environmentSummary**: base image, tooling, baked-in dependencies, contents of `/app`
- **resourceEstimate**: within the sandbox — 8 CPUs, 65536 MB, 40960 MB, agent
  timeout 4-10h (template 18000s, platform floor 7200s, cap 37000s), agent plus verifier fitting the
  50400s trial pool with room for build and teardown
- **networkRequirements**: `none` unless the task itself must reach a host
- **oracleStrategy**: how `solution/solve.sh` reaches full reward
- **verificationStrategy**: what runs, what is visible, what is hidden, and why it
  measures the objective rather than a proxy
- **binarySuccessCondition**: one machine-checkable line
- **partialScoreStrategy**: monotone components and how they accumulate
- **anticipatedExploits**: each shortcut and the mechanism that defeats it

### 5. Check novelty

```bash
python3 scripts/check_novelty.py --slug <slug>
```

A high score means changing the underlying problem, not the wording. Also judge
whether the idea is a well-known exercise a model has already seen, which no local
check can detect.

### 6. Validate the draft

```bash
python3 scripts/validate_odyssey_task.py --slug <slug>
```

Report the real output. Do not claim compliance for a check that was not run.

### 7. Plan the bundle

Fill `plans/<slug>.md`: what goes in each required file, the visible/hidden split,
the oracle path, the expected nop floor, the anti-gaming measures, and the resource
and network mapping into `task.toml`. The plan should be specific enough that another
engineer could implement the bundle from it alone.

### 8. Implement the task

Build out `tasks/<slug>/` in Harbor order (instruction, `task.toml`,
environment, `solve.sh`, tests). Non-negotiables:

- `instruction.md` uses absolute `/app/...` paths and states the objective
  without recipes, detection guides, or leaked hidden cases
- the Dockerfile copies only the starting state into `/app`; `tests/` and
  `solution/` stay out of the image; Harbor reserved paths (`/tests`,
  `/solution`, `/oracle`, `/logs/verifier`) are not created
- `solution/solve.sh` derives the answer by editing `/app`; it does not echo
  goldens and it does not contain the only copy of an e2e solver that tests
  also implement
- `tests/test.sh` runs a visible group (minority of the score, aim ~30%) and
  hidden groups that dominate the reward float, writes a reward on every
  exit, and reports a monotone score
- oracle and agent face identical tests
- difficulty is designed in: interacting failures, decoys off the hot path
  when `/app` has several modules, an almost-correct trap, generated hidden
  cases. `docs/odyssey-difficulty-design.md`

`examples/reference-bundle/` is a working bundle to adapt rather than start from
scratch. Copy its plumbing, not its difficulty. File-level craft:
`docs/harbor-task-anatomy.md` and `docs/odyssey-quality-guidelines.md`.

### 9. Preflight

```bash
scripts/preflight.sh --slug <slug> --with-oracle
```

The oracle and nop pair is the important one: the reference must reach full reward
and the untouched state must sit at its floor, with a real gap between them.
`check_difficulty_design.py` must not report ERROR (recipe instruction, visible
majority weight, interview-exercise shape).

### 10. Prove probes V/D/L/A

- **V** visible-only patch: partial credit, still fails
- **D** decoy-only patch: hidden/hot-path groups still fail
- **L** one-layer patch: later hidden groups still fail
- **A** almost-correct algorithm: some visible pass, hidden fail

If V, D, or L fully pass, do not zip.

### 11. Package

```bash
python3 scripts/package_task.py --slug <slug> --with-oracle
```

Everything is verified before the archive is written, and the archive is validated
after. Only then record it with `scripts/ledger.py add --slug <slug>`.

## Required outputs to the user

Report, in this order:

- Normalized task concept
- Classification and chosen slug
- Draft summary and the paths written
- Bundle design notes, including the visible/hidden split
- Validation findings, quoting the actual command output
- Open issues

## Refusal conditions

Do not describe a task as ready while any of these hold:

- the objective is still a ticket (feature, repair, slice, stubbed module)
  rather than a complete system in the declared family
- honest expert remaining work is below 40 hours
- the objective is still ambiguous
- the reference solution path is unclear
- the verifier measures only a weak proxy
- a visible-only patch would pass
- the network requirement is unjustified
- the resources exceed the sandbox
- novelty depends on renaming rather than a different problem
- a gate was skipped, or failed and was not fixed
