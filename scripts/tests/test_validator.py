import copy
import zipfile
from pathlib import Path

import pytest

from conftest import validator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOOD_DRAFT = REPO_ROOT / "examples" / "good" / "example-good-odyssey-draft.md"

TASK_TOML = """
[metadata]
name = "Strict TOML nested inline tables"
working_slug = "strict-toml-nested-inline-tables"
collection_family = "Library clone"
task_family = "feature_development"
verifier_family = "programmatic"

[agent]
network_mode = "no-network"
timeout_sec = 7200

[verifier]
network_mode = "no-network"
timeout_sec = 1800

[environment]
cpus = 4
memory_mb = 4096
storage_mb = 2048
gpus = 0
network_mode = "no-network"
"""

INSTRUCTION = """# Task

## Objective

Add strict parsing for nested inline tables to the parser in /app, rejecting
duplicate keys across nested scopes while preserving the existing public API.

## What success looks like

The parser accepts every valid nested inline table and raises a precise error on
each malformed one.
"""

TEST_SH = """#!/usr/bin/env bash
set -uo pipefail
cd /app
python -m pytest -q "$(dirname "$0")/visible"
echo "ODYSSEY_SCORE=1.0"
"""

SOLVE_SH = """#!/usr/bin/env bash
set -euo pipefail
cd /app
python - <<'PY'
print("apply reference implementation")
PY
"""


@pytest.fixture
def draft():
    return validator.load_draft(GOOD_DRAFT)


@pytest.fixture
def schema():
    return validator.load_schema()


def make_bundle(root: Path, task_toml: str = TASK_TOML, extra: dict | None = None) -> Path:
    (root / "environment").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "hidden").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "visible").mkdir(parents=True, exist_ok=True)
    (root / "solution").mkdir(parents=True, exist_ok=True)
    (root / "task.toml").write_text(task_toml, encoding="utf-8")
    (root / "instruction.md").write_text(INSTRUCTION, encoding="utf-8")
    (root / "environment" / "Dockerfile").write_text("FROM python:3.11-slim\nWORKDIR /app\n", encoding="utf-8")
    (root / "tests" / "test.sh").write_text(TEST_SH, encoding="utf-8")
    (root / "tests" / "visible" / "test_public.py").write_text("def test_public():\n    assert True\n", encoding="utf-8")
    (root / "tests" / "hidden" / "test_held_out.py").write_text("def test_hidden():\n    assert True\n", encoding="utf-8")
    (root / "solution" / "solve.sh").write_text(SOLVE_SH, encoding="utf-8")
    for rel, content in (extra or {}).items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def zip_bundle(bundle_dir: Path, zip_path: Path, prefix: str = "") -> Path:
    with zipfile.ZipFile(zip_path, "w") as zf:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(bundle_dir).as_posix()
                zf.write(path, f"{prefix}{rel}" if prefix else rel)
    return zip_path


