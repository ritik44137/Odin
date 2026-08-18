import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


paths = _load("odyssey_paths")
packager = _load("package_task")


class TestSlugContract:
    @pytest.mark.parametrize("slug", ["abc", "parse-toml-strict", "a1-b2-c3", "x" * 80])
    def test_accepts_valid_slugs(self, slug):
        assert paths.check_slug(slug) == slug

    @pytest.mark.parametrize(
        "slug",
        [
            "ab",              # too short
            "x" * 81,          # too long
            "Not-Kebab",       # uppercase
            "under_score",     # underscore
            "double--hyphen",  # consecutive hyphens
            "-leading",
            "trailing-",
            "has space",
            "dots.in.it",
        ],
    )
    def test_rejects_invalid_slugs(self, slug):
        with pytest.raises(paths.SlugError):
            paths.check_slug(slug)

    def test_one_slug_resolves_all_four_locations(self):
        slug = "example-task"
        assert paths.draft_path(slug) == REPO_ROOT / "drafts" / "example-task.md"
        assert paths.plan_path(slug) == REPO_ROOT / "plans" / "example-task.md"
        assert paths.task_dir(slug) == REPO_ROOT / "tasks" / "example-task"
        assert paths.zip_path(slug) == REPO_ROOT / "zip" / "example-task.zip"

    def test_an_invalid_slug_cannot_produce_a_path(self):
        with pytest.raises(paths.SlugError):
            paths.task_dir("../escape")

    def test_ledger_lives_outside_the_task_directories(self):
        for directory in (paths.DRAFTS_DIR, paths.TASKS_DIR, paths.ZIP_DIR, paths.PLANS_DIR):
            assert directory not in paths.LEDGER_PATH.parents
        assert paths.LEDGER_PATH.parent == REPO_ROOT

    def test_required_paths_match_the_documented_five(self):
        assert paths.REQUIRED_BUNDLE_PATHS == [
            "task.toml",
            "instruction.md",
            "environment/Dockerfile",
            "tests/test.sh",
            "solution/solve.sh",
        ]


class TestArchiveBuilding:
    @pytest.fixture
    def task(self, tmp_path):
        root = tmp_path / "tasks" / "demo-task"
        (root / "environment").mkdir(parents=True)
        (root / "tests" / "hidden").mkdir(parents=True)
        (root / "tests" / "visible").mkdir(parents=True)
        (root / "solution").mkdir(parents=True)
        (root / "task.toml").write_text("[metadata]\nname = 'demo'\n", encoding="utf-8")
        (root / "instruction.md").write_text("# Task\n", encoding="utf-8")
        (root / "environment" / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
        (root / "tests" / "test.sh").write_text("#!/usr/bin/env bash\necho hi\n", encoding="utf-8")
        (root / "tests" / "test.sh").chmod(0o755)
        (root / "solution" / "solve.sh").write_text("#!/usr/bin/env bash\necho fix\n", encoding="utf-8")
        (root / "solution" / "solve.sh").chmod(0o755)
        (root / "tests" / "visible" / ".gitkeep").write_text("", encoding="utf-8")
        (root / "tests" / "hidden" / "test_held.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "junk.pyc").write_bytes(b"\x00")
        (root / "tests" / "stray.pyc").write_bytes(b"\x00")
        return root

    def test_executable_bit_survives(self, task, tmp_path):
        target = tmp_path / "out.zip"
        packager.write_zip(task, target)
        with zipfile.ZipFile(target) as zf:
            modes = {i.filename: (i.external_attr >> 16) & 0o777 for i in zf.infolist()}
        assert modes["tests/test.sh"] == 0o755
        assert modes["solution/solve.sh"] == 0o755
        assert modes["task.toml"] == 0o644

    def test_droppings_are_excluded(self, task, tmp_path):
        target = tmp_path / "out.zip"
        packager.write_zip(task, target)
        with zipfile.ZipFile(target) as zf:
            names = set(zf.namelist())
        assert not any("__pycache__" in n for n in names)
        assert not any(n.endswith(".pyc") for n in names)
        assert not any(n.endswith(".gitkeep") for n in names)
        assert "tests/hidden/test_held.py" in names

    def test_all_required_paths_are_at_the_root(self, task, tmp_path):
        target = tmp_path / "out.zip"
        packager.write_zip(task, target)
        with zipfile.ZipFile(target) as zf:
            names = set(zf.namelist())
        for required in paths.REQUIRED_BUNDLE_PATHS:
            assert required in names

    def test_nested_root_wraps_every_entry(self, task, tmp_path):
        target = tmp_path / "nested.zip"
        packager.write_zip(task, target, nested_root="demo-task")
        with zipfile.ZipFile(target) as zf:
            names = zf.namelist()
        assert names
        assert all(n.startswith("demo-task/") for n in names)

    def test_rewriting_replaces_rather_than_appends(self, task, tmp_path):
        target = tmp_path / "out.zip"
        packager.write_zip(task, target)
        first = zipfile.ZipFile(target).namelist()
        packager.write_zip(task, target)
        assert zipfile.ZipFile(target).namelist() == first


class TestScaffoldAndRefusal:
    """new_task.py must produce something the gates reject until it is filled in."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "new_task.py"), *args],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )

    def test_rejects_a_bad_slug(self):
        result = self._run("--slug", "Bad_Slug")
        assert result.returncode != 0
        assert "invalid slug" in result.stderr

    def test_scaffold_is_rejected_by_the_validator(self, tmp_path, monkeypatch):
        slug = "scaffold-selftest-task"
        monkeypatch.setattr(paths, "DRAFTS_DIR", tmp_path / "drafts")
        monkeypatch.setattr(paths, "PLANS_DIR", tmp_path / "plans")
        monkeypatch.setattr(paths, "TASKS_DIR", tmp_path / "tasks")

        # Reproduce what new_task.py writes, without touching the real repo.
        validator = _load("validate_odyssey_task")
        template = validator.load_draft(paths.TEMPLATES_DIR / "odyssey-task-draft.template.md")
        template["workingSlug"] = slug
        template["title"] = "Scaffold selftest"

        result = validator.validate_draft(template, validator.load_schema())
        assert result.errors, "an empty scaffold draft must not validate"
        assert any("objective" in e for e in result.errors)
