"""Public checks. The agent can read and run these; they state what done means."""
import pytest

from rangespec import ParseError, parse_spec


def test_single_page():
    assert parse_spec("7") == [7]


def test_ascending_range():
    assert parse_spec("4-6") == [4, 5, 6]


def test_comma_separated():
    assert parse_spec("1-3,8") == [1, 2, 3, 8]


def test_descending_range_matches_its_ascending_form():
    assert parse_spec("6-4") == [4, 5, 6]


def test_whitespace_is_ignored():
    assert parse_spec(" 1 - 2 , 5 ") == [1, 2, 5]


def test_empty_segment_is_rejected():
    with pytest.raises(ParseError):
        parse_spec("1,,2")
