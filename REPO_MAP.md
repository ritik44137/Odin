# Repository Map

```
.
├── .cursor/
│   ├── commands/
│   │   ├── create-task.md              # ENGINE_1 then 3: idea -> draft + bundle
│   │   ├── revise-task.md              # ENGINE_7: lane router, never bounce to easy
│   │   ├── harden-task.md              # ENGINE_8: structural difficulty
│   │   ├── audit-task.md               # ENGINE_4: pre-zip review + probes
│   │   ├── verify-task.md              # ENGINE_5: oracle 1.0 / NOP floor
│   │   └── package-task.md             # ENGINE_6: package_task.py only
│   └── rules/
│       ├── 00-project-overview.mdc     # purpose, terminology, global intent
│       ├── 01-submission-lifecycle.mdc # draft -> upload -> inspection -> funnel
│       ├── 02-authoring-and-draft-rules.mdc
│       ├── 03-bundle-structure-and-validation.mdc
│       ├── 04-quality-review-and-antigaming.mdc
│       ├── 05-instruction-writing.mdc  # six principles, absolute paths, no recipes
│       ├── 06-environment-and-docker.mdc
│       ├── 07-oracle-verifier-and-quality.mdc
│       ├── 08-difficulty-design.mdc    # probe, decoys, grader weights, probes V/D/L/A
│       ├── 09-engine-router.mdc        # pick ENGINE_1-8 from the paste
│       └── engines/                    # on-demand ENGINE_1..8 (Read one per turn)
├── drafts/                             # <slug>.md — drafts, and nothing else
├── plans/                              # <slug>.md — bundle plans
├── tasks/                              # <slug>/ — bundle roots, exactly what gets zipped
├── zip/                                # <slug>.zip — finished archives, and nothing else
├── LEDGER.json                         # local: submissions and hashes (gitignored)
├── docs/
│   ├── odyssey-repo-layout.md          # the slug contract and mandatory sequence
│   ├── odyssey-authoring-loop.md       # the operating loop, end to end
│   ├── harbor-task-anatomy.md          # how Harbor runs the ZIP; reserved paths
│   ├── odyssey-quality-guidelines.md   # QG1-QG8, verifier integrity, common errors
│   ├── odyssey-difficulty-design.md    # probe, decoys, grader weights, probes V/D/L/A
│   ├── odyssey-long-horizon.md         # collection-scale remaining work (not tickets)
│   ├── odyssey-engines.md              # Terminus -> Odin engine map; difficulty first
│   ├── odyssey-bundle-checklist.md     # preflight checklist before upload
│   ├── odyssey-bundle-plan-rubric.md   # quality bar for bundle plans
│   ├── odyssey-family-specific-guidance.md
│   ├── odyssey-open-questions.md       # assumptions the source guide leaves unstated
│   └── odyssey-reviewer-notes.md       # reviewer-oriented self-check
├── examples/
│   ├── good/                           # one strong draft per collection family
│   ├── bad/                            # one counterexample per common rejection:
│   │                                   #   ambiguous objective, weak verification,
│   │                                   #   easy for the wrong reasons, novelty by renaming,
│   │                                   #   instruction recipes, solver living in tests/,
│   │                                   #   decorative hardening, decoy on the hot path
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
│   ├── check_difficulty_design.py      # heuristic easy-shape + horizon scan (not the probe)
│   ├── odyssey_horizon.py              # collection-scale remaining-work bar
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
│   ├── odyssey-dockerfile.template
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
| How does Harbor actually run the ZIP? | `docs/harbor-task-anatomy.md` |
| What file-level quality bar applies? | `docs/odyssey-quality-guidelines.md` |
| How do I design for the difficulty probe? | `docs/odyssey-difficulty-design.md` |
| What remaining work counts as long-horizon? | `docs/odyssey-long-horizon.md` |
| Which engine do I run? | `docs/odyssey-engines.md`, `.cursor/rules/09-engine-router.mdc` |
| What does a valid bundle look like? | `examples/reference-bundle/` |
| Is my draft and bundle internally consistent? | `scripts/validate_odyssey_task.py` |
| Did I leak the held-out data? | `scripts/scan_bundle_leaks.py` |
| Can my reference solution actually solve it? | `scripts/run_oracle_nop.py` |
| Is this too close to something I already submitted? | `scripts/check_novelty.py` |
| How do I produce the archive safely? | `scripts/package_task.py --slug <slug>` |
| What did I upload, and when? | `scripts/ledger.py` |
| What is guesswork rather than documented? | `docs/odyssey-open-questions.md` |
