# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Implement offline invoice approval queue with retry-safe reconciliation

## Working slug

offline-invoice-approval-queue

## Collection family

Product clone

## Task family

systems_integration

## Verifier family

programmatic

## Objective

Implement an offline-capable invoice approval workflow in an existing web application slice. The agent must add queueing and reconciliation logic so approval actions created while disconnected are persisted locally, replayed safely when connectivity is restored, and reflected consistently in application state without duplicate approvals or lost updates. Done means the workflow behaves correctly across visible and hidden end-to-end scenarios covering offline creation, reconnect synchronization, replay idempotency, and UI-visible state consistency.

## Motivation

This task stands in for realistic product engineering work where user actions must remain reliable across intermittent connectivity and where correctness depends on coordinating application state, persistence, and backend synchronization.

## Difficulty explanation

The task is difficult because it crosses multiple application layers. A shallow implementation can appear to work in a simple happy path while failing under reconnect races, duplicate replays, stale state hydration, or partial synchronization. The agent must reason about idempotency, queue lifecycle, state transitions, and user-visible consistency rather than only wiring a button to a request.

## Expert time estimate (hours)

8

## Environment summary

The sandbox contains a JavaScript application in /app with a backend stub, local persistence layer, and a visible subset of integration tests. Node.js, the package manager, and the required test tooling are preinstalled in the image. The task is fully offline at runtime, with all dependencies already baked into the environment.

## Resource estimate

cpuMillis: 4000
memoryMb: 4096
storageMb: 4096
gpuCount: 0
agentTimeoutSec: 7200
verifierTimeoutSec: 2400

## Network requirements

mode: none
justification: The task simulates connectivity transitions locally and does not require external hosts.
hosts: (none)

## Oracle strategy

The reference solution implements a durable local approval queue, reconnect-aware replay logic, idempotent reconciliation against server acknowledgements, and UI state updates that remain consistent across refreshes and reconnect events. It also updates any integration seams needed so the verifier reaches full reward.

## Verification strategy

The verifier runs visible workflow checks and hidden integration cases through tests/test.sh. Visible checks cover basic offline approval creation and later synchronization. Hidden checks add repeated reconnect cycles, duplicate replay attempts, stale local state, interleaved approvals, and UI-state consistency assertions. The verifier inspects persisted queue state, server-side reconciliation effects, and final user-visible outcomes so the task cannot pass through superficial UI patching alone.

## Binary success condition

The task passes only if the full verifier confirms correct offline persistence, replay safety, reconciliation behavior, and consistent final application state across visible and hidden scenarios.

## Partial score strategy

Partial credit is awarded across workflow correctness groups such as offline capture, replay behavior, idempotent reconciliation, and state consistency. Hidden failures in replay safety or duplicate prevention reduce score sharply because they indicate product-breaking behavior.

## Anticipated exploits

The agent may try to fake queue state in memory only, patch the visible UI without durable persistence, special-case visible reconnect scenarios, or suppress duplicate effects without true reconciliation logic. Hidden tests defeat this by forcing refreshes, varying operation order, replaying the same event multiple times, and inspecting both internal state and externally observable outcomes.
