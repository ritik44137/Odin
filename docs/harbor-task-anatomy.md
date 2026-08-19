# Harbor Task Anatomy

Odyssey bundles use the Terminal-Bench / Harbor 2.0 layout. This page is the
runtime model for that layout: what each file is for, how Harbor runs it, and
the authoring order inside `tasks/<slug>/`. It is adapted from Harbor and from
the Terminus Terminal-Bench authoring corpus in `terminal-bench-reference/`.
Snorkel-only policy (nine taxonomy radios, milestone tasks, rubrics, required
tmux/asciinema, Case 6 hardening) is not Odyssey policy and is not copied here.

The Odyssey draft, slug contract, and funnel remain in
`docs/odyssey-repo-layout.md` and `source-of-truth.txt`. This document answers
a different question: what actually happens when the ZIP is executed.

## What the agent, oracle, and verifier each see

Harbor runs three roles against one image built from `environment/Dockerfile`.

```
                    built image
                         |
                         v
                    /app  (WORKDIR)
                         |
         +---------------+---------------+
         |               |               |
      agent           oracle          nop
   (reads prompt,   (runs solve.sh,  (does nothing,
    edits /app)      then test.sh)    then test.sh)
         |               |               |
         +---------------+---------------+
                         |
                         v
                    verifier
              (runs tests/test.sh)
                         |
                         v
              /logs/verifier/reward.txt
```

- **Agent rollout.** The model receives `instruction.md` as the problem
  statement and works in `/app`. `tests/` and `solution/` are not in the image.
  Network follows `[agent] network_mode`.
- **Oracle.** Harbor runs `solution/solve.sh`, then the same `tests/test.sh`
  the agent will be graded with. Same image, same network, same tests. If the
  oracle cannot reach full reward, the task is broken.
- **NOP.** Harbor runs `tests/test.sh` against the untouched starting state.
  This must sit at the floor declared in `partialScoreStrategy`. If NOP already
  scores well, the verifier is not measuring the work.
- **Verifier.** Harbor mounts the bundle's `tests/` (typically at `/tests`) and
  executes `tests/test.sh`. Exit status is not the score. The script must write
  `/logs/verifier/reward.txt` (a float in `[0,1]`) or `/logs/verifier/reward.json`
  on every exit path, including failures.

The local counterpart is `scripts/run_oracle_nop.py`. It mounts the verifier
outside `/app` (at `/odyssey/tests`) so a passing local run also proves grading
does not depend on agent-readable files. Write `test.sh` so it locates itself
via `$0` rather than assuming one mount path.

## Reserved paths

Harbor mounts these. The Dockerfile must not `mkdir`, `COPY`, `ADD`, or `chown`
them, and `/app` must not pretend to own them:

- `/tests` -- verifier tree, mounted at grade time
- `/solution` -- reference tree, used by the oracle run
- `/oracle` -- oracle working mount
- `/logs/verifier` -- reward file destination
- `/logs/agent` -- agent logs

If the image already contains `/tests` or `/solution`, the mount collides and
the trial fails for infrastructure reasons rather than task difficulty.

## Bundle files and who they are for

```
tasks/<slug>/
├── task.toml                 Harbor config: identity, timeouts, resources, network
├── instruction.md            the only problem statement the agent is guaranteed
├── environment/
│   ├── Dockerfile            builds the image; COPY only the starting state
│   └── app/                  becomes /app; this is what the agent can read
├── tests/
│   ├── test.sh               the only verifier entrypoint Harbor will run
│   ├── visible/              public checks that state what "done" means
│   └── hidden/               held-out cases and grading logic
└── solution/
    └── solve.sh              the only oracle entrypoint Harbor will run
```

`instruction.md` is a prompt, not a file the agent is promised under `/app`.
Put contracts the agent must read in `/app` (for example `/app/README.md` or
`/app/docs/`) and refer to them by absolute path.

Do not put planning notes in this tree. They would ship to the grader.

## Authoring order inside the bundle

Draft and plan come first (`docs/odyssey-authoring-loop.md`). When implementing
`tasks/<slug>/`, write files in this order so each step has something to check:

1. **`instruction.md`** -- the objective, constraints, and absolute output paths.
   Requirements, not recipes. No golden values, no detection guides.
2. **`task.toml`** -- families, timeouts, resources, and network posture that
   match the draft. Unknown keys are rejected by Harbor's parser.
3. **`environment/`** -- starting state in `app/`, Dockerfile that bakes
   dependencies and copies only that state into `/app`.
