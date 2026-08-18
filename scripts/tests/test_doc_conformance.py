"""Every constraint stated in the Odyssey authoring guide, asserted against the repo.

The guide is the source of truth for this repository. These tests transcribe its
numbers, enums, and required paths directly from the prose so that a future edit to
the schema, the validator, or the templates cannot silently drift away from it.

Each constant below is quoted from the guide in its comment. If the guide changes,
change these first and let the failures show you what else has to move.
"""
import json
from pathlib import Path

import pytest

from conftest import validator

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent

# "title 3–200 chars", "workingSlug 3–80", "objective 40–20,000 chars", and so on.
FIELD_BOUNDS = {
    "title": (3, 200),
    "workingSlug": (3, 80),
    "objective": (40, 20000),
    "motivation": (20, 10000),
    "difficultyExplanation": (40, 20000),
    "environmentSummary": (40, 20000),
    "oracleStrategy": (20, 20000),
    "verificationStrategy": (40, 20000),
    "binarySuccessCondition": (20, 10000),
    "partialScoreStrategy": (20, 10000),
    "anticipatedExploits": (20, 20000),
}

# "cpuMillis (100–64,000), memoryMb (128–262,144), storageMb (128–1,048,576),
#  gpuCount (0–8), agentTimeoutSec and verifierTimeoutSec (each capped at 86,400)"
RESOURCE_BOUNDS = {
    "cpuMillis": (100, 64000),
    "memoryMb": (128, 262144),
    "storageMb": (128, 1048576),
    "gpuCount": (0, 8),
    "agentTimeoutSec": (7200, 86400),
    "verifierTimeoutSec": (1, 86400),
}

# "Library clone ... Product clone ... ML engineering ... Algorithmic optimization"
COLLECTION_FAMILIES = ["Library clone", "Product clone", "ML engineering", "Algorithmic optimization"]

# "feature_development, debugging, refactoring, performance, systems_integration, or other"
TASK_FAMILIES = ["feature_development", "debugging", "refactoring", "performance", "systems_integration", "other"]

# "programmatic (tests / scripts), optimization (a metric to push), ml_artifact ..., or custom"
VERIFIER_FAMILIES = ["programmatic", "optimization", "ml_artifact", "custom"]

# "task.toml ... instruction.md ... environment/Dockerfile ... tests/test.sh ... solution/solve.sh"
REQUIRED_PATHS = ["task.toml", "instruction.md", "environment/Dockerfile", "tests/test.sh", "solution/solve.sh"]


@pytest.fixture(scope="module")
def schema():
    return json.loads((REPO_ROOT / "schemas" / "odyssey-task-draft.schema.json").read_text(encoding="utf-8"))


class TestDraftFieldBounds:
    @pytest.mark.parametrize("field,bounds", sorted(FIELD_BOUNDS.items()))
    def test_schema_matches_the_guide(self, schema, field, bounds):
        prop = schema["properties"][field]
        assert (prop["minLength"], prop["maxLength"]) == bounds

    @pytest.mark.parametrize("field,bounds", sorted(FIELD_BOUNDS.items()))
    def test_validator_reads_the_same_bounds(self, field, bounds):
        assert validator.load_schema().string_bounds(field) == bounds

    def test_slug_pattern_allows_only_lowercase_kebab(self, schema):
        # "lowercase letters, digits, and single hyphens (a-z0-9, e.g. parse-toml-strict)"
        assert schema["properties"]["workingSlug"]["pattern"] == "^[a-z0-9]+(?:-[a-z0-9]+)*$"

    def test_expert_time_estimate_is_any_positive_number(self, schema):
        # "any positive estimate (metadata)" — descriptive, and explicitly not a gate
        prop = schema["properties"]["expertTimeEstimateHours"]
        assert prop["type"] == "number"
        assert prop["exclusiveMinimum"] == 0
        assert "maximum" not in prop

    def test_every_guide_field_is_required(self, schema):
        expected = set(FIELD_BOUNDS) | {
            "collectionFamily", "taskFamily", "verifierFamily",
            "expertTimeEstimateHours", "resourceEstimate", "networkRequirements",
        }
        assert expected <= set(schema["required"])

    def test_no_extra_fields_are_accepted(self, schema):
        # The form collects a fixed set; a typo must not pass silently.
        assert schema["additionalProperties"] is False


class TestEnums:
    def test_collection_families(self, schema):
        assert schema["properties"]["collectionFamily"]["enum"] == COLLECTION_FAMILIES

    def test_task_families(self, schema):
        assert schema["properties"]["taskFamily"]["enum"] == TASK_FAMILIES

    def test_verifier_families(self, schema):
        assert schema["properties"]["verifierFamily"]["enum"] == VERIFIER_FAMILIES

    def test_network_modes_exclude_open(self, schema):
        # "none (default — fully offline) or allowlist"; open egress "is rejected at intake"
        assert schema["properties"]["networkRequirements"]["properties"]["mode"]["enum"] == ["none", "allowlist"]

    def test_host_limit(self, schema):
        # "requires at least one host, up to 100"
        assert schema["properties"]["networkRequirements"]["properties"]["hosts"]["maxItems"] == 100


