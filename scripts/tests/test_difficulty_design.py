from pathlib import Path

from conftest import difficulty
from test_validator import INSTRUCTION, TEST_SH, make_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

WEIGHTED_SH = """#!/usr/bin/env bash
set -uo pipefail
run_group() {{ :; }}
run_group "visible-behavior"  {visible} true
run_group "hidden-edge-cases" {hidden} true
run_group "hidden-invariants" {inv} true
mkdir -p /logs/verifier
echo 1 > /logs/verifier/reward.txt
"""


def scan(bundle: Path, draft=None):
    files = difficulty.read_tree(bundle)
    return difficulty.scan(files, draft)


class TestDifficultyDesign:
    def test_clean_weighted_bundle_has_no_errors(self, tmp_path):
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={
                "tests/test.sh": WEIGHTED_SH.format(visible=30, hidden=40, inv=30),
                "tests/hidden/test_held_out.py": (
                    "def test_hidden():\n    assert True\n"
                    "def test_generated_union():\n    for _ in range(10):\n        assert True\n"
                ),
                "environment/app/main.py": "def parse():\n    pass\n",
                "environment/app/decoy/legacy.py": "# unused helper\n",
            },
        )
        findings = scan(bundle)
        assert findings.errors == [], findings.errors

    def test_recipe_instruction_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "instruction.md").write_text(
            INSTRUCTION + "\n\nStep 1: fix parser.py.\nStep 2: first patch merge.go.\n",
            encoding="utf-8",
        )
        findings = scan(bundle)
        assert any("fix recipe" in e for e in findings.errors)

    def test_interview_exercise_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "instruction.md").write_text(
            "# Task\n\nImplement an LRU cache in /app with O(1) get and put.\n",
            encoding="utf-8",
        )
        findings = scan(bundle)
        assert any("interview" in e for e in findings.errors)

    def test_visible_majority_weight_is_an_error(self, tmp_path):
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/test.sh": WEIGHTED_SH.format(visible=70, hidden=20, inv=10)},
        )
        findings = scan(bundle)
        assert any("visible groups hold" in e for e in findings.errors)

    def test_shared_visible_hidden_names_are_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tests" / "visible" / "test_public.py").write_text(
            "def test_public():\n    assert True\ndef test_overlap():\n    assert True\n",
            encoding="utf-8",
        )
        (bundle / "tests" / "hidden" / "test_held_out.py").write_text(
            "def test_public():\n    assert True\ndef test_overlap():\n    assert True\n",
            encoding="utf-8",
        )
        findings = scan(bundle)
        assert any("reuse visible test names" in e for e in findings.errors)

    def test_scale_only_difficulty_explanation_is_an_error(self, tmp_path):
        draft = {
            "title": "Repair the parser",
            "objective": "Make parse_spec in /app handle the documented domain.",
            "difficultyExplanation": "This takes many hours because the codebase is large and complex.",
            "anticipatedExploits": "None expected.",
        }
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/test.sh": WEIGHTED_SH.format(visible=30, hidden=40, inv=30)},
        )
        findings = scan(bundle, draft)
        assert any("scale/time only" in e for e in findings.errors)

    def test_reference_bundle_has_no_errors(self):
        root = REPO_ROOT / "examples" / "reference-bundle"
        draft = difficulty.load_draft(root / "draft.md")
        findings = scan(root, draft)
        assert findings.errors == [], findings.errors
        assert any("grader groups" in n for n in findings.notes)

    def test_ticket_sized_hours_are_an_error(self, tmp_path):
        draft = {
            "title": "Repair nested inline tables",
            "collectionFamily": "Library clone",
            "objective": (
                "Implement support for nested inline tables in an existing parser "
                "library so happy-path documents round-trip."
            ),
            "environmentSummary": "A small focused parser module in /app.",
            "expertTimeEstimateHours": 6,
            "difficultyExplanation": (
                "The first-attempt trap is a naive recursive descent that passes "
                "visible samples and fails hidden duplicate-key invariants."
            ),
            "anticipatedExploits": "A visible-only hard-code of the sample documents.",
        }
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/test.sh": WEIGHTED_SH.format(visible=30, hidden=40, inv=30)},
        )
        findings = scan(bundle, draft)
        assert any("collection floor" in e for e in findings.errors)
        assert any("ticket-sized" in e for e in findings.errors)

    def test_plumbing_exemplar_skips_horizon_floor(self, tmp_path):
        draft = {
            "title": "Make page-range parsing a total function",
            "collectionFamily": "Library clone",
            "objective": "Repair parse_spec in an existing helper.",
            "motivation": "Bundled here as a plumbing exemplar rather than a submittable task.",
            "expertTimeEstimateHours": 0.75,
            "difficultyExplanation": "Deliberately small exemplar with a visible-only trap.",
            "anticipatedExploits": "Hard-code the visible cases.",
            "notes": "plumbing exemplar",
        }
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/test.sh": WEIGHTED_SH.format(visible=30, hidden=40, inv=30)},
        )
        findings = scan(bundle, draft)
        assert not any("collection floor" in e for e in findings.errors)

    def test_good_example_drafts_pass_horizon_gate(self):
        good = REPO_ROOT / "examples" / "good"
        for path in sorted(good.glob("*.md")):
            draft = difficulty.load_draft(path)
            errors = difficulty.horizon.horizon_errors(draft)
            assert errors == [], f"{path.name}: {errors}"

    def test_collection_scale_library_clone_has_no_horizon_error(self, tmp_path):
        draft = {
            "title": "Reimplement a Postgres wire protocol frontend",
            "collectionFamily": "Library clone",
            "objective": (
                "Rebuild a PostgreSQL wire-protocol frontend and query planner "
                "subset from the frozen spec in /app: simple query, extended "
                "parse/bind/execute, COPY, and notifications."
            ),
            "environmentSummary": (
                "Spec, catalog fixtures, and a compiling skeleton. The agent "
                "reimplements the protocol and planner, not one helper."
            ),
            "expertTimeEstimateHours": 80,
            "resourceEstimate": {"agentTimeoutSec": 18000},
            "difficultyExplanation": (
                "First attempt will treat the extended protocol as a thin wrapper "
                "over simple query. Hidden cases catch bind/execute mismatch, "
                "portal reuse, and COPY boundary traps."
            ),
            "anticipatedExploits": "Visible-only hard-code of the sample session.",
        }
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/test.sh": WEIGHTED_SH.format(visible=30, hidden=40, inv=30)},
        )
        findings = scan(bundle, draft)
        assert not any("collection floor" in e for e in findings.errors)
        assert not any("ticket-sized" in e for e in findings.errors)
        assert not any("collection-scale system" in e for e in findings.errors)
