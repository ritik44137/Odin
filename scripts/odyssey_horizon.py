"""Collection-scale long-horizon heuristics for Odyssey drafts.

The Odyssey form still treats expertTimeEstimateHours as unconstrained
metadata and 7200s as the agent-timeout floor. The automated difficulty
stage separately rejects ticket-sized work as "too short for the
collection -- not long-horizon". These constants calibrate local gates to
that collection bar (SWE-Marathon-scale Harbor tasks), not to Terminal-Bench 2.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# SWE-Marathon published expert-human envelope starts at 40 hours.
COLLECTION_EXPERT_HOURS_MIN = 40

# Harbor stock init is ~100x too small. SWE-Marathon template is 5 hours.
COLLECTION_AGENT_TIMEOUT_TARGET_SEC = 18000
COLLECTION_AGENT_TIMEOUT_WARN_BELOW_SEC = 14400  # 4h; 7200 is the platform floor

PLUMBING_MARKERS = (
    "plumbing exemplar",
    "deliberately too easy",
    "deliberately small exemplar",
    "not a submittable task",
    "not submittable",
)

# Ticket / TB2 shapes that the difficulty judge has already called short.
SHORT_HORIZON_RES = (
    re.compile(r"(?i)\bexisting (parser|library|module|helper|codebase)\b"),
    re.compile(r"(?i)\bnested inline"),
    re.compile(r"(?i)\b(web )?application slice\b"),
    re.compile(r"(?i)\brepair (an |the )?existing\b"),
    re.compile(r"(?i)\b(add|implement) support for\b"),
    re.compile(r"(?i)\breduce peak memory\b"),
    re.compile(r"(?i)\bfocused (library|module|parser|helper|codebase)\b"),
    re.compile(r"(?i)\bsmall (parser|library|module|helper)\b"),
    re.compile(r"(?i)\bpage-range parsing\b"),
    re.compile(r"(?i)\bsingle (function|method|class|module|file)\b"),
    re.compile(r"(?i)\bone[- ]file\b"),
    re.compile(r"(?i)\bticket[- ]sized\b"),
    re.compile(r"(?i)\bimplement the go module\b"),
    re.compile(r"(?i)\bfrozen public api\b"),
    re.compile(r"(?i)\boffline-capable\b"),
    re.compile(r"(?i)\boffline invoice\b"),
)

# Remaining work must look like a complete system in the declared family.
# One match is required in title+objective+environmentSummary.
SYSTEM_SCALE_RES: Dict[str, Tuple[re.Pattern[str], ...]] = {
    "Library clone": (
        re.compile(r"(?i)\b(reimplement|rebuild|clone|port)\b"),
        re.compile(r"(?i)\bfrom rfc\b"),
        re.compile(r"(?i)\brfc\s+\d+\b"),
        re.compile(r"(?i)\bmulti-pass\b"),
        re.compile(r"(?i)\b(compiler|interpreter|language server|\blsp\b)\b"),
        re.compile(r"(?i)\b(decoder|encoder|codec)\b"),
        re.compile(r"(?i)\b(control[-\s]?plane|query planner|storage engine|wire[-\s]?protocol)\b"),
        re.compile(r"(?i)\b(runtime|virtual machine|\bvm\b|wasm)\b"),
    ),
    "Product clone": (
        re.compile(r"(?i)\bclone\b"),
        re.compile(r"(?i)\bfull[-\s]?stack\b"),
        re.compile(r"(?i)\bcompatible (api|service|sdk)\b"),
        re.compile(r"(?i)\b(realtime|real-time) api\b"),
        re.compile(r"(?i)\b(oauth|webhooks?|lifecycle|versioning)\b"),
        re.compile(r"(?i)\b(console|browser) ui\b"),
    ),
    "ML engineering": (
        re.compile(r"(?i)\bpost[-\s]?train"),
        re.compile(r"(?i)\btrain .{8,120}(checkpoint|parameter|latency|budget|cap)\b"),
        re.compile(r"(?i)\b(eval harness|evaluation harness)\b"),
        re.compile(r"(?i)\bport .{8,80}(pytorch|jax|tensorflow|triton)\b"),
        re.compile(r"(?i)\b(triton kernel|custom kernel)\b"),
        re.compile(r"(?i)\b\d+\s+datasets?\b"),
    ),
    "Algorithmic optimization": (
        re.compile(r"(?i)\bcustom (isa|vliw|instruction set)\b"),
        re.compile(r"(?i)\b(cycle|conflict|latency) target\b"),
        re.compile(r"(?i)\b(cdcl|sat solver|network alignment)\b"),
        re.compile(r"(?i)\bwithout (breaking|changing) (correctness|semantics|proof)\b"),
        re.compile(r"(?i)\bproof logging\b"),
    ),
}

FRONTIER_ONLY_RES = (
    re.compile(r"(?i)\bfrontier (coding )?models?\b"),
    re.compile(r"(?i)\bagents? (one-shot|fail|cannot)\b"),
    re.compile(r"(?i)\bmodels? (will )?(fail|struggle|not one-shot)\b"),
)


def is_plumbing(texts: Iterable[str]) -> bool:
    blob = " ".join(texts).lower()
    return any(marker in blob for marker in PLUMBING_MARKERS)


def short_horizon_hits(text: str) -> List[str]:
    hits = []
    for cre in SHORT_HORIZON_RES:
        m = cre.search(text)
        if m:
            hits.append(m.group(0))
    return hits


def has_system_scale_signal(family: str, text: str) -> bool:
    patterns = SYSTEM_SCALE_RES.get(family) or ()
    if not patterns:
        # Unknown family: demand at least one clone/rebuild/port/rfc signal.
        patterns = SYSTEM_SCALE_RES["Library clone"]
    return any(cre.search(text) for cre in patterns)


def frontier_only_explanation(explanation: str) -> bool:
    if not explanation.strip():
        return False
    lowered = explanation.lower()
    has_frontier = any(cre.search(explanation) for cre in FRONTIER_ONLY_RES)
    has_surface = any(
        word in lowered
        for word in (
            "subsystem", "compiler", "protocol", "clone", "rfc",
            "control plane", "training", "kernel", "parity", "passes",
        )
    )
    return has_frontier and not has_surface


def horizon_errors(
    draft: Optional[Dict],
    extra_texts: Sequence[str] = (),
) -> List[str]:
    """Return blocking horizon failures for a real (non-plumbing) draft."""
    if not draft:
        return []
    texts = [
        str(draft.get("title") or ""),
        str(draft.get("objective") or ""),
        str(draft.get("motivation") or ""),
        str(draft.get("difficultyExplanation") or ""),
        str(draft.get("environmentSummary") or ""),
        str(draft.get("notes") or ""),
        *extra_texts,
    ]
    if is_plumbing(texts):
        return []

    errors: List[str] = []
    hours = draft.get("expertTimeEstimateHours")
    if isinstance(hours, (int, float)) and not isinstance(hours, bool):
        if hours < COLLECTION_EXPERT_HOURS_MIN:
            errors.append(
                f"expertTimeEstimateHours is {hours}; the collection floor is "
                f"{COLLECTION_EXPERT_HOURS_MIN} honest expert hours of remaining "
                "work. Ticket-sized Harbor tasks fail Automated Difficulty as "
                "too short / not long-horizon. Padding the number without "
                "expanding the system does not pass. See docs/odyssey-long-horizon.md"
            )

    scope = "\n".join(
        (
            str(draft.get("title") or ""),
            str(draft.get("objective") or ""),
            str(draft.get("environmentSummary") or ""),
        )
    )
    short = short_horizon_hits(scope)
    if short:
        errors.append(
            "title/objective reads as ticket-sized work "
            f"({', '.join(short[:4])}); the difficulty probe rejects focused "
            "features, repairs, and single-module libraries as too short for "
            "this collection. Remaining work must be a complete system clone "
            "or reproduction. See docs/odyssey-long-horizon.md"
        )

    family = str(draft.get("collectionFamily") or "")
    if family and not has_system_scale_signal(family, scope):
        errors.append(
            f"{family} remaining work does not name a collection-scale system "
            "(clone, rebuild, port, RFC, compiler/decoder/LSP, full-stack product, "
            "training-under-cap, or custom-ISA kernel). A focused module with "
            "interacting bugs is still too short. See docs/odyssey-long-horizon.md"
        )

    explanation = str(draft.get("difficultyExplanation") or "")
    if frontier_only_explanation(explanation):
        errors.append(
            "difficultyExplanation argues from frontier-model failure without "
            "naming the remaining-work surface. Model trials do not make a "
            "ticket long-horizon. Name the subsystems the oracle still has to "
            "build. See docs/odyssey-long-horizon.md"
        )
    return errors


def horizon_warnings(draft: Optional[Dict]) -> List[str]:
    if not draft or is_plumbing(
        [
            str(draft.get("motivation") or ""),
            str(draft.get("difficultyExplanation") or ""),
            str(draft.get("notes") or ""),
        ]
    ):
        return []
    warnings: List[str] = []
    resource = draft.get("resourceEstimate") or {}
    timeout = resource.get("agentTimeoutSec") if isinstance(resource, dict) else None
    if isinstance(timeout, int) and timeout < COLLECTION_AGENT_TIMEOUT_WARN_BELOW_SEC:
        warnings.append(
            f"agentTimeoutSec is {timeout}s (platform floor 7200s). Collection-scale "
            f"Harbor tasks budget 4-10 hours; template default is "
            f"{COLLECTION_AGENT_TIMEOUT_TARGET_SEC}s. A 2h clock on a 40h clone "
            "starves the trial; a 2h clock on a ticket does not lengthen it"
        )
    return warnings