class TestResourceBounds:
    @pytest.mark.parametrize("field,bounds", sorted(RESOURCE_BOUNDS.items()))
    def test_schema_matches_the_guide(self, schema, field, bounds):
        prop = schema["properties"]["resourceEstimate"]["properties"][field]
        assert (prop["minimum"], prop["maximum"]) == bounds

    def test_long_horizon_floor(self, schema):
        # "the effective agentTimeoutSec must be at least 2h (7,200s)"
        assert schema["properties"]["resourceEstimate"]["properties"]["agentTimeoutSec"]["minimum"] == 7200

    def test_trial_pool_ceiling(self):
        # "the whole trial — build + agent + verify + teardown — must fit the 50,400s (14h) pool"
        assert validator.TRIAL_POOL_SEC == 50400
        assert validator.BUILD_TEARDOWN_RESERVE_SEC > 0, "the pool must reserve room for build and teardown"

    def test_sandbox_ceilings(self):
        # "The trial sandbox provides 8 CPUs, 65536 MB of memory and 40960 MB of storage"
        assert validator.SANDBOX_CPUS == 8
        assert validator.SANDBOX_MEMORY_MB == 65536
        assert validator.SANDBOX_STORAGE_MB == 40960

    def test_bundle_size_limit(self):
        # "a single application/zip archive (up to 512 MiB compressed)"
        assert validator.MAX_BUNDLE_BYTES == 512 * 1024 * 1024


class TestBundleContract:
    def test_required_paths_are_exact(self):
        # "The required set is exact"
        assert validator.REQUIRED_BUNDLE_PATHS == REQUIRED_PATHS

    def test_templates_exist_for_every_required_path(self):
        templates = REPO_ROOT / "templates"
        for name in (
            "odyssey-task-toml.template.toml",
            "odyssey-instruction.template.md",
            "odyssey-test.template.sh",
            "odyssey-solve.template.sh",
            "odyssey-task-draft.template.md",
            "odyssey-bundle-plan.template.md",
        ):
            assert (templates / name).is_file(), name

    def test_task_toml_template_declares_all_four_sections(self):
        # "a [metadata] table ... plus [verifier], [agent], and [environment] sections"
        text = (REPO_ROOT / "templates" / "odyssey-task-toml.template.toml").read_text(encoding="utf-8")
        for section in ("[metadata]", "[agent]", "[verifier]", "[environment]"):
            assert section in text, section

    def test_task_toml_template_is_within_the_sandbox(self):
        template = REPO_ROOT / "templates" / "odyssey-task-toml.template.toml"
        parsed = validator.parse_toml_bytes(template.read_bytes())
        env = parsed["environment"]
        assert env["cpus"] <= validator.SANDBOX_CPUS
        assert env["memory_mb"] <= validator.SANDBOX_MEMORY_MB
        assert env["storage_mb"] <= validator.SANDBOX_STORAGE_MB
        assert parsed["agent"]["timeout_sec"] >= 7200
        assert parsed["agent"]["timeout_sec"] + parsed["verifier"]["timeout_sec"] <= validator.TRIAL_POOL_SEC

    def test_task_toml_template_seals_the_rollout(self):
        parsed = validator.parse_toml_bytes(
            (REPO_ROOT / "templates" / "odyssey-task-toml.template.toml").read_bytes()
        )
        assert parsed["agent"]["network_mode"] == "no-network"
        assert parsed["verifier"]["network_mode"] == "no-network"
        assert parsed["environment"]["network_mode"] == "no-network"

    def test_draft_template_is_within_the_sandbox(self):
        draft = validator.load_draft(REPO_ROOT / "templates" / "odyssey-task-draft.template.md")
        resource = draft["resourceEstimate"]
        assert resource["cpuMillis"] <= validator.SANDBOX_CPUS * 1000
        assert resource["memoryMb"] <= validator.SANDBOX_MEMORY_MB
        assert resource["storageMb"] <= validator.SANDBOX_STORAGE_MB
        assert resource["agentTimeoutSec"] >= 7200
        assert draft["networkRequirements"]["mode"] == "none"

    def test_draft_template_default_families_are_valid(self):
        draft = validator.load_draft(REPO_ROOT / "templates" / "odyssey-task-draft.template.md")
        assert draft["collectionFamily"] in COLLECTION_FAMILIES
        assert draft["taskFamily"] in TASK_FAMILIES
        assert draft["verifierFamily"] in VERIFIER_FAMILIES


class TestExampleDraftsConform:
    @pytest.mark.parametrize(
        "path",
        sorted({*(REPO_ROOT / "examples").rglob("*draft*.md"), *(REPO_ROOT / "examples").glob("*/draft.md")}),
        ids=lambda p: str(p.relative_to(REPO_ROOT)),
    )
    def test_example_draft_validates(self, path):
        draft = validator.load_draft(path)
        result = validator.validate_draft(draft, validator.load_schema())
        assert result.errors == [], f"{path}: {result.errors}"

    def test_one_example_exists_per_collection_family(self):
        families = set()
        for path in (REPO_ROOT / "examples" / "good").glob("*.md"):
            families.add(validator.load_draft(path)["collectionFamily"])
        assert families == set(COLLECTION_FAMILIES)
