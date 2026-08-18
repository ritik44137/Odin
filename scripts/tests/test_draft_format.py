from pathlib import Path

import pytest

from conftest import validator

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent


def _load(name: str):
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


odyssey_draft = _load("odyssey_draft")

TEMPLATE = REPO_ROOT / "templates" / "odyssey-task-draft.template.md"
TASK_DRAFT = REPO_ROOT / "drafts" / "three-way-merge-engine.md"


class TestMarkdownDraftCodec:
    def test_round_trip_preserves_fields(self):
        original = {
            "title": "Example title here",
            "workingSlug": "example-title-here",
            "collectionFamily": "Library clone",
            "taskFamily": "feature_development",
            "verifierFamily": "programmatic",
            "objective": "x" * 40,
            "motivation": "y" * 20,
            "difficultyExplanation": "z" * 40,
            "expertTimeEstimateHours": 6,
            "environmentSummary": "e" * 40,
            "resourceEstimate": {
                "cpuMillis": 4000,
                "memoryMb": 4096,
                "storageMb": 2048,
                "gpuCount": 0,
                "agentTimeoutSec": 7200,
                "verifierTimeoutSec": 1800,
            },
            "networkRequirements": {
                "mode": "none",
                "justification": "Fully offline.",
                "hosts": [],
            },
            "oracleStrategy": "o" * 20,
            "verificationStrategy": "v" * 40,
            "binarySuccessCondition": "b" * 20,
            "partialScoreStrategy": "p" * 20,
            "anticipatedExploits": "a" * 20,
            "notes": "local only",
        }
        text = odyssey_draft.render_markdown(original)
        parsed = odyssey_draft.parse_markdown(text)
        assert parsed == original

    def test_unknown_heading_is_an_error(self):
        with pytest.raises(odyssey_draft.DraftError, match="unknown draft heading"):
            odyssey_draft.parse_markdown("## Not a real field\n\nbody\n")

    def test_allowlist_hosts_split(self):
        text = odyssey_draft.render_markdown({
            "title": "Hosted",
            "networkRequirements": {
                "mode": "allowlist",
                "justification": "Need a registry.",
                "hosts": ["pypi.org", "files.pythonhosted.org"],
            },
        })
        parsed = odyssey_draft.parse_markdown(text)
        assert parsed["networkRequirements"]["hosts"] == ["pypi.org", "files.pythonhosted.org"]

    def test_template_parses(self):
        draft = odyssey_draft.parse_markdown(TEMPLATE.read_text(encoding="utf-8"))
        assert draft["collectionFamily"] == "Library clone"
        assert draft["resourceEstimate"]["agentTimeoutSec"] == 7200
        assert draft["networkRequirements"]["mode"] == "none"

    def test_three_way_merge_draft_validates(self):
        if not TASK_DRAFT.is_file():
            pytest.skip("task draft not present in this checkout")
        draft = odyssey_draft.load(TASK_DRAFT)
        source = TASK_DRAFT.read_text(encoding="utf-8")
        result = validator.validate_draft(draft, validator.load_schema(), source_text=source)
        assert result.errors == [], result.errors

    def test_platform_draft_files_are_keyboard_ascii(self):
        paths = [TEMPLATE, *sorted((REPO_ROOT / "examples" / "good").glob("*.md"))]
        if TASK_DRAFT.is_file():
            paths.append(TASK_DRAFT)
        paths.append(REPO_ROOT / "examples" / "reference-bundle" / "draft.md")
        for path in paths:
            text = path.read_text(encoding="utf-8")
            hits = odyssey_draft.keyboard_ascii_violations(text, str(path))
            assert hits == [], hits

    def test_notes_heading_is_keyboard_ascii(self):
        heading = odyssey_draft.HEADING_BY_FIELD["notes"]
        assert odyssey_draft.keyboard_ascii_violations(heading, "notes heading") == []
        parsed = odyssey_draft.parse_markdown("## Notes (local only -- do not paste)\n\nscratch\n")
        assert parsed["notes"] == "scratch"
