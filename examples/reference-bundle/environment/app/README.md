# rangespec

Parses page-range specifications used by the print pipeline.

`parse_spec(spec)` returns the pages a specification selects, in ascending order,
with no duplicates.

## Accepted syntax

- a single page: `7`
- an ascending range, inclusive at both ends: `4-9`
- a descending range, meaning the same pages as its ascending form: `9-4`
- any number of the above joined by commas, with optional surrounding whitespace

## Failure behaviour

`parse_spec` raises `ParseError` for input it cannot interpret: empty segments,
non-integer parts, missing range bounds, and page numbers below 1.
