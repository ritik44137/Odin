# Repository Map

```
.
├── .cursor/
│   ├── commands/
│   │   ├── create-task.md              # idea -> draft + bundle plan + validation pass
│   │   └── revise-task.md              # feedback -> compliant revision
│   └── rules/
│       ├── 00-project-overview.mdc     # purpose, terminology, global intent
│       ├── 01-submission-lifecycle.mdc # draft -> upload -> inspection -> funnel
│       ├── 02-authoring-and-draft-rules.mdc
│       ├── 03-bundle-structure-and-validation.mdc
│       └── 04-quality-review-and-antigaming.mdc
├── drafts/                             # <slug>.md — drafts, and nothing else
├── plans/                              # <slug>.md — bundle plans
├── tasks/                              # <slug>/ — bundle roots, exactly what gets zipped
├── zip/                                # <slug>.zip — finished archives, and nothing else
├── LEDGER.json                         # submissions and bundle hashes (created on first use)
├── docs/
│   ├── odyssey-repo-layout.md          # the slug contract and mandatory sequence
│   ├── odyssey-authoring-loop.md       # the operating loop, end to end
│   ├── odyssey-bundle-checklist.md     # preflight checklist before upload
│   ├── odyssey-bundle-plan-rubric.md   # quality bar for bundle plans
│   ├── odyssey-family-specific-guidance.md
│   ├── odyssey-open-questions.md       # assumptions the source guide leaves unstated
│   └── odyssey-reviewer-notes.md       # reviewer-oriented self-check
├── examples/
│   ├── good/                           # one strong draft per collection family
│   ├── bad/                            # one counterexample per common rejection:
│   │                                   #   ambiguous objective, weak verification,
│   │                                   #   easy for the wrong reasons, novelty by renaming
│   └── reference-bundle/               # a complete working bundle (not submittable)
├── schemas/
│   └── odyssey-task-draft.schema.json  # the single source of truth for draft bounds
├── scripts/
│   ├── odyssey_paths.py                # the layout: slug -> draft, plan, task, zip
│   ├── new_task.py                     # scaffold all locations from one slug
│   ├── odyssey_draft.py                # Markdown draft codec (form-shaped headings)
│   ├── print_draft.py                  # print one form field for pasting
│   ├── validate_odyssey_task.py        # draft + bundle structure and consistency
│   ├── scan_bundle_leaks.py            # anti-gaming: what leaked into /app
│   ├── check_novelty.py                # local stand-in for the similarity stage
│   ├── run_oracle_nop.py               # oracle & nop stage, locally, via Docker
│   ├── ledger.py                       # submitted tasks and bundle content hashes
│   ├── preflight.sh                    # runs every local gate in order
│   ├── package_task.py                 # verify everything, then write zip/<slug>.zip
│   └── tests/                          # tests for the tooling above
├── templates/
│   ├── odyssey-task-draft.template.md
│   ├── odyssey-task-toml.template.toml
│   ├── odyssey-instruction.template.md
│   ├── odyssey-test.template.sh
│   ├── odyssey-solve.template.sh
│   └── odyssey-bundle-plan.template.md
├── .gitignore                          # built ZIPs stay out of git; the ledger keeps their hashes
├── pytest.ini                          # scopes collection to scripts/tests
└── README.md
```

## Which artifact answers which question

| Question | Artifact |
|---|---|
| Where does each artifact live, and in what order? | `docs/odyssey-repo-layout.md` |
| How do I start a task? | `scripts/new_task.py --slug <slug>` |
| What are the draft field bounds? | `schemas/odyssey-task-draft.schema.json` |
| What should a strong draft read like? | `examples/good/` |
| What does a valid bundle look like? | `examples/reference-bundle/` |
| Is my draft and bundle internally consistent? | `scripts/validate_odyssey_task.py` |
| Did I leak the held-out data? | `scripts/scan_bundle_leaks.py` |
| Can my reference solution actually solve it? | `scripts/run_oracle_nop.py` |
| Is this too close to something I already submitted? | `scripts/check_novelty.py` |
| How do I produce the archive safely? | `scripts/package_task.py --slug <slug>` |
| What did I upload, and when? | `scripts/ledger.py` |
| What is guesswork rather than documented? | `docs/odyssey-open-questions.md` |
