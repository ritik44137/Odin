"""Presence and difficulty-first content for Odin engines."""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RULES = REPO / ".cursor" / "rules"
ENGINES = RULES / "engines"
COMMANDS = REPO / ".cursor" / "commands"

REQUIRED_ENGINES = [
    "ENGINE_1_ideas.mdc",
    "ENGINE_2_novelty.mdc",
    "ENGINE_3_create.mdc",
    "ENGINE_4_audit.mdc",
    "ENGINE_5_verify.mdc",
    "ENGINE_6_package.mdc",
    "ENGINE_7_revise.mdc",
    "ENGINE_8_harden.mdc",
]

REQUIRED_COMMANDS = [
    "create-task.md",
    "revise-task.md",
    "harden-task.md",
    "audit-task.md",
    "verify-task.md",
    "package-task.md",
]


class TestEngineInventory:
    def test_router_exists_and_is_always_on(self):
        router = (RULES / "09-engine-router.mdc").read_text(encoding="utf-8")
        assert "alwaysApply: true" in router
        for n in range(1, 9):
            assert str(n) in router
        assert "difficulty" in router.lower()
        assert "ENGINE_8" in router or "8 harden" in router

    def test_engine_files_exist_and_are_on_demand(self):
        for name in REQUIRED_ENGINES:
            path = ENGINES / name
            assert path.is_file(), name
            text = path.read_text(encoding="utf-8")
            assert "alwaysApply: false" in text
            assert "Engine:" in text or "ENGINE_" in text

    def test_commands_exist_and_name_engines(self):
        for name in REQUIRED_COMMANDS:
            path = COMMANDS / name
            assert path.is_file(), name
            text = path.read_text(encoding="utf-8")
            assert "ENGINE_" in text

    def test_docs_map_exists(self):
        path = REPO / "docs" / "odyssey-engines.md"
        text = path.read_text(encoding="utf-8")
        assert "ENGINE_8" in text
        assert "Case 6" in text


class TestDifficultyFirst:
    def test_engine_1_refuses_without_trap(self):
        text = (ENGINES / "ENGINE_1_ideas.mdc").read_text(encoding="utf-8")
        assert "first-attempt" in text.lower() or "first attempt" in text.lower()
        assert "long-horizon" in text.lower() or "remaining work" in text.lower()
        assert "Ready for ENGINE_3: no" in text or "stop" in text.lower()
        assert "40" in text

    def test_engine_3_requires_hidden_majority(self):
        text = (ENGINES / "ENGINE_3_create.mdc").read_text(encoding="utf-8")
        assert "hidden" in text.lower()
        assert "check_difficulty_design.py" in text
        assert "ingest" in text.lower()  # forbid cloning that pipeline

    def test_engine_7_does_not_ease(self):
        text = (ENGINES / "ENGINE_7_revise.mdc").read_text(encoding="utf-8")
        assert "fairness" in text.lower()
        assert "ENGINE_8" in text
        assert "recipe" in text.lower()

    def test_engine_8_forbids_case_6_clone_and_decorative_pytest(self):
        text = (ENGINES / "ENGINE_8_harden.mdc").read_text(encoding="utf-8")
        assert "Case 6" in text
        assert "pytest" in text.lower()
        assert "ingest" in text.lower()
        assert "probe" in text.lower()
        assert "visible" in text.lower()

    def test_create_command_starts_with_engine_1(self):
        text = (COMMANDS / "create-task.md").read_text(encoding="utf-8")
        assert "ENGINE_1" in text
        idx1 = text.index("ENGINE_1")
        idx3 = text.index("ENGINE_3")
        assert idx1 < idx3

    def test_difficulty_design_doc_still_present(self):
        path = REPO / "docs" / "odyssey-difficulty-design.md"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        assert "visible-only" in lower
        assert "decoy-only" in lower
        assert "ENGINE_8" in text
        horizon = (REPO / "docs" / "odyssey-long-horizon.md").read_text(encoding="utf-8")
        assert "too short" in horizon.lower()
        assert "40" in horizon

    def test_heuristic_gate_wired_into_preflight_and_package(self):
        preflight = (REPO / "scripts" / "preflight.sh").read_text(encoding="utf-8")
        package = (REPO / "scripts" / "package_task.py").read_text(encoding="utf-8")
        assert "check_difficulty_design.py" in preflight
        assert "check_difficulty_design.py" in package
