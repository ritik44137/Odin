# Odyssey Long-Horizon Collection Bar

The automated difficulty stage rejects ticket-sized Harbor work with
`Too short for the collection -- not long-horizon`. That verdict is about
**remaining expert work**, not about whether a frontier model already fails
the task, and not about whether `[agent].timeout_sec` is at least 7200.

This page is the local calibration. Design the idea against it in ENGINE_1.
Do not scaffold a ticket and hope ENGINE_8 will stretch it later.

## What the collection actually is

Odyssey's four `collectionFamily` values are the same families as
SWE-Marathon (Harbor tasks, visible/hidden verifiers, multi-hour rollouts):

| Family | Collection-scale remaining work | Not collection-scale |
|---|---|---|
| Library clone | Reproduce a complete real library, compiler, decoder, interpreter, LSP, or control plane against a frozen spec/RFC | Add a feature to an existing parser; implement one Go module from stubs |
| Product clone | Clone a full application: APIs, persistence, auth, jobs, and the product surface (UI or SDK) | One workflow slice (offline queue, invoice retry) in an existing app |
| ML engineering | Train, post-train, port, or kernel-optimize a real model under a hard cap, or build a multi-dataset eval harness | Repair a broken classifier eval pipeline to recover F1 |
| Algorithmic optimization | Beat a tight cycle/quality target on a substantial solver or custom-ISA kernel without breaking correctness | Reduce peak memory in an already-correct batched helper |

Accepted public Harbor tasks in that collection include rebuilding a
framework (routing, middleware, SSR, SSG), a multi-pass C compiler with
codegen, a Kubernetes-scale control plane, a language server with source
analysis, a Zstandard decoder from RFC, full-stack clones (chat, sheets,
object storage, payments), Parameter-Golf-style training under a checkpoint
cap, and custom-ISA kernel optimization.

SWE-Marathon's published envelope: **expert-human estimates 40 to 400 hours**,
**agent timeouts 2 to 10 hours**, template default **5 hours / 4 CPUs / 16 GB /
20 GB**. Their CONTRIBUTING note is the calibration in one line: Harbor's
stock `harbor tasks init` defaults are about **100x too small**. Terminal-Bench
2 and LHTB (tens of minutes to ~90 minutes of agent work) are the wrong
yardstick.

A 32-hour in-process merge library, even with diff3, unified diffs, binaries,
and tree+rename, still failed this funnel stage. Padding hours or the clock
on the same module does not change the verdict.

## Two independent bars

The difficulty probe can fail a well-built bundle for either reason:

1. **Too short / not long-horizon.** A qualified expert would finish the
   remaining work in a sitting or a day. The deliverable is a ticket, a
   focused module, or a single pipeline bug. Frontier-model failure does not
   rescue this. The judge can see the `/app` surface.
2. **Too easy.** The remaining work is large, but a frontier agent one-shots
   it (recall, recipe instruction, visible-majority scoring, one-file fix).

Both must pass. Trap design (`docs/odyssey-difficulty-design.md`) is bar 2.
This page is bar 1.

`difficultyExplanation` must name the remaining-work surface (subsystems the
oracle actually has to build) **and** the first-attempt trap. "Frontier models
fail this" is not a horizon argument. "It takes N hours because the tree is
large" is not a trap argument.

## Local floors (authoring, not the form schema)

The Odyssey form still accepts any positive `expertTimeEstimateHours` and a
7200s agent-timeout minimum. Those are **platform intake** numbers. The
difficulty judge is a different stage.

This repo refuses to scaffold or package a real submission unless:

| Lever | Floor | Do not |
|---|---|---|
| Honest expert remaining work | **>= 40 hours** | Inflate the number on a 6-hour ticket |
| Agent budget | **4-10 hours** (template 5h = 18000s; cap 37000s) | Leave 7200s on a 40-hour clone; padding 7200s on a ticket |
| Deliverable | A complete system in the declared family | A feature, a repair, a slice, a stubbed module of a few public functions |
| Starting state | Spec, assets, incomplete skeleton, decoys | A nearly-finished library with one missing operator |

`scripts/check_difficulty_design.py` encodes the mechanical part of this
(hours, ticket-shaped titles/objectives, missing system-scale signals). It
cannot certify the probe. Plumbing exemplars (`examples/reference-bundle/`)
are exempt because they are documented as not submittable.

## What does not count as lengthening

These were tried and still read as short:

- Raising `expertTimeEstimateHours` without adding subsystems
- Raising `[agent].timeout_sec` on the same `/app`
- Adding more pytest on the same operator
- Expanding one library from three functions to twelve
- "Long-context" dumps of docs that are not the graded system
- Claiming hardness from frontier-model trials on a ticket

Lengthen by changing **what has to be built**: more interacting subsystems
that a real engineer would ship as one project, each graded, with hidden
channels that a partial clone cannot fake.

## ENGINE_1 refusal

Refuse to run `new_task.py` when the idea is any of:

- add/fix/repair a feature in an existing focused library
- one product workflow inside an existing app
- debug a training/eval script
- implement a well-known algorithm or a small greenfield module
- "hard because models fail" with a sitting's worth of remaining work

Ready for ENGINE_3 only when you can name the complete system, the subsystems
an expert would still have to write after reading `/app`, an honest >= 40h
estimate, and a first-attempt trap that is not "the repo is big".
