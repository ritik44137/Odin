# Odin Engines

Terminus used numbered engines so the agent did not invent a workflow.
Odin does the same, adapted to Odyssey. Difficulty is the default concern
in every engine.

Always-on picker: `.cursor/rules/09-engine-router.mdc`.
On-demand policy: `.cursor/rules/engines/ENGINE_N_*.mdc` (Read one per turn).
Commands in `.cursor/commands/` invoke the matching engine.

## Mapping from Terminus

| Terminus | Odin | What changed |
|---|---|---|
| ENGINE_1 ideas | ENGINE_1 ideas | Same job: qualify the idea. Odyssey adds a mandatory first-attempt trap **and** collection-scale remaining work. No 9 taxonomy radios. |
| ENGINE_2 anti-spam | ENGINE_2 novelty | `check_novelty.py`. Conceptual novelty, not rename. |
| ENGINE_3 create | ENGINE_3 create | Harbor order + difficulty mechanisms. No `difficulty = "hard"` key, no Case 6 stamp. |
| ENGINE_4 audit | ENGINE_4 audit | Leaks + `check_difficulty_design.py` + probes V/D/L/A. |
| ENGINE_5 verify | ENGINE_5 verify | Oracle 1.0, NOP floor. Do not ease tests. |
| ENGINE_6 zip | ENGINE_6 package | `package_task.py --with-oracle` only. |
| ENGINE_7 revise | ENGINE_7 revise | Lanes O/F/H/R/C. Too-easy is H -> ENGINE_8, not Case 6. |
| Case 6 / trivial harden | ENGINE_8 harden | Structural mechanisms only. Forbidden: ingest-staging-export clone. |

Do not copy Terminus live stubs (they point at 10k-line dumps). Odin engines
are the operational text.

## What difficulty already is in this repo

These existed before the engines and still bind:

| Layer | Path |
|---|---|
| Design | `docs/odyssey-difficulty-design.md`, `docs/odyssey-long-horizon.md` |
| Always-on rule | `.cursor/rules/08-difficulty-design.mdc` |
| Heuristic gate | `scripts/check_difficulty_design.py` |
| Gate tests | `scripts/tests/test_difficulty_design.py` |
| Preflight / pack | `scripts/preflight.sh`, `scripts/package_task.py` |
| Bad examples | `examples/bad/example-bad-too-easy.md`, `example-bad-decorative-hardening.md`, `example-bad-decoy-on-hot-path.md`, `example-bad-instruction-hints.md` |
| Draft field | `difficultyExplanation` in schema and authoring rules |
| Plan template | Difficulty design section in `templates/odyssey-bundle-plan.template.md` |
| Checklist | `docs/odyssey-bundle-checklist.md` Difficulty section |
| Family shape | `docs/odyssey-family-specific-guidance.md` |

The engines do not replace those. They route work so difficulty is applied
at the right stage instead of as a last-minute pytest dump.

## Snorkel / Terminus numbers that are not Odyssey law

Recorded in `docs/odyssey-open-questions.md`: published Terminus bands
(Hard <= 20% on best or worst, reject if worst > 80%) are not Odyssey
authoring-guide figures. Design as if a frontier agent must not one-shot
and must not be blocked by unfairness. Local heuristics cannot certify
the probe.
