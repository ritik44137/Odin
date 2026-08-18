"""Invariants checked over generated input, so hard-coding cases cannot pass.

The properties hold for every valid specification, which is what makes them a
different grading channel from the enumerated cases in test_edge_cases.py.
"""
import random

from rangespec import parse_spec


def random_spec(rng):
    segments = []
    for _ in range(rng.randint(1, 6)):
        if rng.random() < 0.5:
            segments.append(str(rng.randint(1, 40)))
        else:
            a, b = rng.randint(1, 40), rng.randint(1, 40)
            segments.append(f"{a}-{b}")
    return ",".join(segments)


def test_output_is_sorted_unique_and_matches_the_segment_union():
    rng = random.Random(20260818)
    for _ in range(400):
        spec = random_spec(rng)
        pages = parse_spec(spec)

        assert pages == sorted(pages), spec
        assert len(pages) == len(set(pages)), spec

        expected = set()
        for segment in spec.split(","):
            if "-" in segment:
                a, b = (int(x) for x in segment.split("-"))
                expected.update(range(min(a, b), max(a, b) + 1))
            else:
                expected.add(int(segment))
        assert set(pages) == expected, spec


def test_order_of_segments_does_not_change_the_result():
    rng = random.Random(99)
    for _ in range(200):
        segments = random_spec(rng).split(",")
        forward = parse_spec(",".join(segments))
        rng.shuffle(segments)
        assert parse_spec(",".join(segments)) == forward
