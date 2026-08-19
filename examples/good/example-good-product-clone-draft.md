# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Clone a code-review product with PRs, checks, and webhooks

## Working slug

code-review-product-clone

## Collection family

Product clone

## Task family

systems_integration

## Verifier family

programmatic

## Objective

Build a GitHub-like code review service from the product spec in /app/docs/product.md: repositories, pull requests, review comments and requested changes, required status checks, protected branches, identity and tokens, webhook delivery with retries, and a browser UI for the review workflow. Done means the HTTP API, persistence, background delivery, and UI-visible states all match the spec on visible flows and on hidden multi-actor, retry, and permission cases. This is a full-stack clone, not an offline approval queue bolted onto an existing app slice.

## Motivation

Product-clone work in this collection is cloning a real application surface -- APIs, jobs, auth, and UI -- the way an engineer would stand up a competitor slice. A single reconnect-safe form is not that job.

## Difficulty explanation

The remaining work is several product subsystems that only succeed together: authz on protected branches, check rollup vs required contexts, review-comment identity, and at-least-once webhook delivery. The first-attempt trap is a CRUD PR store that passes the visible happy path while failing hidden permission, retry, and UI-state cases. A shallow UI patch without durable delivery still fails hidden groups.

## Expert time estimate (hours)

120

## Environment summary

The image contains the product spec, a compiling skeleton (HTTP server, empty stores, stub UI), local mail/webhook sinks, and decoy billing routes off the graded path. Node or equivalent tooling is pinned and baked in. Runtime is sealed. The agent implements the service under /app.

## Resource estimate

cpuMillis: 4000
memoryMb: 16384
storageMb: 20480
gpuCount: 0
agentTimeoutSec: 18000
verifierTimeoutSec: 2400

## Network requirements

mode: none
justification: The task simulates webhook delivery locally and does not require external hosts.
hosts: (none)

## Oracle strategy

The reference solution implements API handlers, durable stores, check rollup, protected-branch rules, and a retrying webhook worker, plus the UI states the spec names. It derives those behaviors from /app/docs/product.md rather than echoing held-out fixtures.

## Verification strategy

Visible checks cover open PR, one review, one check, one webhook. Hidden enumerated cases add permission denials, required-check failure, duplicate deliveries, and UI consistency after refresh. A generated group varies actors and retry schedules. Visible weight is a minority.

## Binary success condition

The task passes only if API, persistence, webhook delivery, and UI-visible state all pass visible and hidden groups.

## Partial score strategy

Independent weights for API correctness, authz, webhook delivery, and UI state. Hidden authz or delivery failures reduce score sharply.

## Anticipated exploits

The agent may fake webhook success in memory, special-case visible PR ids, or patch the UI without durable stores. Hidden retries, permission matrices, and generated actors defeat that.
