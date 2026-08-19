# Open Questions and Local Assumptions

The source authoring guide is detailed about the submission flow, the required
paths, and the resource and network ceilings. It is silent on several things a
bundle still has to commit to. Where this repo had to choose, the choice is
recorded here so nobody mistakes a guess for a documented rule.

Before your first real submission, confirm each of these against the platform's own
task format documentation, and correct the templates and validator if they differ.

## Repository layout

**Local convention, not a platform rule.** The guide says nothing about how you
organise work on your own machine; it only specifies what must be inside the uploaded
ZIP. So `drafts/<slug>.md`, `plans/<slug>.md`, `tasks/<slug>/`, and `zip/<slug>.zip`
are this repository's choice, described in `docs/odyssey-repo-layout.md`.

The one part that touches the platform is that `tasks/<slug>/` is the bundle root, so
its contents are exactly what the grader receives. That is why planning artifacts live
in `plans/` rather than beside the task files.

## Verifier score reporting

**Confirmed (Harbor):** `tests/test.sh` must write `/logs/verifier/reward.txt`
(a single float in `[0,1]`) or `/logs/verifier/reward.json` (numeric metrics).
Harbor downloads that directory after the script exits and fails the trial with
"Verifier completed without writing a reward file" if neither exists. Exit status
is not a substitute. Write the file on every path, including failures; an `EXIT`
trap is the reliable way.

**Local convention:** the same float is also printed as `ODYSSEY_SCORE=<float>`
so `run_oracle_nop.py` can read it from stdout. If that marker is absent, the
local harness falls back to exit status (`0 -> 1.0`, non-zero -> `0.0`).

**Consequence if missing:** the platform records an infra-style verifier failure
instead of a score, even when the oracle would have earned full reward.

## What `environment/` becomes

**Documented:** "`environment/` becomes `/app` and must include a Dockerfile."

**Assumed:** the build context is `environment/`, and the Dockerfile explicitly
copies the starting state into `/app` (`COPY app/ /app/` in the reference bundle).
This works under either reading and never puts the Dockerfile itself into `/app`.

**Unknown:** whether the harness instead copies the whole of `environment/` into
`/app` and treats the Dockerfile as build instructions only. Under that reading,
anything you place in `environment/` is agent-visible.

**Consequence if wrong:** files you assumed were build-only would be readable by
the agent. Mitigate by never placing anything in `environment/` that you would not
hand the agent.

## `task.toml` key names

**Documented:** the four sections `[metadata]`, `[verifier]`, `[agent]`,
`[environment]`; the fields `network_mode` per phase; the `[environment]` resource
figures `cpus`, `memory_mb`, `storage_mb`, `gpus`; and
`[metadata] open_internet_justification`.

**Harbor schema (confirmed):** `network_mode` is the Harbor `NetworkMode` enum
`no-network` | `public` | `allowlist`. The draft form still says `none` /
`allowlist`; `none` maps to `no-network`, and `public` is Harbor's spelling of
open egress (refused for `[agent]`). `timeout_sec`, `workdir`, `name`,
`working_slug`, the `*_family` fields, and `allowed_hosts` are the Harbor /
Odyssey keys. `entrypoint` and `dockerfile` are not Harbor fields; the grader
runs `tests/test.sh` and builds `environment/Dockerfile` by path.

**Invalid (the values this repo used to invent):** `none`, `open`, `enabled`,
`disabled`. Harbor's pydantic parser rejects them, which surfaces as
"task.toml is invalid".

## `[environment] network_mode` values

**Documented:** the image *build* is not gated, and a build that fetches packages
is normal.

**Harbor schema (confirmed):** `[environment].network_mode` is the *runtime
baseline* applied when the agent environment starts, not docker-build
networking. Default is `public`. For a sealed Odyssey task, set environment,
agent, and verifier all to `no-network` so there is no phase override. A
mismatch between baseline and `[agent].network_mode` requires
`dynamic_network_policy` or Harbor rejects the task.

`run_oracle_nop.py` always allows a networked image build, and seals the
container run when the agent/environment mode is `no-network`.

