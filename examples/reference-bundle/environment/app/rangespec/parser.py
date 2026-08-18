"""Parse page-range specifications like "1-3,5,9-11" into integer lists.

The current implementation handles simple ascending ranges only. See README.md
for the behaviour the printing pipeline needs.
"""


class ParseError(ValueError):
    """Raised when a specification cannot be parsed."""


def parse_spec(spec):
    result = []
    for segment in spec.split(","):
        if "-" in segment:
            start, end = segment.split("-")
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(segment))
    return result
