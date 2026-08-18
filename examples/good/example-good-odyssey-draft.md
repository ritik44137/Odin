# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Rebuild strict TOML parsing for nested inline tables

## Working slug

strict-toml-nested-inline-tables

## Collection family

Library clone

## Task family

feature_development

## Verifier family

programmatic

## Objective

Implement support for strict parsing and validation of nested inline tables in an existing TOML parser library. The agent must update the parser so it accepts valid nested inline-table constructs, rejects malformed or duplicate-key variants with precise failure behavior, and preserves compatibility with the rest of the parser API. Done means the updated parser passes both visible regression tests and hidden conformance cases that exercise nested structures, duplicate keys, whitespace normalization, and mixed table syntax interactions.

## Motivation

This task stands in for real maintenance work on a configuration parsing library where edge-case correctness matters because downstream systems depend on deterministic parsing semantics and clear failures on invalid input.

## Difficulty explanation

The difficulty is not just adding syntax support. The agent must reason about parser state transitions, duplicate-key semantics across nested scopes, and compatibility with existing behavior. Naive fixes often pass happy-path examples while breaking error handling, key shadowing rules, or mixed parsing of regular tables and inline tables. The hidden tests can detect shallow patches that only special-case obvious samples.

## Expert time estimate (hours)

6

## Environment summary

The sandbox contains a small parser codebase in /app written in Python with pytest preinstalled. The working tree includes the parser implementation, a subset of visible tests, and developer notes describing high-level TOML compliance expectations. No runtime network access is needed. The agent edits the library locally and runs tests in the containerized environment.

## Resource estimate

cpuMillis: 4000
memoryMb: 4096
storageMb: 2048
gpuCount: 0
agentTimeoutSec: 7200
verifierTimeoutSec: 1800

## Network requirements

mode: none
justification: The task is fully self-contained and grading should remain deterministic.
hosts: (none)

## Oracle strategy

The reference solution updates the parser grammar and validation logic for inline tables, adds recursive handling for nested inline structures, enforces duplicate-key checks across nested scopes, and preserves existing public API behavior. The solution also includes regression coverage to ensure hidden and visible cases reach full reward.

## Verification strategy

The verifier runs tests/test.sh, which executes visible regression tests plus held-out cases. Visible tests show the required public behavior for valid nested inline tables and representative invalid inputs. Hidden tests cover additional malformed variants, tricky duplicate-key interactions, table-order edge cases, and API compatibility checks. Success depends on parser behavior and failure semantics, not on matching a specific implementation.

## Binary success condition

The task passes only if the full verifier suite completes successfully with no failing visible or hidden cases.

## Partial score strategy

Partial credit is awarded by percentage of verifier checks passed, with core correctness groups weighted more heavily than minor compatibility checks. Hidden failures in duplicate-key or malformed-input categories reduce score materially because they indicate shallow or unsafe fixes.

## Anticipated exploits

The agent may try to special-case only the visible examples, bypass duplicate-key validation, or weaken error handling so malformed inputs parse silently. The hidden tests defeat this by varying syntax shapes, key orders, spacing, and mixed table forms. Because the verifier checks parser behavior through the public API on unseen inputs, hard-coding known outputs is ineffective.