class TestDraft:
    def test_good_example_passes(self, draft, schema):
        result = validator.validate_draft(draft, schema)
        assert result.errors == []

    def test_all_good_examples_pass(self, schema):
        for path in sorted((REPO_ROOT / "examples" / "good").glob("*.md")):
            data = validator.load_draft(path)
            source = path.read_text(encoding="utf-8")
            result = validator.validate_draft(data, schema, source_text=source)
            assert result.errors == [], f"{path.name}: {result.errors}"

    def test_keyboard_only_rejects_arrows_and_superscripts(self, draft, schema):
        draft["oracleStrategy"] = "diffs base\u2192ours with O(n\u00b2) work"
        result = validator.validate_draft(draft, schema)
        joined = " ".join(result.errors)
        assert "U+2192" in joined
        assert "U+00B2" in joined

    def test_keyboard_only_rejects_em_dash_in_source(self, draft, schema):
        source = "# Odyssey task draft\n\n## Title\n\nHello \u2014 world\n"
        result = validator.validate_draft(draft, schema, source_text=source)
        assert any("U+2014" in e for e in result.errors)

    def test_unknown_field_rejected(self, draft, schema):
        draft["objectives"] = "typo of objective"
        result = validator.validate_draft(draft, schema)
        assert any("not a known draft field" in e for e in result.errors)

    def test_missing_required_field_reported(self, draft, schema):
        del draft["objective"]
        result = validator.validate_draft(draft, schema)
        assert any("draft.objective is required" in e for e in result.errors)

    def test_bounds_come_from_schema(self, draft, schema):
        draft["title"] = "ab"
        result = validator.validate_draft(draft, schema)
        assert any("draft.title length must be between 3" in e for e in result.errors)

    def test_slug_must_be_kebab(self, draft, schema):
        draft["workingSlug"] = "Not_Kebab"
        result = validator.validate_draft(draft, schema)
        assert any("kebab-case" in e for e in result.errors)

    def test_cpu_millis_above_sandbox_is_rejected(self, draft, schema):
        """The form accepts up to 64000, but above the sandbox it is rejected at intake."""
        draft["resourceEstimate"]["cpuMillis"] = 16000
        result = validator.validate_draft(draft, schema)
        assert any("8-CPU trial sandbox" in e for e in result.errors)

    def test_memory_above_sandbox_is_rejected(self, draft, schema):
        draft["resourceEstimate"]["memoryMb"] = 131072
        result = validator.validate_draft(draft, schema)
        assert any("trial sandbox memory" in e for e in result.errors)

    def test_storage_above_sandbox_is_rejected(self, draft, schema):
        draft["resourceEstimate"]["storageMb"] = 65536
        result = validator.validate_draft(draft, schema)
        assert any("trial sandbox storage" in e for e in result.errors)

    def test_sandbox_maxima_are_accepted(self, draft, schema):
        draft["resourceEstimate"].update({"cpuMillis": 8000, "memoryMb": 65536, "storageMb": 40960})
        result = validator.validate_draft(draft, schema)
        assert result.errors == []

    def test_allowlist_mode_warns_about_harness_egress(self, draft, schema):
        draft["networkRequirements"] = {
            "mode": "allowlist",
            "justification": "the task must reach a pinned package index at rollout",
            "hosts": ["pypi.org"],
        }
        result = validator.validate_draft(draft, schema)
        assert result.errors == []
        assert any("deny-all plus the model endpoint" in w for w in result.warnings)

    def test_trial_pool_ceiling_is_an_error(self, draft, schema):
        draft["resourceEstimate"]["agentTimeoutSec"] = 50000
        draft["resourceEstimate"]["verifierTimeoutSec"] = 1000
        result = validator.validate_draft(draft, schema)
        assert any("per-trial pool" in e for e in result.errors)

    def test_build_reserve_warns_before_the_ceiling(self, draft, schema):
        draft["resourceEstimate"]["agentTimeoutSec"] = 49000
        draft["resourceEstimate"]["verifierTimeoutSec"] = 1000
        result = validator.validate_draft(draft, schema)
        assert result.errors == []
        assert any("image build and teardown" in w for w in result.warnings)

    def test_allowlist_requires_hosts(self, draft, schema):
        draft["networkRequirements"] = {
            "mode": "allowlist",
            "justification": "needs a package index at rollout",
            "hosts": [],
        }
        result = validator.validate_draft(draft, schema)
        assert any("at least one host" in e for e in result.errors)

    def test_notes_field_warns(self, draft, schema):
        draft["notes"] = "local scratch"
        result = validator.validate_draft(draft, schema)
        assert result.errors == []
        assert any("no Odyssey form counterpart" in w for w in result.warnings)


