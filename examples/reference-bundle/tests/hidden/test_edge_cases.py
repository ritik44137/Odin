"""Held-out cases. A patch that only satisfies tests/visible fails here."""
import pytest

from rangespec import ParseError, parse_spec


@pytest.mark.parametrize(
    "spec,expected",
    [
        ("3,1,2", [1, 2, 3]),
        ("5-7,6-8", [5, 6, 7, 8]),
        ("2-4,3", [2, 3, 4]),
        ("9,9,9", [9]),
        ("10-10", [10]),
        ("1-3,7-5", [1, 2, 3, 5, 6, 7]),
    ],
)
def test_results_are_sorted_and_deduplicated(spec, expected):
    assert parse_spec(spec) == expected


@pytest.mark.parametrize(
    "spec",
    ["", "   ", "1-", "-4", "a", "1-b", "1--2", "0", "-1", "3-0", "1.5", "1,2,"],
)
def test_invalid_specs_raise_parse_error(spec):
    with pytest.raises(ParseError):
        parse_spec(spec)


def test_parse_error_is_a_value_error():
    with pytest.raises(ValueError):
        parse_spec("nope")
