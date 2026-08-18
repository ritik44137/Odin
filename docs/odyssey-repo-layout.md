# Repository Layout and the Slug Contract

## One slug, four locations

A task is identified by a single slug, chosen once when the draft is created and
never changed afterwards. It is the same string as the draft's `workingSlug` and the
`[metadata] working_slug` in `task.toml`, and it names the task everywhere:

```
drafts/<slug>.md       the draft, and nothing else
plans/<slug>.md        the pre-implementation bundle plan
tasks/<slug>/          the bundle root: exactly the files that get zipped
zip/<slug>.zip         the archive that gets uploaded, and nothing else
```

Each directory holds exactly one kind of artifact. `drafts/` never contains bundle
files, `tasks/` never contains drafts or archives, and `zip/` contains only finished
archives. Bookkeeping that belongs to no single task -- the submission ledger -- sits
at the repository root as `LEDGER.json`. It is created on first use and is
gitignored with the rest of the local task work.

Every script accepts `--slug`, resolves these paths itself, and refuses a slug that
is not lowercase kebab-case of 3 to 80 characters. Nothing needs a path typed by
hand, which is what keeps the four locations from drifting apart.

## `tasks/<slug>/` is the bundle root

What is in that directory is what ends up in the archive:

```
tasks/<slug>/
├── task.toml
├── instruction.md
├── environment/
│   ├── Dockerfile
│   └── app/            the starting state copied into /app
├── tests/
│   ├── test.sh         the verifier entrypoint the grader runs
│   ├── visible/        public checks the agent can read
│   └── hidden/         held-out cases and grading logic
└── solution/
    └── solve.sh        the reference entrypoint the oracle runs
```

Do not put notes, scratch files, or planning documents here — they would be shipped
inside a graded bundle. That is why the bundle plan lives in `plans/` instead.
`package_task.py` drops `__pycache__`, `.gitkeep`, and editor droppings when it
builds the archive, but it will not guess about anything else.

## The order of operations

The steps are ordered because each one depends on the last, and because the platform
submits a bundle automatically once inspection passes it. There is no later point at
which a mistake can be caught.

1. **Idea.** State the engineering problem, and classify it into a collection
   family, task family, and verifier family.
2. **Slug.** Choose a lowercase-kebab slug that describes the core engineering
   problem, not the domain dressing. This is the last chance to pick it.
3. **Scaffold.** `python3 scripts/new_task.py --slug <slug>` creates the draft, the
   plan, and the task skeleton in all three directories at once.
4. **Draft.** Write `drafts/<slug>.md` to the standard the draft form expects:
   one `##` heading per form field, so each section body can be pasted into the
   platform. Use only keyboard-accessible ASCII in those bodies and in
   `instruction.md`. Every field should be specific enough that a reviewer can
   understand and trust the task from the draft alone.
5. **Novelty.** `python3 scripts/check_novelty.py --slug <slug>`, before any
   implementation effort is spent.
6. **Validate the draft.** `python3 scripts/validate_odyssey_task.py --slug <slug>`.
7. **Plan the bundle.** Fill `plans/<slug>.md` so the future archive is designed
   before it is built, including the visible/hidden split and the oracle path.
8. **Implement.** Build out `tasks/<slug>/`, keeping held-out material out of the
   image.
9. **Preflight.** `scripts/preflight.sh --slug <slug> --with-oracle`. The oracle and
   nop pair must have passed at least once before upload.
10. **Package.** `python3 scripts/package_task.py --slug <slug> --with-oracle`. This
    re-runs every gate, writes `zip/<slug>.zip` only if they all pass, then
    validates the archive itself and deletes it if that fails.
11. **Record.** `python3 scripts/ledger.py add --slug <slug>` stores the archive's
    SHA-256, so a later byte-identical resubmission is caught locally rather than by
    the platform's content hash.
12. **Close the loop.** When the verdict arrives,
    `python3 scripts/ledger.py set-status --slug <slug> --status <status> --reason "..."`.

Steps 5, 6, 9, and 10 are gates, not formalities: a failure there is a defect that
would otherwise surface upstream as a rejection.

## Why the draft comes first

Submission is two-phase. The draft is authored and versioned first, and the bundle is
uploaded afterwards through a quarantined channel. Writing the draft first is not
bureaucracy: the objective, verification strategy, and success condition are what the
bundle then has to implement. A bundle built before its draft tends to produce a
draft that describes whatever was built, which is how tasks end up with a verifier
that measures a proxy rather than the objective.

## Revisions

A byte-identical bundle is blocked by content hash, and a near-duplicate is caught by
the similarity stage, so a revision has to be substantive. Keep the slug, revise the
draft and the task in place, re-run the gates, and re-package. `ledger.py` will refuse
an archive whose hash it has already recorded, which is the local signal that nothing
actually changed.
