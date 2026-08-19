# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Reimplement a Postgres wire-protocol frontend and planner subset

## Working slug

postgres-wire-frontend-planner

## Collection family

Library clone

## Task family

feature_development

## Verifier family

programmatic

## Objective

Rebuild a PostgreSQL-compatible frontend and a constrained query planner from the frozen spec in /app/docs/protocol.md and /app/docs/planner.md. Remaining work is a complete protocol stack, not a parser feature: startup and authentication, simple-query mode, the extended parse/bind/execute/describe/close cycle, COPY in and out, listen/notify, error fields, and a planner that produces the documented join order, parameter types, and catalog lookups against /app/catalog. Done means a client speaking the wire protocol through the public socket in /app can complete held-out sessions, and the planner matches the spec on generated catalogs rather than on the visible examples.

## Motivation

This is the shape of reproducing a production frontend: an agent has to implement an entire protocol and planner against a spec and a catalog, then keep them coherent under session reuse. It stands in for library-clone work that takes an expert days, not a nested-syntax ticket in an existing parser.

## Difficulty explanation

The remaining surface is several interacting subsystems (startup, simple query, extended protocol, COPY, notify, planner). The first-attempt trap is treating extended protocol as a wrapper around simple query and planning only the visible join shapes. That passes a short happy-path session and fails hidden bind/execute mismatch, portal reuse, COPY boundary framing, and generated catalogs whose statistics change join order. Padding hours on a single parse function would not create this surface.

## Expert time estimate (hours)

80

## Environment summary

The sandbox is a pinned language image with the protocol spec, catalog fixtures, a compiling skeleton (socket accept loop, stub message codec, empty planner), and decoy admin utilities that are not on the graded path. Dependencies are baked in. Runtime network is sealed; the agent speaks the protocol on a local socket. No tests or solution files are in the image.

## Resource estimate

cpuMillis: 4000
memoryMb: 16384
storageMb: 20480
gpuCount: 0
agentTimeoutSec: 18000
verifierTimeoutSec: 1800

## Network requirements

mode: none
justification: The task is fully self-contained and grading should remain deterministic.
hosts: (none)

## Oracle strategy

The reference solution implements the message codec, session state machine, extended-protocol portals, COPY framing, notify delivery, and the planner described by the spec, then copies those sources into /app. It derives behavior from the spec and catalog, and does not echo held-out session transcripts.

## Verification strategy

The verifier runs tests/test.sh. Visible checks drive a short simple-query plus one extended-protocol session so the agent can aim. Hidden enumerated sessions cover bind/execute reuse, COPY, notify, and error fields the visible set does not contain. A generated hidden group builds catalogs and parameter sequences so a hard-coded transcript cannot pass. Visible weight is a minority of the float.

## Binary success condition

The task passes only if the full verifier suite completes successfully: visible sessions, hidden sessions, and generated catalog/planner cases all pass.

## Partial score strategy

Partial credit is awarded by independently weighted groups (visible sessions, hidden protocol cases, generated planner cases). Protocol failures and planner failures are separate channels. Score rises only with real subsystem progress.

## Anticipated exploits

The agent may implement only simple query, special-case visible sessions, or plan only the sample catalog. Hidden sessions and generated catalogs defeat that. Hard-coding transcripts fails because generated inputs change. Editing the verifier fails because tests/ is not in the image.
