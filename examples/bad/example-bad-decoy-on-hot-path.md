# Bad Example: Decoy on the Hot Path

## Why this is bad

A decoy is a file that looks like the work and is not graded. If the export
path still calls it, agents patch that file and pass. Terminus called this
G-030. Odyssey needs the same split whenever `/app` has several plausible
modules.

## Weak tree excerpt

```
/app/wrap.py      # looks broken; agents fix this first
/app/export.py    # calls wrap.py
```

`instruction.md` says "ignore unused helpers" but `export.py` imports
`wrap`. Hidden tests go green after a wrap-only patch.

## Problems

- Probe D (decoy-only) PASSES the task, so the decoy is the solution.
- The instruction lies: "ignore" is false.
- Dual obvious files that both sit on the hot path are two easy fixes, not
  two decoys.

## Better pattern

The obvious module stays broken and unused. The graded stage has its own
bugs. A wrap-only (or wrap+merge-only) patch leaves hidden export, order,
or invariant groups failing. Tests may assert the decoy file still exists
so the agent cannot delete the distraction. Document the split in
`difficultyExplanation` and in the bundle plan.
