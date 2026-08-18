# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Reduce peak memory in batched diff computation without changing output semantics

## Working slug

reduce-peak-memory-batched-diff

## Collection family

Algorithmic optimization

## Task family

performance

## Verifier family

optimization

## Objective

Optimize an existing batched diff engine so it preserves exact output semantics while substantially reducing peak memory usage on large input sets. The agent must modify the implementation to stay correct on all visible and hidden cases, including stable ordering and diff completeness, while improving memory behavior enough to satisfy the verifier's optimization thresholds. Done means the solver meets correctness requirements first and then clears the held-out memory targets under the benchmark harness.

## Motivation

This task represents realistic systems work where an implementation is functionally correct but operationally too expensive at production scale, so engineering effort focuses on reducing resource consumption without changing externally visible behavior.

## Difficulty explanation

The challenge is balancing strict semantic preservation against resource reduction. Naive changes can lower memory in one path while breaking stable ordering, completeness, or worst-case behavior on irregular workloads. The agent must understand where allocations accumulate, restructure data flow carefully, and avoid optimizing only the visible benchmark inputs. Hidden tests and benchmarks can catch changes that trade correctness for superficial wins.

## Expert time estimate (hours)

7

## Environment summary

The sandbox contains a compiled-language service in /app with a benchmark harness, visible correctness tests, and profiling helpers. The toolchain and benchmark dependencies are preinstalled in the image. The task runs fully offline and all benchmark inputs are bundled locally.

## Resource estimate

cpuMillis: 6000
memoryMb: 8192
storageMb: 4096
gpuCount: 0
agentTimeoutSec: 7200
verifierTimeoutSec: 3600

## Network requirements

mode: none
justification: The benchmark harness and datasets are bundled locally for deterministic offline grading.
hosts: (none)

## Oracle strategy

The reference solution restructures the diff pipeline to stream or chunk intermediate state, reuses memory where safe, and preserves exact output ordering and completeness. It also retains compatibility with the existing public API and clears both correctness and optimization thresholds in the verifier.

## Verification strategy

The verifier first runs correctness checks on visible and hidden datasets, then runs benchmark measurements on held-out workloads to assess peak memory and related resource behavior. Visible checks tell the agent that correctness is non-negotiable and expose representative benchmark structure. Hidden checks include adversarial workload shapes and larger cases so the task cannot be solved by overfitting to one benchmark profile. Scoring combines semantic correctness with optimization performance, and binary success requires both correctness and threshold achievement.

## Binary success condition

The task passes only if the optimized implementation preserves all required outputs on the full verifier suite and meets the held-out peak-memory target under the benchmark harness.

## Partial score strategy

Partial credit is awarded for correctness-preserving improvements that reduce memory usage monotonically toward the target, with zero credit for changes that break semantic correctness even if they improve resource metrics.

## Anticipated exploits

The agent may try to skip portions of the diff, degrade ordering guarantees, special-case benchmark inputs, or move work in ways that make visible metrics look better while breaking hidden workloads. The verifier defeats this by checking exact outputs, varying workload structure, and benchmarking held-out inputs that expose shallow optimizations.
