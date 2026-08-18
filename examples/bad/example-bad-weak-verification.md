# Bad Example: Weak Verification

## Why this is bad

A task can have a decent objective and still fail Odyssey review if the verifier is shallow, single-channel, or easy to game.

## Weak draft excerpt

**Verification strategy:**
Run one test case that exercises the main functionality. If the output matches the expected result, the task passes.

**Anticipated exploits:**
None expected.

## Problems

- One happy-path check is not robust verification.
- The strategy does not mention visible versus hidden checks.
- It invites hard-coded solutions.
- It assumes no exploitation pressure.
- It measures a narrow proxy, not durable task success.

## Better pattern

Use multiple independent checks, held-out cases, exploit-aware grading logic, and a clear explanation of why the verifier measures the actual objective.