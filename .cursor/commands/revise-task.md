# revise-task

Use this command when the user provides feedback on an existing Odyssey draft, bundle plan, verifier design, or validation result and wants Cursor to revise the work without drifting away from repository rules.

This command is **ENGINE_7**. Read `.cursor/rules/engines/ENGINE_7_revise.mdc`
and pick a lane from the paste. Do not invent "too easy". Order: oracle (O)
beats fairness (F) beats too-easy (H -> ENGINE_8) beats reviewer (R) beats
family relabel (C). Too-easy is not this file's pytest dump: Read ENGINE_8.

## Inputs

The user should provide:

- the current draft, plan, or relevant file contents
- the feedback to incorporate
- any constraints on what must remain unchanged

## Core revision rule

Treat user feedback as a **requested change set**, not as permission to ignore repository rules. Cursor must incorporate the feedback as far as possible while still preserving Odyssey compliance, internal consistency, and repo standards.

## Required outputs

Produce all of the following:

1. **Feedback interpretation**
   - restate the requested changes in concrete engineering and authoring terms
   - identify which parts of the current artifact are affected
   - identify any requested changes that would create rule conflicts or likely Odyssey rejection risks

2. **Revision plan**
   - separate direct edits from ripple effects
   - note which draft fields, verifier assumptions, resource declarations, or bundle expectations must also change

3. **Updated artifact**
   - revise the draft, plan, checklist, or supporting files directly
   - preserve unaffected good content rather than rewriting everything gratuitously

4. **Compliance review**
   - verify the revision still satisfies repo rules
   - call out any remaining tensions, unresolved ambiguities, or likely review objections

## Required behavior

- Follow the provided feedback faithfully where it does not conflict with repo rules.
- If feedback conflicts with repo rules or Odyssey constraints, do not silently comply.
- Instead, preserve the intent of the feedback while adjusting the implementation to remain compliant.
- If a direct request would weaken verification, realism, anti-gaming, or internal consistency, explain the issue and provide the closest safe revision.
- Do not ease a solvable task into a one-liner or drop hidden checks just to silence a reviewer nit. Fairness fixes (docs matching tests, broken oracle) are required; hint-injection and test-softening are not.
- Keep draft fields and `instruction.md` keyboard-ASCII only. If feedback uses arrows, superscripts, or typographic dashes, rewrite those strings as `->`, `^2`, `--`, and similar keyboard equivalents.

## Revision procedure

1. Read the current artifact carefully.
2. Extract the exact requested changes.
3. Identify downstream consequences.
4. Apply the smallest coherent set of edits that fully addresses the feedback.
5. Re-check classification, objective, verification, exploits, resources, and network posture.
6. Return the revised artifact plus a concise summary of what changed and why.

## Keep the slug, revise in place

A revision keeps the existing slug, so it stays `drafts/<slug>.md`,
`plans/<slug>.md`, `tasks/<slug>/`, and `zip/<slug>.zip`. Never fork a task to a new
slug to avoid a failing gate.

Where a change lands:

- draft wording, scoring, resources, or network posture -> `drafts/<slug>.md`
- verifier design, oracle path, or anti-gaming measures -> `plans/<slug>.md` **and**
  `tasks/<slug>/`, since a plan that no longer matches the bundle is worse than none
- anything touching resources or network -> both the draft and `tasks/<slug>/task.toml`,
  because the two are compared in both directions

## Re-verify after every revision

Run the gates again; a revision is not complete until they pass:

```bash
python3 scripts/validate_odyssey_task.py --slug <slug>
scripts/preflight.sh --slug <slug> --with-oracle
python3 scripts/package_task.py --slug <slug> --with-oracle
```

A byte-identical bundle is blocked by content hash, so a revision must be
substantive. `scripts/ledger.py add --slug <slug>` refuses a hash it has already
recorded, which is the local signal that nothing actually changed. Re-run the oracle
and nop pair after any change to the verifier or the reference solution, and re-run
the shallow-patch check after any change to the visible/hidden split. Re-run
probes D/L/A if decoys, stages, or almost-correct traps changed. Do not ease
hidden tests or add instruction recipes to raise pass rate.

## Preferred response shape

When Cursor runs this command, it should answer in sections named:

- Engine 7 lane (O|F|H|R|C) and bounce risk
- Feedback interpretation
- Conflicts with repo rules, if any
- Revision plan
- Updated artifact
- Post-revision validation notes
- Outcome contract: oracle 1.0, NOP floor, probes V/D/L/A still fail hidden