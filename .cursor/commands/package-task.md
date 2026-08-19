# package-task

Write `zip/<slug>.zip` the only allowed way.

This command is **ENGINE_6**. Read `.cursor/rules/engines/ENGINE_6_package.mdc`.

## Run

```bash
python3 scripts/package_task.py --slug <slug> --with-oracle
python3 scripts/ledger.py add --slug <slug>
```

Do not `zip -r`. `package_task.py` re-runs structure, leak scan, difficulty
design, novelty, and (with `--with-oracle`) oracle/nop. It writes the
archive only if they pass, then validates the archive.

## Last look

- ENGINE_8 is not still owed
- probes V/D/L/A were actually run
- instruction still has no recipe
- difficulty-design warnings listed even when the pack gate passed (WARN
  is not `--strict` on this path)

## Required reply

Engine 6 block: pack result, zip path or not written, remaining warnings,
probes run yes/no.
