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