class TestBundleReading:
    def test_flat_directory(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        files, read = validator.read_bundle(bundle)
        assert read.errors == []
        assert "task.toml" in files

    def test_nested_zip_is_accepted(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        archive = zip_bundle(bundle, tmp_path / "nested.zip", prefix="my-task/")
        files, read = validator.read_bundle(archive)
        assert read.errors == []
        assert "task.toml" in files
        assert any("nested under 'my-task/'" in w for w in read.warnings)

    def test_flat_zip_is_accepted(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        archive = zip_bundle(bundle, tmp_path / "flat.zip")
        files, read = validator.read_bundle(archive)
        assert read.errors == []
        assert "environment/Dockerfile" in files

    def test_unsafe_path_rejected(self, tmp_path):
        archive = tmp_path / "unsafe.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("../escape.txt", "nope")
            zf.writestr("task.toml", TASK_TOML)
        _, read = validator.read_bundle(archive)
        assert any("unsafe path" in e for e in read.errors)

    def test_duplicate_path_rejected(self, tmp_path):
        archive = tmp_path / "dupe.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("instruction.md", INSTRUCTION)
            zf.writestr("instruction.md", INSTRUCTION)
        _, read = validator.read_bundle(archive)
        assert any("duplicate path" in e for e in read.errors)


class TestBundleContents:
    def test_valid_bundle_passes(self, tmp_path, draft):
        bundle = make_bundle(tmp_path / "bundle")
        files, read = validator.read_bundle(bundle)
        assert read.errors == []
        result = validator.validate_bundle(files, draft)
        assert result.errors == [], result.errors

    def test_instruction_rejects_non_keyboard_characters(self, tmp_path, draft):
        bundle = make_bundle(
            tmp_path / "bundle",
            extra={"instruction.md": INSTRUCTION + "\nFollow base\u2192ours.\n"},
        )
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("instruction.md" in e and "U+2192" in e for e in result.errors)

    def test_toml_parses_without_python311(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert not any("TOML parser" in e for e in result.errors)

    def test_missing_task_toml_reports_skipped_checks(self, tmp_path, draft):
        bundle = make_bundle(tmp_path / "bundle")
        (bundle / "task.toml").unlink()
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("missing required path: task.toml" in e for e in result.errors)
        assert any("task.toml checks" in s for s in result.skipped)

    def test_malformed_toml_reports_skipped_checks(self, tmp_path, draft):
        bundle = make_bundle(tmp_path / "bundle", task_toml="[metadata\nname = ")
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("not valid TOML" in e for e in result.errors)
        assert any("could not be parsed" in s for s in result.skipped)

    def test_no_draft_reports_skipped_consistency(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert any("consistency" in s for s in result.skipped)

    def test_placeholder_templates_are_rejected(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        templates = REPO_ROOT / "templates"
        (bundle / "instruction.md").write_bytes((templates / "odyssey-instruction.template.md").read_bytes())
        (bundle / "tests" / "test.sh").write_bytes((templates / "odyssey-test.template.sh").read_bytes())
        (bundle / "solution" / "solve.sh").write_bytes((templates / "odyssey-solve.template.sh").read_bytes())
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        for path in ("instruction.md", "tests/test.sh", "solution/solve.sh"):
            assert any(path in e and "placeholder" in e for e in result.errors), path

    def test_open_rollout_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace('[agent]\nnetwork_mode = "no-network"', '[agent]\nnetwork_mode = "public"')
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("may not be public" in e for e in result.errors)

    def test_legacy_none_network_mode_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace('[agent]\nnetwork_mode = "no-network"', '[agent]\nnetwork_mode = "none"')
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("not a Harbor NetworkMode" in e and "no-network" in e for e in result.errors)

    def test_legacy_enabled_environment_network_mode_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace(
            'gpus = 0\nnetwork_mode = "no-network"',
            'gpus = 0\nnetwork_mode = "enabled"',
        )
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("[environment].network_mode 'enabled'" in e for e in result.errors)

    def test_open_internet_justification_needs_explicit_agent_mode(self, tmp_path):
        toml = TASK_TOML.replace(
            'verifier_family = "programmatic"',
            'verifier_family = "programmatic"\nopen_internet_justification = "needs a package index"',
        ).replace('[agent]\nnetwork_mode = "no-network"\n', "[agent]\n")
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert any("open_internet_justification" in e for e in result.errors)

    def test_cpus_above_draft_cpu_millis_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace("cpus = 4", "cpus = 6")
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("milliCPU" in e for e in result.errors)

    def test_cpus_within_draft_allowance_passes(self, tmp_path, draft):
        assert draft["resourceEstimate"]["cpuMillis"] == 4000
        bundle = make_bundle(tmp_path / "bundle")
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert not any("milliCPU" in e for e in result.errors)

    def test_memory_above_draft_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace("memory_mb = 4096", "memory_mb = 8192")
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("memory_mb" in e and "exceeds the draft" in e for e in result.errors)

    def test_sandbox_ceiling_rejected(self, tmp_path):
        toml = TASK_TOML.replace("cpus = 4", "cpus = 16")
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert any("sandbox ceiling of 8" in e for e in result.errors)

    def test_network_mismatch_rejected(self, tmp_path, draft):
        draft = copy.deepcopy(draft)
        draft["networkRequirements"] = {
            "mode": "allowlist",
            "justification": "the task must reach a pinned package index",
            "hosts": ["pypi.org"],
        }
        bundle = make_bundle(tmp_path / "bundle")
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("not allowlist" in e for e in result.errors)

    def test_bundle_hosts_must_be_a_subset_of_the_draft(self, tmp_path, draft):
        draft = copy.deepcopy(draft)
        draft["networkRequirements"] = {
            "mode": "allowlist",
            "justification": "the task must reach a pinned package index",
            "hosts": ["pypi.org"],
        }
        toml = TASK_TOML.replace(
            '[agent]\nnetwork_mode = "no-network"',
            '[agent]\nnetwork_mode = "allowlist"\nallowed_hosts = ["pypi.org", "github.com"]',
        )
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("absent from the draft allowlist" in e and "github.com" in e for e in result.errors)

    def test_family_disagreement_rejected(self, tmp_path, draft):
        toml = TASK_TOML.replace('collection_family = "Library clone"', 'collection_family = "Product clone"')
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, draft)
        assert any("collection_family" in e and "disagrees" in e for e in result.errors)

    def test_verifier_public_network_is_advisory_not_fatal(self, tmp_path):
        """Only the rollout phase is governed by the network policy."""
        toml = TASK_TOML.replace(
            '[verifier]\nnetwork_mode = "no-network"',
            '[verifier]\nnetwork_mode = "public"',
        )
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert not any("verifier" in e.lower() for e in result.errors)
        assert any("[verifier].network_mode is public" in w for w in result.warnings)

    def test_short_agent_timeout_rejected(self, tmp_path):
        toml = TASK_TOML.replace("timeout_sec = 7200", "timeout_sec = 3600")
        bundle = make_bundle(tmp_path / "bundle", task_toml=toml)
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert any("at least 7200" in e for e in result.errors)

    def test_empty_tests_directory_rejected(self, tmp_path):
        bundle = make_bundle(tmp_path / "bundle")
        for path in (bundle / "tests").rglob("*"):
            if path.is_file():
                path.unlink()
        files, _ = validator.read_bundle(bundle)
        result = validator.validate_bundle(files, None)
        assert any("no files under tests/" in e for e in result.errors)
