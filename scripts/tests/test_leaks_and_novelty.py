import json
from pathlib import Path

import pytest

from conftest import leaks, novelty, validator
from test_validator import INSTRUCTION, SOLVE_SH, TEST_SH, make_bundle

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def scan(bundle: Path):
    files = leaks.read_bundle(bundle)
    findings = leaks.Findings()
    leaks.check_dockerfile(files, findings)
    leaks.check_ai_scaffolding(files, findings)
    leaks.check_duplicate_content(files, findings)
    leaks.check_instruction_leaks(files, findings)
    leaks.check_verifier_surface(files, findings)
    leaks.check_solution_surface(files, findings)
    leaks.check_stale_artifacts(files, findings)
    return findings


class TestLeakScanner:
    def test_clean_bundle_passes(self, tmp_path):
        findings = scan(make_bundle(tmp_path / "bundle"))
        assert findings.errors == [], findings.errors

    def test_dockerfile_copying_tests_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim\nWORKDIR /app\nCOPY tests/ /app/tests/\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("copies 'tests/'" in e for e in findings.errors)

    def test_dockerfile_copying_solution_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim\nWORKDIR /app\nCOPY ./solution /app/ref\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("solution/ is agent-readable" in e for e in findings.errors)

    def test_context_escape_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim\nCOPY ../tests /app/t\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("outside the build context" in e for e in findings.errors)

    def test_broad_copy_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim\nWORKDIR /app\nCOPY . /app\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert findings.errors == []
        assert any("wholesale" in w for w in findings.warnings)

    def test_identical_held_out_file_is_an_error(self, tmp_path):
        payload = "EXPECTED = " + json.dumps({"cases": list(range(40))}) + "\n"
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={
                "tests/hidden/expected.py": payload,
                "environment/app/expected.py": payload,
            },
        )
        findings = scan(bundle)
        assert any("byte-identical" in e for e in findings.errors)

    def test_grading_against_app_fixture_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tests" / "test.sh").write_text(
            TEST_SH + 'diff /app/expected_output.txt /tmp/actual.txt\n', encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("inside /app" in w for w in findings.warnings)

    def test_missing_hidden_split_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tests" / "hidden" / "test_held_out.py").unlink()
        findings = scan(bundle)
        assert any("held out" in w for w in findings.warnings)

    def test_solution_reading_verifier_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "solution" / "solve.sh").write_text(
            SOLVE_SH + 'cat tests/hidden/test_held_out.py\n', encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("references the verifier" in e for e in findings.errors)

    def test_networked_solution_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "solution" / "solve.sh").write_text(
            SOLVE_SH + 'curl -sSL https://example.com/patch.diff -o /tmp/p.diff\n', encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("fetch from the network" in w for w in findings.warnings)

    def test_compiled_bytecode_warns(self, tmp_path):
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"tests/hidden/__pycache__/test_held_out.cpython-311.pyc": "\x00stale"},
        )
        findings = scan(bundle)
        assert findings.errors == []
        assert any("compiled Python artifacts" in w for w in findings.warnings)

    def test_dockerfile_template_does_not_trip_reserved_paths(self):
        text = (REPO_ROOT / "templates" / "odyssey-dockerfile.template").read_text(encoding="utf-8")
        findings = leaks.Findings()
        leaks.check_dockerfile({"environment/Dockerfile": text.encode("utf-8")}, findings)
        assert findings.errors == [], findings.errors

    def test_dockerfile_reserved_path_is_an_error(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim\nWORKDIR /app\nRUN mkdir -p /tests\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("Harbor reserved path" in e for e in findings.errors)

    def test_ai_scaffolding_in_environment_is_an_error(self, tmp_path):
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"environment/app/CLAUDE.md": "# helper\n" + ("x" * 80)},
        )
        findings = scan(bundle)
        assert any("AI scaffolding" in e for e in findings.errors)

    def test_runtime_fetch_in_test_sh_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tests" / "test.sh").write_text(
            TEST_SH + "curl -sSL https://example.com/cases.json -o /tmp/c.json\n", encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("fetch or install" in w for w in findings.warnings)

    def test_oracle_split_in_test_sh_warns(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "tests" / "test.sh").write_text(
            TEST_SH + 'if [ -n "${EVAL_IS_ORACLE:-}" ]; then chmod 777 /app; fi\n', encoding="utf-8"
        )
        findings = scan(bundle)
        assert any("identical tests" in w for w in findings.warnings)

    def test_zip_with_nested_root_is_read(self, tmp_path):
        import zipfile

        bundle = make_bundle(tmp_path / "bundle")
        archive = tmp_path / "b.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    zf.write(path, f"my-task/{path.relative_to(bundle).as_posix()}")
        files = leaks.read_bundle(archive)
        assert "task.toml" in files


class TestNovelty:
    def _score(self, a: dict, b: dict) -> float:
        fa = novelty.features(novelty.draft_text(a))
        fb = novelty.features(novelty.draft_text(b))
        idf = {term: 1.0 for term in set(fa) | set(fb)}
        return novelty.cosine(fa, fb, idf)

    @pytest.fixture
    def drafts(self):
        return [
            validator.load_draft(path)
            for path in sorted((REPO_ROOT / "examples" / "good").glob("*.md"))
        ]

    def test_identical_drafts_score_one(self, drafts):
        assert self._score(drafts[0], drafts[0]) == pytest.approx(1.0)

    def test_distinct_families_score_low(self, drafts):
        scores = [
            self._score(a, b)
            for i, a in enumerate(drafts)
            for b in drafts[i + 1:]
        ]
        assert scores
        assert max(scores) < 0.55, f"example drafts are more similar than expected: {max(scores):.3f}"

    def test_reworded_duplicate_still_scores_high(self, drafts):
        original = drafts[0]
        reskin = json.loads(json.dumps(original))
        reskin["title"] = "A completely different sounding title"
        reskin["workingSlug"] = "renamed-task"
        assert self._score(original, reskin) > 0.9
