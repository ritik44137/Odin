# Bad Example: Instruction Is a Recipe

## Why this is bad

Harbor `instruction.md` must state requirements, not the solution. A stepwise
recipe, a detection guide, or a dump of golden values collapses the task into
instruction-following. Frontier agents then one-shot it, and the difficulty
probe rejects it for the right reason.

## Weak instruction excerpt

Implement the parser in `/app` as follows:

1. Split the spec on commas.
2. For a token matching `(\d+)-(\d+)`, emit every integer from min to max.
3. The golden output for `3-1,5,5` is `1,2,3,5`.
4. Detection guidance: watch for descending ranges, duplicate pages, and
   `int()` raising `ValueError` on empty segments.

## Problems

- The numbered steps are the reference solution.
- The golden string is a held-out expectation the hidden tests will check.
- "Detection guidance" lists the bugs, so diagnosis is no longer the work.
- Absolute paths are used, which is good, but they do not rescue a recipe.

## Better pattern

State the public behavior (`parse_spec` returns the sorted unique union;
invalid input raises `ParseError`) and point at `/app/README.md` for the
domain. Leave the algorithm, the bug list, and the expected tuples in
`solution/` and `tests/hidden/`.
