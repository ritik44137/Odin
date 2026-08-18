# Odyssey Bundle Plan Template

Use this document to design the future task bundle before you build the ZIP. It should stay tightly aligned with the draft.

## Task identity

- **Title:**
- **Working slug:**
- **Collection family:**
- **Task family:**
- **Verifier family:**

## Goal of the bundle

Explain what the uploaded bundle will contain and how it will realize the draft's objective in executable form.

## Planned bundle tree

my-task/
  task.toml
  instruction.md
  environment/
    Dockerfile
  tests/
    test.sh
  solution/
    solve.sh

## File-by-file plan

### task.toml

Describe the intended metadata, agent settings, verifier settings, environment settings, resource values, and network posture.

### instruction.md

Describe what the agent will be told, what will be explicit, and what must remain unstated because it belongs to hidden grading logic.

### environment/Dockerfile

Describe the base image, languages, dependencies, assets, and the exact starting state prepared in `/app`.

### tests/test.sh

Describe the verifier entrypoint, visible checks, hidden checks, scoring logic, pass/fail line, and anti-gaming protections.

### solution/solve.sh

Describe how the oracle will reach full or near-full reward and why the reference solution proves the task is solvable.

## Visible versus hidden verifier split

- **Visible checks:**
- **Hidden checks:**
- **Why the hidden checks matter:**

## Oracle and NOP expectations

- **Oracle expected outcome:**
- **Untouched starting state expected outcome:**
- **Why the gap is meaningful:**

## Anti-gaming analysis

List the likely exploit attempts and how the bundle design prevents each.

## Resource and network alignment

- **Draft resource envelope:**
- **Bundle environment request:**
- **Agent network mode:**
- **Verifier network mode:**
- **Environment build network mode:**
- **Consistency notes:**

## Likely failure points before upload

List the earliest structure, quality, oracle, or review failures you still need to eliminate.