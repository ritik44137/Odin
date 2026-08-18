# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.

## Title

Make page-range parsing a total function over its documented domain

## Working slug

rangespec-total-parse

## Collection family

Library clone

## Task family

debugging

## Verifier family

programmatic

## Objective

Repair rangespec.parse_spec in /app so it implements the behaviour documented in /app/README.md: return the ascending, de-duplicated union of the pages a specification selects, treat a descending range as equivalent to its ascending form, tolerate whitespace around segments and bounds, and raise ParseError for every input outside the documented domain. The public signature must not change, ParseError must keep its name and remain a subclass of ValueError, and the change must stay inside /app/rangespec/. Done means every valid specification returns the sorted, de-duplicated union of its segments and every invalid one raises ParseError rather than leaking IndexError, TypeError, or a bare ValueError from int().

## Motivation

This is the shape of a real maintenance bug: a helper that was written for the happy path is now load-bearing for a pipeline that feeds it messy user input, and the fix has to make failure behaviour uniform without breaking the callers that already catch ValueError. Bundled here as a plumbing exemplar rather than a submittable task.

## Difficulty explanation

The trap is that the visible checks are satisfiable with a small patch that still fails the held-out grading, because sorting and de-duplication are properties of the whole result rather than of any one segment, and because uniform error behaviour requires validating the segment shape before converting to int rather than letting int() raise. Property checks over generated specifications also catch a fix that special-cases the enumerated inputs. As a deliberately small exemplar this is far easier than a real submission should be.

## Expert time estimate (hours)

0.75

## Environment summary

python:3.11-slim with pytest 8.3.4 baked into the image and no network at rollout. /app holds the rangespec package (__init__.py and parser.py) plus README.md documenting the required behaviour. The verifier and reference solution are mounted outside /app at grade time, so nothing in the agent's working tree reveals the held-out cases.

## Resource estimate

cpuMillis: 2000
memoryMb: 2048
storageMb: 2048
gpuCount: 0
agentTimeoutSec: 7200
verifierTimeoutSec: 900

## Network requirements

mode: none
justification: Every dependency is baked into the image, and sealed execution keeps grading deterministic.
hosts: (none)

## Oracle strategy

solution/solve.sh rewrites /app/rangespec/parser.py so segments are matched against an anchored regex before conversion, page numbers below 1 are rejected explicitly, descending bounds are normalised with min/max, and results are accumulated in a set and returned sorted. It then asserts one representative case inline so the oracle fails loudly if the rewrite is broken, which drives all three verifier groups to full reward.

## Verification strategy

tests/test.sh runs three independently weighted groups and prints a score. The visible group (tests/visible, weight 30) is the public statement of done and mirrors instruction.md. The first hidden group (weight 40) enumerates held-out edge cases: unordered and overlapping segments, repeated pages, single-element ranges, descending bounds, and twelve invalid specifications. The second hidden group (weight 30) checks properties over 600 generated specifications, asserting the result is sorted, unique, equal to the union of its segments, and invariant under segment reordering. Grading imports the library from /tmp through its public surface, so it measures behaviour rather than implementation, and the generated inputs mean the enumerated cases cannot be memorised.

## Binary success condition

All three verifier groups pass, so tests/test.sh exits 0 and reports ODYSSEY_SCORE=1.0000.

## Partial score strategy

Score is earned weight over total weight across the three groups: 0.30 for the visible behaviour group, 0.40 for held-out edge cases, 0.30 for the invariant properties. The floor is 0.0 because the untouched parser fails all three, and the score rises monotonically as real behaviour is fixed, so a solution that handles valid input but not error semantics still scores partial credit.

## Anticipated exploits

An agent may patch only the visible cases, which the two hidden groups defeat. It may hard-code the enumerated expectations, which the generated property checks defeat because the inputs are not fixed. It may try to edit the verifier, which fails because tests/ is never copied into the image and the graded copy is mounted at grade time outside /app. It may shadow the library with a module in the working directory, which fails because grading runs from /tmp with PYTHONPATH pinned to /app. It may broaden ParseError to swallow everything, which fails because valid specifications must still return exact page lists.

## Notes (local only -- do not paste)

This draft accompanies examples/reference-bundle/ and exists to exercise the local tooling end to end. It is intentionally far too easy to submit.
