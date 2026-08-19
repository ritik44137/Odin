# audit-task

Read-only review of an existing slug before verify or package.

This command is **ENGINE_4**. Read `.cursor/rules/engines/ENGINE_4_audit.mdc`.
Do not write `zip/<slug>.zip`.

## Inputs

- the slug
- optionally a platform or reviewer summary (quote facts; do not invent lanes)

## Must run and quote

```bash
python3 scripts/validate_odyssey_task.py --slug <slug>
python3 scripts/scan_bundle_leaks.py --slug <slug>
python3 scripts/check_difficulty_design.py --slug <slug>
python3 scripts/check_novelty.py --slug <slug>
```

SKIPPED is unknown, not passing.

## Fill the ENGINE_4 table

Instruction recipe, visible weight, independent hidden trap, generated
channel, decoy plan, probes V/D/L/A, decorative hardening,
`difficultyExplanation`.

Any FAIL or "not run" on probe V -> not ready. Decorative present -> next
engine is 8, not more pytest.

## Required reply

Engine 4 block: table, blockers, next engine (5, 8, or 7-F).
