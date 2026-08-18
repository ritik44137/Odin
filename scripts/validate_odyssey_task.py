#!/usr/bin/env python3
"""Local preflight validator for Odyssey drafts and task bundles.

Draft bounds and enums are read from schemas/odyssey-task-draft.schema.json so the
schema stays the single source of truth. Bundle checks mirror the deterministic
structure stage plus the draft/bundle consistency rules.
"""
import argparse
import functools
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_draft as draft_codec  # noqa: E402
import odyssey_paths as paths  # noqa: E402

try:
    import tomllib as _toml
except ModuleNotFoundError:
    try:
        import tomli as _toml  # type: ignore[no-redef]
    except ModuleNotFoundError:
        _toml = None  # type: ignore[assignment]

REPO_ROOT = paths.REPO_ROOT
SCHEMA_PATH = paths.SCHEMA_PATH
REQUIRED_BUNDLE_PATHS = paths.REQUIRED_BUNDLE_PATHS

# Trial sandbox ceilings, as published in the Odyssey authoring guide.
SANDBOX_CPUS = 8
SANDBOX_MEMORY_MB = 65536
SANDBOX_STORAGE_MB = 40960

# The 14h per-trial pool covers build + agent + verify + teardown, so agent and
# verifier timeouts alone must leave room for the phases we cannot measure here.
TRIAL_POOL_SEC = 50400
BUILD_TEARDOWN_RESERVE_SEC = 1800

MAX_BUNDLE_BYTES = 512 * 1024 * 1024

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Harbor NetworkMode enum (src/harbor/models/task/config.py). The Odyssey draft
# form still says none/allowlist; none maps to Harbor no-network, and public is
# Harbor's spelling of open egress.
HARBOR_NETWORK_MODES = frozenset({"no-network", "public", "allowlist"})
LEGACY_NETWORK_MODE_HINTS = {
    "none": "no-network",
    "open": "public",
    "enabled": "public",
    "disabled": "no-network",
}

PLACEHOLDER_MARKERS = {
    "instruction.md": [
        "replace this section",
        "hints the author may optionally provide",
    ],
    "tests/test.sh": [
        "implement the verifier steps",
        "replace the visible and hidden check bodies",
    ],
    "solution/solve.sh": [
        "implement the reference solution steps",
        "replace the steps below",
    ],
}


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def skip(self, message: str) -> None:
        """Record a check that could not run, so silence is never read as a pass."""
        self.skipped.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


class DraftSchema:
    """Bounds and enums derived from the JSON schema."""

    def __init__(self, schema: Dict):
        self.schema = schema
        props = schema.get("properties", {})
        self.properties = props
        self.required: List[str] = list(schema.get("required", []))
        self.allow_extra: bool = schema.get("additionalProperties", True) is not False
        self.known_keys = set(props)

    def string_bounds(self, name: str) -> Tuple[int, int]:
        prop = self.properties.get(name, {})
        return int(prop.get("minLength", 0)), int(prop.get("maxLength", 10**9))

    def enum(self, name: str) -> List[str]:
        return list(self.properties.get(name, {}).get("enum", []))

    def int_bounds(self, parent: str, name: str) -> Tuple[int, int]:
        prop = self.properties.get(parent, {}).get("properties", {}).get(name, {})
        return int(prop.get("minimum", -(10**9))), int(prop.get("maximum", 10**9))

    def nested_required(self, parent: str) -> List[str]:
        return list(self.properties.get(parent, {}).get("required", []))

    def string_fields(self) -> List[str]:
        return [
            name
            for name, prop in self.properties.items()
            if prop.get("type") == "string" and not prop.get("enum")
        ]


def timeout_seconds(value) -> Optional[int]:
    """Harbor types timeout_sec as float; TOML authors usually write an integer."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def check_harbor_network_mode(r: ValidationResult, section: str, raw) -> Optional[str]:
    """Return a Harbor NetworkMode value, or record why the field is invalid."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        r.error(f"task.toml [{section}].network_mode must be a string")
        return None
    if raw in HARBOR_NETWORK_MODES:
        return raw
    hint = LEGACY_NETWORK_MODE_HINTS.get(raw)
    if hint:
        r.error(
            f"task.toml [{section}].network_mode '{raw}' is not a Harbor NetworkMode; "
            f"use '{hint}' (allowed: no-network, public, allowlist)"
        )
        return None
    r.error(
        f"task.toml [{section}].network_mode must be one of: no-network, public, allowlist"
    )
    return None


