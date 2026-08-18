#!/usr/bin/env bash
# Canonical reference-solution entrypoint. The oracle runs exactly this file.
set -euo pipefail

cd /app

cat > /app/rangespec/parser.py <<'PY'
"""Parse page-range specifications like "1-3,5,9-11" into integer lists."""
import re

SEGMENT_RE = re.compile(r"^(?P<start>\d+)(?:-(?P<end>\d+))?$")


class ParseError(ValueError):
    """Raised when a specification cannot be parsed."""


def _page(text, spec):
    if not SEGMENT_RE.match(text):
        raise ParseError(f"invalid page {text!r} in {spec!r}")
    value = int(text)
    if value < 1:
        raise ParseError(f"page numbers start at 1, got {value} in {spec!r}")
    return value


def parse_spec(spec):
    if not isinstance(spec, str):
        raise ParseError(f"expected a string, got {type(spec).__name__}")
    if not spec.strip():
        raise ParseError("specification is empty")

    pages = set()
    for raw in spec.split(","):
        segment = "".join(raw.split())
        if not segment:
            raise ParseError(f"empty segment in {spec!r}")

        match = SEGMENT_RE.match(segment)
        if match is None:
            raise ParseError(f"invalid segment {raw!r} in {spec!r}")

        start = _page(match.group("start"), spec)
        end_text = match.group("end")
        if end_text is None:
            pages.add(start)
            continue

        end = _page(end_text, spec)
        pages.update(range(min(start, end), max(start, end) + 1))

    return sorted(pages)
PY

python -c "from rangespec import parse_spec; assert parse_spec('1-3,7-5') == [1,2,3,5,6,7]"
echo "reference solution applied"