## Allowlist enforcement during local runs

`run_oracle_nop.py` runs containers on Docker's `bridge` network when the bundle
declares `allowlist`, because reproducing a host allowlist locally is out of scope.
That is *broader* than the real rollout, so a hidden dependency on an unlisted host
will pass locally and fail upstream. Prefer `none`.

## What the nop floor actually is

**Assumed:** the untouched starting state scores 0. The guide says only that it
must "sit at its floor", which for a task with a non-zero baseline metric — an
optimization task, say — is not zero. Pass `--nop-max` to `run_oracle_nop.py` to
declare the real floor, and make `partialScoreStrategy` state it explicitly.

## Similarity threshold

`check_novelty.py` compares against local drafts only, with a TF-IDF cosine
threshold of 0.55 chosen so the four example drafts read as distinct. The platform
uses embeddings over the whole corpus, so a local pass says nothing about
collisions with other authors' tasks. It only catches you duplicating yourself.

## Terminal-Bench requirements this repo does not copy

`terminal-bench-reference/` (Terminus) encodes Snorkel Terminal-Bench Edition 2
policy. Several of those requirements are **not** Odyssey rules. The Harbor
runtime model that *does* transfer is in `docs/harbor-task-anatomy.md`.

**tmux and asciinema.** Terminus fails a pack if the final image lacks `tmux`
and `asciinema`, because Snorkel records agent sessions that way. The Odyssey
authoring guide does not mention them. Do not install them unless the task
itself needs a terminal multiplexer.

**Digest-pinned canonical ECR bases.** Terminus requires `@sha256:<digest>` on
every `FROM` and a sanctioned ECR image. Odyssey requires a reproducible image
with pinned package versions. Digest pinning is good practice, not a local gate.

**Binary 0/1 reward.** Terminus writes `1` or `0`. Odyssey writes a float in
`[0,1]` and keeps a separate binary gate (all groups pass). Harbor accepts either
file format; this repo's templates use the float.

**Nine taxonomy categories, rubrics, milestones, decoy counts.** Odyssey
classifies with `collectionFamily` / `taskFamily` / `verifierFamily`. There is
no rubric sidecar, no milestone `steps/` layout, and no required `decoys: N`
CREATE prompt. Decoy files in `/app` are a difficulty mechanism (off the
graded hot path); they are not a ritual count. See
`docs/odyssey-difficulty-design.md`.

**Mandatory ingest -> staging -> export.** Terminus required that pipeline on
Go/Rust CLI tasks (Case 6). Copying it onto every Odyssey slug would fail
similarity. Use the *mechanisms* (interaction, decoys, chained failure) in a
shape native to the family.

**Hard <= 20% / reject > 80%.** Those bands are Snorkel Terminal-Bench
Welcome text. Odyssey's authoring guide only says the probe fails if a
frontier agent saturates, or if the task is unsolvable. This repo does not
treat 20% as an Odyssey published number. Design as if the agent must not
one-shot the work.

**Engines.** Numbered ENGINE_1-8 are a local authoring convention, adapted
from Terminus so Cursor does not invent a lane. They are not an Odyssey
platform API. Too-easy work goes to ENGINE_8 (structural mechanisms), not
Terminus Case 6.

## Difficulty probe vs local heuristic

`scripts/check_difficulty_design.py` is a shape scan (recipe prompts, visible
majority weight, interview exercises, ticket-sized remaining work). A PASS is
not a probe pass. Author probes V/D/L/A are still mandatory.

The Odyssey form still treats `expertTimeEstimateHours` as unconstrained
metadata and 7200s as the agent-timeout floor. Observed Automated Difficulty
verdicts (`Too short for the collection -- not long-horizon`) and
SWE-Marathon's published envelope (40-400 expert hours, 2-10h agent, 5h
template) are a **local collection bar**, recorded in
`docs/odyssey-long-horizon.md` and enforced by `scripts/odyssey_horizon.py`.
Padding hours or the clock on a ticket is not a substitute. Frontier-model
failure is not a horizon argument.