@functools.lru_cache(maxsize=1)
def load_schema() -> DraftSchema:
    try:
        return DraftSchema(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    except FileNotFoundError:
        raise SystemExit(f"Draft schema not found at {SCHEMA_PATH}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Draft schema is not valid JSON: {exc}")


def load_draft(path: Path):
    try:
        return draft_codec.load(path)
    except FileNotFoundError:
        raise SystemExit(f"Draft file not found: {path}")
    except draft_codec.DraftError as exc:
        raise SystemExit(str(exc))


def check_int_range(result: ValidationResult, obj: Dict, key: str, lo: int, hi: int, prefix: str) -> None:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        result.error(f"{prefix}.{key} must be an integer")
        return
    if value < lo or value > hi:
        result.error(f"{prefix}.{key} must be between {lo} and {hi}")


def check_keyboard_ascii(result: ValidationResult, text: str, label: str) -> None:
    """Reject characters a standard keyboard cannot type.

    Odyssey form fields and instruction.md are pasted or shown as-is. Arrows,
    superscripts, em dashes, and similar glyphs fail this check.
    """
    for message in draft_codec.keyboard_ascii_violations(text, label):
        result.error(message)


def validate_draft(draft: Dict, schema: DraftSchema, source_text: Optional[str] = None) -> ValidationResult:
    r = ValidationResult()

    if not isinstance(draft, dict):
        r.error("draft must be an object")
        return r

    for name in schema.required:
        if name not in draft:
            r.error(f"draft.{name} is required but missing")

    unknown = sorted(set(draft) - schema.known_keys)
    for name in unknown:
        if schema.allow_extra:
            r.warn(f"draft.{name} is not a known draft field")
        else:
            r.error(f"draft.{name} is not a known draft field")
    if "notes" in draft:
        r.warn("draft.notes is a local convenience field with no Odyssey form counterpart; do not paste it into the form")

    for name in schema.string_fields():
        if name not in draft:
            continue
        value = draft.get(name)
        lo, hi = schema.string_bounds(name)
        if not isinstance(value, str):
            r.error(f"draft.{name} must be a string")
            continue
        if len(value) < lo or len(value) > hi:
            r.error(f"draft.{name} length must be between {lo} and {hi} (got {len(value)})")

    slug = draft.get("workingSlug")
    if isinstance(slug, str) and not SLUG_RE.fullmatch(slug):
        r.error("draft.workingSlug must be lowercase kebab-case")

    for name in ("collectionFamily", "taskFamily", "verifierFamily"):
        allowed = schema.enum(name)
        if name in draft and draft.get(name) not in allowed:
            r.error(f"draft.{name} must be one of: {', '.join(allowed)}")

    hours = draft.get("expertTimeEstimateHours")
    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or hours <= 0:
        r.error("draft.expertTimeEstimateHours must be a positive number")

    resource = draft.get("resourceEstimate")
    if not isinstance(resource, dict):
        r.error("draft.resourceEstimate must be an object")
        r.skip("resource bound checks (draft.resourceEstimate is not an object)")
    else:
        for key in schema.nested_required("resourceEstimate"):
            lo, hi = schema.int_bounds("resourceEstimate", key)
            check_int_range(r, resource, key, lo, hi, "draft.resourceEstimate")

        agent_timeout = resource.get("agentTimeoutSec")
        verifier_timeout = resource.get("verifierTimeoutSec")
        if isinstance(agent_timeout, int) and isinstance(verifier_timeout, int):
            total = agent_timeout + verifier_timeout
            if total > TRIAL_POOL_SEC:
                r.error(
                    f"draft agentTimeoutSec + verifierTimeoutSec is {total}s, above the {TRIAL_POOL_SEC}s per-trial pool"
                )
            elif total > TRIAL_POOL_SEC - BUILD_TEARDOWN_RESERVE_SEC:
                r.warn(
                    f"draft agentTimeoutSec + verifierTimeoutSec is {total}s, leaving under "
                    f"{TRIAL_POOL_SEC - total}s of the {TRIAL_POOL_SEC}s pool for image build and teardown"
                )

        # The form accepts figures well above what a trial provides, but a request
        # above the sandbox is rejected at intake rather than run starved, so these
        # are hard failures and not advisory.
        cpu_millis = resource.get("cpuMillis")
        if isinstance(cpu_millis, int) and cpu_millis > SANDBOX_CPUS * 1000:
            r.error(
                f"draft.resourceEstimate.cpuMillis ({cpu_millis}) exceeds the {SANDBOX_CPUS}-CPU trial sandbox "
                f"({SANDBOX_CPUS * 1000} milliCPU); a request above the sandbox is rejected at intake"
            )
        if isinstance(resource.get("memoryMb"), int) and resource["memoryMb"] > SANDBOX_MEMORY_MB:
            r.error(
                f"draft.resourceEstimate.memoryMb ({resource['memoryMb']}) exceeds the trial sandbox memory of "
                f"{SANDBOX_MEMORY_MB} MB; a request above the sandbox is rejected at intake"
            )
        if isinstance(resource.get("storageMb"), int) and resource["storageMb"] > SANDBOX_STORAGE_MB:
            r.error(
                f"draft.resourceEstimate.storageMb ({resource['storageMb']}) exceeds the trial sandbox storage of "
                f"{SANDBOX_STORAGE_MB} MB; a request above the sandbox is rejected at intake"
            )

    network = draft.get("networkRequirements")
    if not isinstance(network, dict):
        r.error("draft.networkRequirements must be an object")
        r.skip("network posture checks (draft.networkRequirements is not an object)")
    else:
        mode = network.get("mode")
        hosts = network.get("hosts")
        justification = network.get("justification")
        allowed_modes = schema.properties.get("networkRequirements", {}).get("properties", {}).get("mode", {}).get(
            "enum", ["none", "allowlist"]
        )
        if mode not in allowed_modes:
            r.error(f"draft.networkRequirements.mode must be one of: {', '.join(allowed_modes)}")
        if not isinstance(justification, str) or not justification.strip():
            r.error("draft.networkRequirements.justification must be a non-empty string")
        if not isinstance(hosts, list):
            r.error("draft.networkRequirements.hosts must be an array")
        else:
            if len(hosts) > 100:
                r.error("draft.networkRequirements.hosts may contain at most 100 entries")
            if mode == "none" and hosts:
                r.error("draft.networkRequirements.hosts must be empty when mode is none")
            if mode == "allowlist" and not hosts:
                r.error("draft.networkRequirements.hosts must contain at least one host when mode is allowlist")

        if mode == "allowlist":
            r.warn(
                "draft.networkRequirements.mode is allowlist; the rollout already runs deny-all plus the model "
                "endpoint the harness injects, so use allowlist only when the task itself must reach a host"
            )

    strategy = draft.get("verificationStrategy")
    if isinstance(strategy, str):
        lowered = strategy.lower()
        if "hidden" not in lowered:
            r.warn("draft.verificationStrategy does not explicitly mention hidden verification")
        if "visible" not in lowered:
            r.warn("draft.verificationStrategy does not explicitly mention visible verification")

    if source_text is not None:
        check_keyboard_ascii(r, source_text, "draft file")
    else:
        for path, text in draft_codec.iter_string_fields(draft, "draft"):
            check_keyboard_ascii(r, text, path)

    return r


def strip_bundle_root(files: Dict[str, bytes], result: ValidationResult) -> Dict[str, bytes]:
    """Accept both a flat bundle and one nested under a single top-level directory.

    The published layout shows `my-task/task.toml`, while some authors zip the
    contents directly, so both must validate identically.
    """
    if not files or any(req in files for req in REQUIRED_BUNDLE_PATHS):
        return files

    roots = {name.split("/", 1)[0] for name in files if "/" in name}
    unrooted = [name for name in files if "/" not in name]
    if len(roots) != 1 or unrooted:
        return files

    root = roots.pop()
    stripped = {name.split("/", 1)[1]: blob for name, blob in files.items()}
    if any(req in stripped for req in REQUIRED_BUNDLE_PATHS):
        result.warn(f"bundle contents are nested under '{root}/'; validating relative to that directory")
        return stripped
    return files


def read_bundle(bundle_path: Path) -> Tuple[Dict[str, bytes], ValidationResult]:
    r = ValidationResult()
    files: Dict[str, bytes] = {}

    if bundle_path.is_dir():
        for path in bundle_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(bundle_path).as_posix()
                files[rel] = path.read_bytes()
        r.warn("validating an unpacked directory; re-run against the real ZIP before upload")
        return strip_bundle_root(files, r), r

    if bundle_path.is_file() and bundle_path.suffix.lower() == ".zip":
        size = bundle_path.stat().st_size
        if size > MAX_BUNDLE_BYTES:
            r.error(f"bundle is {size / 1024 / 1024:.1f} MiB, above the 512 MiB compressed limit")
        try:
            with zipfile.ZipFile(bundle_path) as zf:
                seen = set()
                for info in zf.infolist():
                    name = info.filename.rstrip("/")
                    if not name:
                        continue
                    if name in seen:
                        r.error(f"bundle contains duplicate path: {name}")
                    seen.add(name)
                    parts = Path(name).parts
                    if name.startswith("/") or ".." in parts or Path(name).is_absolute():
                        r.error(f"bundle contains unsafe path: {name}")
                        continue
                    if not info.is_dir():
                        files[name] = zf.read(info)
        except zipfile.BadZipFile:
            r.error("bundle is not a valid ZIP archive")
        return strip_bundle_root(files, r), r

    r.error("bundle path must be a directory or a .zip file")
    return files, r


def parse_toml_bytes(blob: bytes) -> Dict:
    if _toml is None:
        raise RuntimeError("no TOML parser available (need Python 3.11+ or the 'tomli' package)")
    return _toml.loads(blob.decode("utf-8"))


def decode_text(blob: bytes) -> str:
    return blob.decode("utf-8", errors="ignore").strip()


def looks_like_placeholder(text: str, markers: List[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def check_script(r: ValidationResult, files: Dict[str, bytes], path: str, label: str) -> None:
    if path not in files:
        return
    content = decode_text(files[path])
    if len(content) < 40:
        r.error(f"{path} is present but not substantive")
    if looks_like_placeholder(content, PLACEHOLDER_MARKERS.get(path, [])):
        r.error(f"{path} still appears to contain template placeholder content")
    if not content.startswith("#!"):
        r.warn(f"{path} has no shebang; the harness runs this {label} directly")


def validate_bundle(files: Dict[str, bytes], draft: Optional[Dict]) -> ValidationResult:
    r = ValidationResult()

    for req in REQUIRED_BUNDLE_PATHS:
        if req not in files:
            r.error(f"bundle missing required path: {req}")

    if not any(name.startswith("tests/") for name in files):
        r.error("bundle has no files under tests/, so the task cannot be graded")
    if not any(name.startswith("solution/") for name in files):
        r.error("bundle has no files under solution/, so the oracle cannot be run")

    if "instruction.md" in files:
        raw = files["instruction.md"]
        try:
            instruction_text = raw.decode("utf-8")
        except UnicodeDecodeError:
            r.error("instruction.md is not valid UTF-8")
            instruction_text = None
        if instruction_text is not None:
            check_keyboard_ascii(r, instruction_text, "instruction.md")
        content = decode_text(raw)
        if len(content) < 40:
            r.error("instruction.md is present but not substantive")
        if looks_like_placeholder(content, PLACEHOLDER_MARKERS["instruction.md"]):
            r.error("instruction.md still appears to contain template placeholder content")
        lowered = content.lower()
        if "objective" not in lowered:
            r.warn("instruction.md does not explicitly label the objective")
        if "success" not in lowered:
            r.warn("instruction.md does not explicitly describe what success looks like")

    check_script(r, files, "tests/test.sh", "verifier")
    check_script(r, files, "solution/solve.sh", "reference solution")

    task_toml: Optional[Dict] = None
    if "task.toml" not in files:
        r.skip("all task.toml checks (metadata, sections, network posture, resources, timeouts) because task.toml is missing")
    else:
        try:
            task_toml = parse_toml_bytes(files["task.toml"])
        except RuntimeError as exc:
            r.error(str(exc))
            r.skip("all task.toml checks because no TOML parser is available")
        except Exception as exc:
            r.error(f"task.toml is not valid TOML: {exc}")
            r.skip("all task.toml checks because task.toml could not be parsed")

    if task_toml is None:
        return r

    validate_task_toml(r, task_toml, draft)
    return r


def validate_task_toml(r: ValidationResult, task_toml: Dict, draft: Optional[Dict]) -> None:
    schema = load_schema()
    metadata = task_toml.get("metadata", {}) or {}
    agent = task_toml.get("agent", {}) or {}
    verifier = task_toml.get("verifier", {}) or {}
    environment = task_toml.get("environment", {}) or {}

    for section in ("agent", "verifier", "environment"):
        if section not in task_toml:
            r.error(f"task.toml missing required section [{section}]")

    if not isinstance(metadata.get("name"), str) or not metadata.get("name", "").strip():
        r.error("task.toml [metadata].name must be non-empty")

    working_slug = metadata.get("working_slug")
    if working_slug is not None and (not isinstance(working_slug, str) or not SLUG_RE.fullmatch(working_slug)):
        r.error("task.toml [metadata].working_slug must be lowercase kebab-case when present")

    for toml_key, draft_key in (
        ("collection_family", "collectionFamily"),
        ("task_family", "taskFamily"),
        ("verifier_family", "verifierFamily"),
    ):
        value = metadata.get(toml_key)
        allowed = schema.enum(draft_key)
        if value is not None and value not in allowed:
            r.error(f"task.toml [metadata].{toml_key} must be one of: {', '.join(allowed)}")

    agent_mode = check_harbor_network_mode(r, "agent", agent.get("network_mode"))
    verifier_mode = check_harbor_network_mode(r, "verifier", verifier.get("network_mode"))
    env_mode = check_harbor_network_mode(r, "environment", environment.get("network_mode"))
    if agent_mode == "public":
        r.error("task.toml [agent].network_mode may not be public; open egress is refused at intake")
    # Only the rollout phase is governed by the network policy. Grading posture is
    # declared but not restricted, so public here is advisory rather than fatal.
    if verifier_mode == "public":
        r.warn("task.toml [verifier].network_mode is public; sealed grading is what keeps a verdict deterministic")
    if (
        env_mode is not None
        and agent_mode is not None
        and env_mode != agent_mode
    ):
        r.warn(
            "task.toml [agent].network_mode differs from [environment].network_mode; "
            "Harbor rejects a phase override unless the provider supports dynamic_network_policy"
        )

    if metadata.get("open_internet_justification") and agent_mode is None:
        r.error(
            "task.toml declares [metadata].open_internet_justification but leaves [agent].network_mode unset; "
            "rollout egress is read from that field alone"
        )

    agent_hosts = agent.get("allowed_hosts") or agent.get("allowlist_hosts") or agent.get("hosts")
    if agent_mode == "allowlist" and not agent_hosts:
        r.warn("task.toml [agent].network_mode is allowlist but no hosts are declared in the bundle")
    if agent_hosts and agent_mode != "allowlist":
        r.error("task.toml declares agent hosts but [agent].network_mode is not allowlist")

    if verifier.get("entrypoint") is not None:
        r.warn("task.toml [verifier].entrypoint is not a Harbor field; the grader runs tests/test.sh by name")
    if environment.get("dockerfile") is not None:
        r.warn("task.toml [environment].dockerfile is not a Harbor field; the image is built from environment/Dockerfile")

    agent_timeout = timeout_seconds(agent.get("timeout_sec"))
    verifier_timeout = timeout_seconds(verifier.get("timeout_sec"))
    if isinstance(agent_timeout, int):
        if agent_timeout < 7200:
            r.error("task.toml [agent].timeout_sec must be at least 7200 to meet the long-horizon floor")
        if agent_timeout > 86400:
            r.error("task.toml [agent].timeout_sec exceeds the 86400s cap")
    if isinstance(verifier_timeout, int) and verifier_timeout > 86400:
        r.error("task.toml [verifier].timeout_sec exceeds the 86400s cap")
    if isinstance(agent_timeout, int) and isinstance(verifier_timeout, int):
        total = agent_timeout + verifier_timeout
        if total > TRIAL_POOL_SEC:
            r.error(f"task.toml agent and verifier timeouts total {total}s, above the {TRIAL_POOL_SEC}s per-trial pool")
        elif total > TRIAL_POOL_SEC - BUILD_TEARDOWN_RESERVE_SEC:
            r.warn(
                f"task.toml agent and verifier timeouts total {total}s, leaving under "
                f"{TRIAL_POOL_SEC - total}s of the pool for image build and teardown"
            )

    if isinstance(environment.get("cpus"), (int, float)) and environment["cpus"] > SANDBOX_CPUS:
        r.error(f"task.toml [environment].cpus exceeds the sandbox ceiling of {SANDBOX_CPUS}")
    if isinstance(environment.get("memory_mb"), int) and environment["memory_mb"] > SANDBOX_MEMORY_MB:
        r.error(f"task.toml [environment].memory_mb exceeds the sandbox ceiling of {SANDBOX_MEMORY_MB}")
    if isinstance(environment.get("storage_mb"), int) and environment["storage_mb"] > SANDBOX_STORAGE_MB:
        r.error(f"task.toml [environment].storage_mb exceeds the sandbox ceiling of {SANDBOX_STORAGE_MB}")

    if draft is None:
        r.skip("draft/bundle consistency checks (network posture, resources, timeouts) because no --draft was given")
        return

    validate_consistency(r, metadata, agent, verifier, environment, draft, agent_mode, agent_hosts,
                         agent_timeout, verifier_timeout)


def validate_consistency(
    r: ValidationResult,
    metadata: Dict,
    agent: Dict,
    verifier: Dict,
    environment: Dict,
    draft: Dict,
    agent_mode: Optional[str],
    agent_hosts,
    agent_timeout,
    verifier_timeout,
) -> None:
    draft_slug = draft.get("workingSlug")
    toml_slug = metadata.get("working_slug")
    if isinstance(draft_slug, str) and isinstance(toml_slug, str) and draft_slug != toml_slug:
        r.warn(f"task.toml working_slug '{toml_slug}' does not match draft workingSlug '{draft_slug}'")

    for toml_key, draft_key in (
        ("collection_family", "collectionFamily"),
        ("task_family", "taskFamily"),
        ("verifier_family", "verifierFamily"),
    ):
        toml_value = metadata.get(toml_key)
        draft_value = draft.get(draft_key)
        if toml_value is not None and draft_value is not None and toml_value != draft_value:
            r.error(f"task.toml [metadata].{toml_key} ('{toml_value}') disagrees with draft {draft_key} ('{draft_value}')")

    network = draft.get("networkRequirements")
    if not isinstance(network, dict):
        r.skip("network consistency checks because draft.networkRequirements is missing or malformed")
    else:
        draft_mode = network.get("mode")
        if draft_mode == "none" and agent_mode not in (None, "no-network"):
            r.error("draft requests no network, but bundle [agent].network_mode is not no-network")
        if draft_mode == "allowlist" and agent_mode != "allowlist":
            r.error(
                "draft requests allowlist network, but bundle [agent].network_mode is not allowlist; "
                "the rollout would run sealed and fail for a reason that is not the task's difficulty"
            )
        draft_hosts = network.get("hosts")
        if isinstance(draft_hosts, list) and isinstance(agent_hosts, list):
            extra = sorted(set(agent_hosts) - set(draft_hosts))
            if extra:
                r.error(f"task.toml declares hosts absent from the draft allowlist: {', '.join(extra)}")

    resource = draft.get("resourceEstimate")
    if not isinstance(resource, dict):
        r.skip("resource consistency checks because draft.resourceEstimate is missing or malformed")
        return

    cpus = environment.get("cpus")
    cpu_millis = resource.get("cpuMillis")
    if isinstance(cpus, (int, float)) and isinstance(cpu_millis, int) and cpus * 1000 > cpu_millis:
        r.error(
            f"task.toml [environment].cpus ({cpus}) requests {int(cpus * 1000)} milliCPU, "
            f"above the draft cpuMillis allowance of {cpu_millis}"
        )

    for toml_key, draft_key in (
        ("memory_mb", "memoryMb"),
        ("storage_mb", "storageMb"),
        ("gpus", "gpuCount"),
    ):
        env_value = environment.get(toml_key)
        draft_value = resource.get(draft_key)
        if isinstance(env_value, int) and isinstance(draft_value, int) and env_value > draft_value:
            r.error(
                f"task.toml [environment].{toml_key} ({env_value}) exceeds the draft {draft_key} allowance ({draft_value})"
            )

    if isinstance(agent_timeout, int) and isinstance(resource.get("agentTimeoutSec"), int):
        if agent_timeout > resource["agentTimeoutSec"]:
            r.error("task.toml [agent].timeout_sec exceeds the draft agentTimeoutSec allowance")
    if isinstance(verifier_timeout, int) and isinstance(resource.get("verifierTimeoutSec"), int):
        if verifier_timeout > resource["verifierTimeoutSec"]:
            r.error("task.toml [verifier].timeout_sec exceeds the draft verifierTimeoutSec allowance")


def print_result(name: str, result: ValidationResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {name}")
    for msg in result.errors:
        print(f"  ERROR:   {msg}")
    for msg in result.warnings:
        print(f"  WARN:    {msg}")
    for msg in result.skipped:
        print(f"  SKIPPED: {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Odyssey draft Markdown and bundle structure")
    parser.add_argument("--slug", help="Resolve drafts/<slug>.md and tasks/<slug>/ automatically")
    parser.add_argument("--draft", type=Path, help="Path to Odyssey draft Markdown")
    parser.add_argument("--bundle", type=Path, help="Path to bundle directory or ZIP")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    if args.slug:
        try:
            slug = paths.check_slug(args.slug)
        except paths.SlugError as exc:
            parser.error(str(exc))
        # An explicit path always wins, so --slug can be narrowed when needed.
        if not args.draft and paths.draft_path(slug).is_file():
            args.draft = paths.draft_path(slug)
        if not args.bundle:
            if paths.zip_path(slug).is_file() and not paths.task_dir(slug).is_dir():
                args.bundle = paths.zip_path(slug)
            elif paths.task_dir(slug).is_dir():
                args.bundle = paths.task_dir(slug)
        if not args.draft and not args.bundle:
            parser.error(f"no draft or task directory found for slug '{slug}'")

    if not args.draft and not args.bundle:
        parser.error("provide --slug, or at least one of --draft and --bundle")

    schema = load_schema()
    results: List[ValidationResult] = []
    draft = None

    if args.draft:
        draft = load_draft(args.draft)
        source_text = args.draft.read_text(encoding="utf-8")
        # Markdown is checked as the paste artifact. JSON is checked via parsed
        # strings so escaped unicode in the file still fails once decoded.
        source_for_scan = None if args.draft.suffix.lower() == ".json" else source_text
        draft_result = validate_draft(draft, schema, source_text=source_for_scan)
        print_result("draft", draft_result)
        results.append(draft_result)

    if args.bundle:
        bundle_files, read_result = read_bundle(args.bundle)
        print_result("bundle read", read_result)
        results.append(read_result)
        if read_result.ok:
            bundle_result = validate_bundle(bundle_files, draft)
            print_result("bundle contents", bundle_result)
            results.append(bundle_result)
        if not args.draft:
            print("  NOTE:    pass --draft to also check draft/bundle consistency")

    ok = all(r.ok for r in results)
    if args.strict and any(r.warnings for r in results):
        print("[FAIL] strict mode: warnings present")
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
