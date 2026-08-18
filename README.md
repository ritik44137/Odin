# Odin

Cursor-native authoring system for Odyssey software-engineering tasks. Given a
task idea, this repo is meant to produce a compliant draft, a bundle plan, and
local checks that fail here instead of after upload.

See `REPO_MAP.md` for the tree and `docs/odyssey-repo-layout.md` for the layout
contract.

## Current status

This is the Alpha authoring repo: the rules, commands, schema, templates,
examples, and local funnel scripts are in place and are the source of truth for
how tasks are written.

| Item | State |
|---|---|
| Authoring system (rules, scripts, templates, examples) | Ready to use |
| In-progress task | `three-way-merge-engine` |
| Ledger status | `drafting` |
| Collection / task / verifier family | Library clone / `feature_development` / `programmatic` |
| Packaged ZIP | None in `zip/` yet |

The current task is a Go library clone: implement `textmerge` (`Diff`, `Patch`,
`Merge`) against a frozen spec. A draft, bundle plan, and `tasks/three-way-merge-engine/`
tree exist on disk. Those paths are gitignored on purpose (`drafts/`, `plans/`,
`tasks/`, `zip/`) so solutions and held-out tests stay local. `LEDGER.json` is
tracked and records the slug, status, and last bundle hash.

What is in git is the authoring machinery plus the ledger. Clone this repo to
get the system; keep working copies of drafts, plans, and bundles on the
machine that authors them.

Verifier convention now matches Harbor: `tests/test.sh` must write
`/logs/verifier/reward.txt` (or `reward.json`) on every exit path, and also
print `ODYSSEY_SCORE=<float>` for the local oracle/nop harness.

## How to start

In Cursor, use the repo commands. They encode the mandatory sequence; do not
skip steps. Odyssey auto-submits a bundle once inspection marks it safe, so
mistakes have to be caught locally.

### Create a task

1. Provide a raw idea (and any family, environment, or network constraints).
2. Run the **create-task** command. Cursor will classify the idea, pick a
   lowercase-kebab slug from the engineering problem, and scaffold:

   ```bash
   python3 scripts/new_task.py --slug <slug> --title "<title>"
   ```

   That creates `drafts/<slug>.md`, `plans/<slug>.md`, and `tasks/<slug>/`
   together. The slug is final.
3. Fill the draft until a reviewer could trust the task from that file alone.
4. Check novelty, then validate:

   ```bash
   python3 scripts/check_novelty.py --slug <slug>
   python3 scripts/validate_odyssey_task.py --slug <slug>
   ```

5. Fill the bundle plan, then implement `tasks/<slug>/` from
   `examples/reference-bundle/`.
6. Preflight, prove a visible-only patch still fails, package, and record:

   ```bash
   scripts/preflight.sh --slug <slug> --with-oracle
   python3 scripts/package_task.py --slug <slug> --with-oracle
   python3 scripts/ledger.py add --slug <slug>
   ```

Steps that need Docker: oracle and nop. Drop `--with-oracle` only while
iterating; do not upload until those runs have passed at least once.

### Revise a task

Keep the same slug. Never fork to a new one to escape a failing gate.

1. Provide the existing draft/plan/bundle and the feedback.
2. Run the **revise-task** command. Cursor treats feedback as a change set,
   not as permission to drop verification or consistency rules.
3. Edits land in place:

   - wording, scoring, resources, network -> `drafts/<slug>.md`
   - verifier, oracle, anti-gaming -> `plans/<slug>.md` **and** `tasks/<slug>/`
   - resources or network -> draft **and** `tasks/<slug>/task.toml`

4. Re-run the gates. A revision is not done until they pass:

   ```bash
   python3 scripts/validate_odyssey_task.py --slug <slug>
   scripts/preflight.sh --slug <slug> --with-oracle
   python3 scripts/package_task.py --slug <slug> --with-oracle
   ```

A byte-identical ZIP is blocked by content hash, so the revision must be
substantive. `scripts/ledger.py add` refuses a hash it has already seen.

Full loop, including the anti-gaming shallow-patch check: `docs/odyssey-authoring-loop.md`.

## One slug, four locations

```
drafts/<slug>.md       the draft, and nothing else
plans/<slug>.md        the pre-implementation bundle plan
tasks/<slug>/          the bundle root: exactly the files that get zipped
zip/<slug>.zip         the archive that gets uploaded, and nothing else
```

Every script takes `--slug` and resolves those paths. `LEDGER.json` sits at the
repo root because it belongs to no single task.

## Why local gates matter

Submission is two-phase: author a versioned draft, then upload a ZIP through a
quarantined channel. Once inspection marks the bundle safe it is submitted
automatically. Each funnel stage has a local counterpart:

| Funnel stage | Local counterpart |
|---|---|
| Structure | `scripts/validate_odyssey_task.py` |
| Similarity / dedup | `scripts/check_novelty.py`, `scripts/ledger.py` |
| Oracle & nop | `scripts/run_oracle_nop.py` |
| Quality check | `scripts/validate_odyssey_task.py`, `scripts/scan_bundle_leaks.py` |
| Difficulty probe | no local substitute -- this is a judgement call |
| Synthesis | nothing to check: it confirms earlier stages |
| Human review | `docs/odyssey-reviewer-notes.md` |

`package_task.py` is the only thing that should produce an archive. It re-runs
every gate, writes `zip/<slug>.zip` only if they all pass, preserves the
executable bit on `tests/test.sh` and `solution/solve.sh`, and validates the
archive afterwards.

## What this repo encodes

1. **Rules** in `.cursor/rules/` that Cursor always obeys while authoring.
2. **Commands** in `.cursor/commands/` for creating and revising tasks.
3. **Schema** in `schemas/`, the single source of truth for draft bounds.
4. **Templates** for the draft, `task.toml`, instructions, verifier, reference
   solution, and bundle plan.
5. **Examples**: strong drafts per collection family, weak-authoring
   counterexamples, and a complete working bundle in
   `examples/reference-bundle/`.
6. **Tooling** in `scripts/`, one script per funnel stage, plus `preflight.sh`
   and `package_task.py`.
7. **Process docs** in `docs/`, including `odyssey-repo-layout.md` and
   `odyssey-open-questions.md`.

## Conventions

Drafts are Markdown with one `##` heading per Odyssey form field. The validator
parses them against `schemas/odyssey-task-draft.schema.json`. Draft text and
`instruction.md` must be keyboard ASCII only (`->`, `^2`, `--`, `<=`).

Verifiers must write `/logs/verifier/reward.txt` (or `reward.json`); Harbor
fails the trial if neither exists. They also print
`ODYSSEY_SCORE=<float between 0 and 1>` so `run_oracle_nop.py` can read the
same score from stdout.

## Running the tooling tests

```bash
python3 -m pytest
```

Requires Python 3.11+, or Python 3.9+ with `tomli` installed.
