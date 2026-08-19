# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Optimize a CDCL SAT solver to a conflict target with proof logging

## Working slug

cdcl-sat-conflict-target

## Collection family

Algorithmic optimization

## Task family

performance

## Verifier family

optimization

## Objective

Optimize the CDCL core in /app so it preserves proof-logging semantics while meeting the held-out conflict and runtime targets in /app/docs/solver.md. Remaining work is the solver itself: VSIDS, clause management, inprocessing, and DRAT-style proof logging that a checker in the verifier can replay. Done means every visible and hidden instance is SAT/UNSAT-correct with a valid proof, and the conflict budget on held-out families clears the documented target. This is not reducing peak memory in an already-correct batched diff helper.

## Motivation

Optimization work in this collection is beating a tight target on a substantial solver or custom-ISA kernel without breaking the spec. A local allocation tweak on a correct helper is not that job.

## Difficulty explanation

The remaining surface is heuristic interaction: VSIDS decay, clause deletion, restart, and inprocessing all change conflict counts, and any of them can invalidate proofs. The first-attempt trap is disabling proof logging or special-casing visible CNFs to fake the conflict number. Hidden families and an independent proof checker catch that. A memory-reduction ticket on a batched diff would still be too short for the collection even if a model failed it.

## Expert time estimate (hours)

80

## Environment summary

The image has a correct but slow CDCL baseline, instance families, a proof-logging API, and profiling helpers. The toolchain is pinned. Runtime is sealed. Held-out families used for the conflict target are not in /app.

## Resource estimate

cpuMillis: 8000
memoryMb: 16384
storageMb: 20480
gpuCount: 0
agentTimeoutSec: 18000
verifierTimeoutSec: 3600

## Network requirements

mode: none
justification: The benchmark harness and datasets are bundled locally for deterministic offline grading.
hosts: (none)

## Oracle strategy

The reference solution changes VSIDS, clause management, and inprocessing while keeping proof logging intact, then leaves a solver that meets the hidden conflict target. It does not bake instance answers.

## Verification strategy

Visible checks require correctness plus proof replay on public instances. Hidden groups add held-out families and a conflict-target gate. A generated group perturbs CNFs so baked answers fail. Visible weight is a minority. Binary success requires correctness, valid proofs, and the target.

## Binary success condition

The task passes only if all instances are solved correctly with valid proofs and the held-out conflict target is met.

## Partial score strategy

Partial credit for correctness-preserving improvements that move conflict counts toward the target. Any proof or SAT/UNSAT break scores zero on that group.

## Anticipated exploits

The agent may skip proofs, special-case visible CNFs, or emit precomputed SAT/UNSAT bits. The checker and generated instances defeat that.
