# create-task

Use this command when the user provides a raw Odyssey task idea and wants it turned
into a repository-compliant authoring package.

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
- **difficultyExplanation**: what a strong model gets *wrong* on the first attempt
- **environmentSummary**: base image, tooling, baked-in dependencies, contents of `/app`
- **resourceEstimate**: within the sandbox — 8 CPUs, 65536 MB, 40960 MB, agent
  timeout at least 7200s, agent plus verifier fitting the 50400s trial pool with room
  for build and teardown
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

Build out `tasks/<slug>/`. Non-negotiables:

- the Dockerfile copies only the starting state into `/app`; `tests/` and `solution/`
  stay out of the image
- `tests/test.sh` runs a visible group and at least one held-out group, and reports a
  monotone score
- `solution/solve.sh` drives the verifier to full reward
- `instruction.md` states the objective and what success looks like without leaking
  held-out cases

`examples/reference-bundle/` is a working bundle to adapt rather than start from
scratch.

### 9. Preflight

```bash
scripts/preflight.sh --slug <slug> --with-oracle
```

The oracle and nop pair is the important one: the reference must reach full reward
and the untouched state must sit at its floor, with a real gap between them.

### 10. Prove the anti-gaming claim

Write the shallowest patch that satisfies every visible check, run the verifier
against it, and confirm it earns partial credit and still fails. If it passes, the
hidden split is decorative and the verifier needs work.

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

- the objective is still ambiguous
- the reference solution path is unclear
- the verifier measures only a weak proxy
- a visible-only patch would pass
- the network requirement is unjustified
- the resources exceed the sandbox
- novelty depends on renaming rather than a different problem
- a gate was skipped, or failed and was not fixed
