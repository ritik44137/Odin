# Task

The `rangespec` library in `/app` parses page-range specifications for a printing
pipeline. Its current implementation only handles simple ascending ranges, and
callers are hitting wrong output and unhelpful crashes on everything else.

## Objective

Make `rangespec.parse_spec` implement the behaviour documented in
`/app/README.md`, without changing its public signature or the name and base
class of `ParseError`.

## Requirements

- Return the selected pages in ascending order with duplicates removed, whatever
  order the segments appear in.
- Treat a descending range as equivalent to its ascending form.
- Ignore whitespace around segments and around range bounds.
- Raise `ParseError` for input that cannot be interpreted: empty specifications,
  empty segments, non-integer parts, missing range bounds, and page numbers below 1.
- `ParseError` must remain a subclass of `ValueError`, since callers catch that.

## What success looks like

`parse_spec` behaves as a total function over its documented input domain: every
valid specification returns the sorted, de-duplicated union of its segments, and
every invalid one raises `ParseError` rather than `IndexError`, `TypeError`, or a
bare `ValueError` from `int()`.

Grading runs the public checks under `tests/visible`, a held-out set of enumerated
edge cases, and property checks over generated specifications. Passing only the
visible checks is not sufficient.

## Constraints

- There is no network access. Everything you need is already installed.
- Do not modify anything under `tests/`; the graded copy is not the one you can see.
- Keep the change inside `/app/rangespec/`.
