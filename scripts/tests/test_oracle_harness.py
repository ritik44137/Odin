import importlib.util
import sys
from pathlib import Path

import pytest

from conftest import leaks, validator

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent
REFERENCE_BUNDLE = REPO_ROOT / "examples" / "reference-bundle"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


harness = _load("run_oracle_nop")


class TestScoreExtraction:
    def test_reads_the_score_marker(self):
        assert harness.extract_score("noise\nODYSSEY_SCORE=0.6250\ndone", 1) == pytest.approx(0.625)

    def test_last_marker_wins(self):
        assert harness.extract_score("ODYSSEY_SCORE=0.1\nODYSSEY_SCORE=0.9", 0) == pytest.approx(0.9)

    def test_falls_back_to_exit_status(self):
        assert harness.extract_score("no marker here", 0) == 1.0
        assert harness.extract_score("no marker here", 1) == 0.0

    def test_clamps_out_of_range_scores(self):
        assert harness.extract_score("ODYSSEY_SCORE=4.2", 0) == 1.0

    def test_integer_score_is_accepted(self):
        assert harness.extract_score("ODYSSEY_SCORE=1", 0) == 1.0


class TestOutputEmission:
    def test_stderr_starts_on_its_own_line(self, capsys):
        harness.emit("earned 0 of 100 weight\n", "failed groups: hidden\n")
        captured = capsys.readouterr()
        assert captured.out.endswith("\n")
        assert captured.out == "earned 0 of 100 weight\n"
        assert captured.err == "failed groups: hidden\n"

    def test_blank_streams_produce_nothing(self, capsys):
        harness.emit("", "   \n")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""


class TestDaemonDetection:
    """An unreachable daemon is an infra failure, not a verdict on the task."""

    def test_recognises_daemon_messages(self):
        assert harness.daemon_unreachable(
            "Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?"
        )
        assert harness.daemon_unreachable("permission denied while trying to connect to the Docker daemon socket")

    def test_does_not_flag_a_real_build_failure(self):
        assert not harness.daemon_unreachable(
            "ERROR: failed to solve: process /bin/sh -c pip install nope did not complete successfully"
        )

    def test_infra_exit_code_is_distinct_from_failure(self):
        assert harness.EXIT_INFRA == 3


class TestResourceFlags:
    def test_reads_limits_from_task_toml(self):
        flags = harness.resource_flags({"environment": {"cpus": 2, "memory_mb": 2048}})
        assert flags == ["--cpus", "2", "--memory", "2048m"]

    def test_absent_limits_produce_no_flags(self):
        assert harness.resource_flags({}) == []

    def test_nonsense_limits_are_ignored(self):
        assert harness.resource_flags({"environment": {"cpus": 0, "memory_mb": 4}}) == []

    def test_reference_bundle_limits_are_read(self):
        task_toml = harness.load_task_toml(REFERENCE_BUNDLE)
        assert harness.resource_flags(task_toml) == ["--cpus", "2", "--memory", "2048m"]

    def test_missing_task_toml_yields_empty_config(self, tmp_path):
        assert harness.load_task_toml(tmp_path) == {}


class TestReferenceBundle:
    """The exemplar must keep passing every local gate, or it stops being one."""

    def test_passes_structure_validation(self):
        draft = validator.load_draft(REFERENCE_BUNDLE / "draft.md")
        schema = validator.load_schema()
        draft_result = validator.validate_draft(draft, schema)
        assert draft_result.errors == [], draft_result.errors

        files, read = validator.read_bundle(REFERENCE_BUNDLE)
        assert read.errors == []
        bundle_result = validator.validate_bundle(files, draft)
        assert bundle_result.errors == [], bundle_result.errors

    def test_passes_leak_scan(self):
        files = leaks.read_bundle(REFERENCE_BUNDLE)
        findings = leaks.Findings()
        leaks.check_dockerfile(files, findings)
        leaks.check_ai_scaffolding(files, findings)
        leaks.check_duplicate_content(files, findings)
        leaks.check_instruction_leaks(files, findings)
        leaks.check_verifier_surface(files, findings)
        leaks.check_solution_surface(files, findings)
        assert findings.errors == [], findings.errors
        assert findings.warnings == [], findings.warnings

    def test_verifier_never_reaches_the_image(self):
        dockerfile = (REFERENCE_BUNDLE / "environment" / "Dockerfile").read_text(encoding="utf-8")
        copies = [
            line for line in dockerfile.splitlines()
            if line.strip().upper().startswith(("COPY", "ADD"))
        ]
        assert copies
        for line in copies:
            assert "tests" not in line, line
            assert "solution" not in line, line

    def test_weights_sum_to_one_hundred(self):
        text = (REFERENCE_BUNDLE / "tests" / "test.sh").read_text(encoding="utf-8")
        weights = [
            int(line.split()[2])
            for line in text.splitlines()
            if line.startswith("run_group ")
        ]
        assert weights == [30, 40, 30]
        assert sum(weights) == 100