4. **`solution/solve.sh`** -- a real command sequence that derives the answer
   by editing `/app`. Prove the steps inside a container before wrapping them.
5. **`tests/`** -- visible group first (mirrors the instruction), then hidden
   groups the visible set cannot satisfy. `test.sh` always writes a reward.
6. **Oracle and NOP** -- `scripts/run_oracle_nop.py`. Oracle at 1.0, NOP at the
   declared floor, with a real gap.
7. **Shallow-patch proof** -- the smallest change that passes every visible
   check must still fail overall.

Skipping to tests before a working oracle is how tasks become unsolvable. Skipping
the instruction until after the tests is how tasks leak answers into the prompt.

## `task.toml` in Harbor terms

Required sections: `[metadata]`, `[agent]`, `[verifier]`, `[environment]`.

Network values are Harbor's `NetworkMode`: `no-network`, `allowlist`, `public`.
The draft form still says `none` / `allowlist`. Map `none` to `no-network`.
`public` is open egress and is refused for `[agent]`. Keep all three phases on
the same mode unless you also set `dynamic_network_policy`.

`[environment].network_mode` is the **runtime baseline** when the container
starts, not docker-build networking. Image builds may fetch packages either way.
`run_oracle_nop.py` always allows a networked build and then seals the container
when the agent/environment mode is `no-network`.

Do not invent keys such as `entrypoint` or `dockerfile`. Harbor runs
`tests/test.sh` and builds `environment/Dockerfile` by path.

## Instruction, environment, oracle, tests -- the craft

File-level rules live next to the files they govern:

- instruction: `.cursor/rules/05-instruction-writing.mdc`, six principles below
- image: `.cursor/rules/06-environment-and-docker.mdc`
- oracle and verifier: `.cursor/rules/07-oracle-verifier-and-quality.mdc`
- quality bar and common errors: `docs/odyssey-quality-guidelines.md`

### Six instruction principles

1. **Concise.** A few paragraphs of what to do, not an instruction-following marathon.
2. **Well specified.** Absolute paths, output schemas, and invariants. No "make it better".
3. **Interesting.** Real engineering work, not a one-liner or a toy puzzle.
4. **No answers or hints.** Requirements are allowed. Stepwise recipes, detection
   guides, and golden values are not.
5. **Unique.** A different starting state and a different expected outcome, not a
   rename of a known exercise.
6. **Absolute paths.** Write `/app/config/settings.json`, not `config/settings.json`.

Human-written tone. Vary style across tasks. Spec files under `/app` define
what (schemas, protocols), not how-to walkthroughs that dodge the instruction
length by splitting the prompt into the image.

### Oracle: derive, do not echo

```bash
# GOOD -- mutate /app, then run the real program
cd /app && python calculate.py > /app/output/result.txt

# BAD -- hardcode the answer the hidden tests happen to expect
echo "42" > /app/output/result.txt
```

If deleting `solution/` still lets `tests/` compute the complete expected
artifact, the verifier is doing the solving. That logic belongs in `solution/`.

### Tests: behavior, not implementation

Grade the agent's binary, CLI, or public API. Parse outputs. Use golden hashes,
spec-derived invariants, sealed held-out truth, and perturbation re-runs. Do
not grep source for `if not` or `sorted(`. Do not install packages in `test.sh`.
Always write reward `0` on failure; Harbor ignores exit status if the file is
missing.

## What transferred from Terminal-Bench, and what did not

| Terminal-Bench / Terminus | Odyssey in this repo |
|---|---|
| Harbor 2.0 paths (`task.toml`, `instruction.md`, `environment/`, `tests/test.sh`, `solution/solve.sh`) | Same required paths |
| Category radios (nine Snorkel types) | `collectionFamily` (four) plus `taskFamily` |
| Binary reward 0 or 1 | Float in `[0,1]` plus a binary all-groups gate |
| Task Idea Proposal / Batch P | The Odyssey draft fields |
| Rubric sidecar | Not used |
| `stb harbor` / `create_finish_to_zip.sh` | `scripts/run_oracle_nop.py` / `scripts/package_task.py` |
| Required tmux + asciinema | Not required by the Odyssey guide |
| Digest-pinned ECR canonical bases | Pin versions; digest pin when you can, not a local gate |
| Decoy files as a CREATE ritual | Optional anti-gaming in `/app`, not a required prompt |
| Milestone `steps/` layout | Not used; one instruction, one verifier, one oracle |

Use Terminus as a source of Harbor craft, not as a second submission platform.
