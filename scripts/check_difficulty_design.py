#!/usr/bin/env python3
"""Heuristic difficulty-design scan.

The Odyssey difficulty probe has no local substitute. This script does not
certify hardness. It fails shapes that almost always saturate a frontier
agent, ticket-sized work the collection already rejects as not long-horizon,
and it warns about missing levers (decoys, hidden majority, traps in
the draft). Collection bar: docs/odyssey-long-horizon.md.

  python3 scripts/check_difficulty_design.py --slug <slug>
  python3 scripts/check_difficulty_design.py --draft drafts/x.md --bundle tasks/x
  python3 scripts/check_difficulty_design.py examples/reference-bundle
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_draft as draft_codec  # noqa: E402
import odyssey_horizon as horizon  # noqa: E402
import odyssey_paths as paths  # noqa: E402

RUN_GROUP_RE = re.compile(
    r"""run_group\s+["']([^"']+)["']\s+(\d+)""",
    re.IGNORECASE,
)
TEST_DEF_RE = re.compile(r"^\s*def\s+(test_\w+)", re.MULTILINE)
CODE_EXTS = {".py", ".go", ".rs", ".c", ".cc", ".cpp", ".h", ".ts", ".js", ".java", ".rb", ".sh"}
SKIP_DIR = {"vendor", "node_modules", "target", "dist", "build", "__pycache__", ".git"}
HIDDEN_HINTS = ("hidden", "held_out", "heldout", "private", "sealed")
DECOY_HINTS = ("decoy", "legacy", "unused", "distractor", "ignore_me", "sidecar")
RECIPE_RES = (
    re.compile(r"(?i)\bstep\s+\d+\s*[:.]"),
    re.compile(r"(?i)\bfirst\s+(patch|fix|edit)\b"),
    re.compile(r"(?i)\bfix the following files\b"),
    re.compile(r"(?i)\bthe bugs?\s+(are|is)\s+in\b"),
    re.compile(r"\bBUG:"),
    re.compile(r"\btest_fix_"),
    re.compile(r"(?i)\bthen\s+patch\b"),
    re.compile(r"(?i)\bimplement(?:ation)? plan\b"),
)
INTERVIEW_RES = (
    re.compile(r"(?i)\blru\s+cache\b"),
    re.compile(r"(?i)\breverse\s+a\s+string\b"),
    re.compile(r"(?i)\bfizzbuzz\b"),
    re.compile(r"(?i)\btwo[-\s]?sum\b"),
    re.compile(r"(?i)\bhello\s+world\b"),
    re.compile(r"(?i)\bfibonacci\b"),
    re.compile(r"(?i)\btodo\s+(list|app)\b"),
    re.compile(r"(?i)\bimplement\s+an?\s+palindrome\b"),
    re.compile(r"(?i)\bbinary\s+search\s+tree\b"),
)
TRAP_WORDS = (
    "trap", "wrong", "invariant", "hidden", "decoy", "almost",
    "first attempt", "naive", "plausible", "overfit", "visible-only",
)
SCALE_ONLY = ("hours", "large", "many files", "complex", "lots of")
PROPERTY_HINTS = (
    "hypothesis", "given(", "generated", "for _ in range", "random.seed",
    "parametrize", "fuzz", "property",
)


@dataclass
class Findings:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def decode(blob: bytes) -> str:
    return blob.decode("utf-8", errors="ignore")


def read_tree(root: Path) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    for item in root.rglob("*"):
        if item.is_file():
            files[item.relative_to(root).as_posix()] = item.read_bytes()
    return files


def is_code(name: str) -> bool:
    return Path(name).suffix.lower() in CODE_EXTS


def env_modules(files: Dict[str, bytes]) -> List[str]:
    out = []
    for name in files:
        if not name.startswith("environment/"):
            continue
        parts = Path(name).parts
        if any(p in SKIP_DIR for p in parts):
            continue
        if is_code(name):
            out.append(name)
    return out


def test_functions(files: Dict[str, bytes], prefix: str) -> List[str]:
    names: List[str] = []
    for name, blob in files.items():
        if not name.startswith(prefix) or not name.endswith(".py"):
            continue
        names.extend(TEST_DEF_RE.findall(decode(blob)))
    return names


def group_weights(test_sh: str) -> List[Tuple[str, int]]:
    return [(m.group(1), int(m.group(2))) for m in RUN_GROUP_RE.finditer(test_sh)]


def visible_weight_ratio(groups: List[Tuple[str, int]]) -> Optional[float]:
    if not groups:
        return None
    total = sum(w for _, w in groups)
    if total <= 0:
        return None
    visible = sum(w for name, w in groups if "visible" in name.lower() or "public" in name.lower())
    return visible / total


def recipe_hits(text: str) -> List[str]:
    hits = []
    for cre in RECIPE_RES:
        if cre.search(text):
            hits.append(cre.pattern)
    return hits


def interview_hits(text: str) -> List[str]:
    hits = []
    for cre in INTERVIEW_RES:
        m = cre.search(text)
        if m:
            hits.append(m.group(0))
    return hits


def has_property_channel(files: Dict[str, bytes]) -> bool:
    hidden = "\n".join(
        decode(blob)
        for name, blob in files.items()
        if name.startswith("tests/") and any(h in name.lower() for h in HIDDEN_HINTS)
    )
    lowered = hidden.lower()
    return any(hint in lowered for hint in PROPERTY_HINTS)


def decoy_paths(files: Dict[str, bytes]) -> List[str]:
    found = []
    for name in files:
        if not name.startswith("environment/"):
            continue
        lowered = name.lower()
        if any(h in lowered for h in DECOY_HINTS):
            found.append(name)
    return found


def check_instruction(instruction: str, f: Findings) -> None:
    hits = recipe_hits(instruction)
    if hits:
        f.errors.append(
            "instruction.md reads like a fix recipe (numbered steps, BUG: labels, "
            "or named patch order); that saturates the difficulty probe. Keep a "
            "scenario in the instruction and contracts in /app"
        )
    interview = interview_hits(instruction)
    if interview:
        f.errors.append(
            "instruction.md matches a textbook/interview exercise "
            f"({', '.join(interview)}); the probe will treat it as recall"
        )
    lines = [ln for ln in instruction.splitlines() if ln.strip()]
    if len(lines) > 80:
        f.warnings.append(
            f"instruction.md is {len(lines)} non-empty lines; long prompts often "
            "become checklists. Move algorithms into /app docs"
        )


def check_grader(files: Dict[str, bytes], f: Findings) -> None:
    test_sh = files.get("tests/test.sh")
    if test_sh is None:
        f.errors.append("tests/test.sh is missing, so grader weights cannot be checked")
        return
    text = decode(test_sh)
    groups = group_weights(text)
    ratio = visible_weight_ratio(groups)
    if not groups:
        f.warnings.append(
            "tests/test.sh has no run_group weights; split visible vs hidden with "
            "hidden holding the majority of the float the probe sees"
        )
    else:
        f.notes.append(
            "grader groups: "
            + ", ".join(f"{name}={weight}" for name, weight in groups)
        )
    if ratio is None and groups:
        f.warnings.append(
            "tests/test.sh has run_group weights but none are named visible/public; "
            "the probe cannot tell aiming checks from held-out checks"
        )
    elif ratio is not None:
        if ratio >= 0.50:
            f.errors.append(
                f"visible groups hold {ratio:.0%} of verifier weight; a visible-only "
                "patch will look almost solved to the difficulty probe. Keep visible "
                "under 50% (aim ~30%)"
            )
        elif ratio >= 0.40:
            f.warnings.append(
                f"visible groups hold {ratio:.0%} of verifier weight; consider moving "
                "weight onto hidden enumerated and invariant groups"
            )

    visible_fns = test_functions(files, "tests/visible")
    hidden_fns: List[str] = []
    for name, blob in files.items():
        if not name.startswith("tests/") or not name.endswith(".py"):
            continue
        if not any(h in name.lower() for h in HIDDEN_HINTS):
            continue
        hidden_fns.extend(TEST_DEF_RE.findall(decode(blob)))

    if not hidden_fns:
        sealed = [
            n for n in files
            if n.startswith("tests/") and n != "tests/test.sh"
            and any(h in n.lower() for h in HIDDEN_HINTS)
        ]
        if not sealed:
            f.errors.append(
                "no held-out tests (tests/hidden or similar); the visible/hidden "
                "split the difficulty probe needs is missing"
            )
        else:
            f.warnings.append(
                "held-out files exist but no test_* functions were found under them"
            )
    visible_set = set(visible_fns)
    shared = visible_set & set(hidden_fns)
    if shared and len(shared) >= max(2, len(visible_set) // 2):
        f.errors.append(
            "hidden tests reuse visible test names "
            f"({sorted(shared)[:5]}); hidden must be a different failure mode, "
            "not a copy of visible"
        )
    if hidden_fns and visible_fns and len(hidden_fns) < 2:
        f.warnings.append(
            f"only {len(hidden_fns)} hidden test function(s); a single held-out "
            "assert is usually the same root cause as visible"
        )
    if hidden_fns and not has_property_channel(files):
        f.warnings.append(
            "hidden tests have no generated/property channel (hypothesis, "
            "parametrized ranges, seeded generation); enumerated cases can be memorized"
        )


def check_starting_state(files: Dict[str, bytes], f: Findings) -> None:
    modules = env_modules(files)
    f.notes.append(f"agent-visible code files under environment/: {len(modules)}")
    if len(modules) <= 1:
        f.warnings.append(
            "starting state has at most one code file; unless the spec itself is "
            "the trap, a frontier agent will treat this as a one-file implement"
        )
    decoys = decoy_paths(files)
    if decoys:
        f.notes.append("possible decoy paths: " + ", ".join(decoys[:6]))
    elif len(modules) >= 4:
        f.warnings.append(
            "several modules in /app but no path looks like a decoy (decoy/, "
            "legacy/, unused/). If every file is on the hot path, agents patch "
            "the obvious one and pass. See docs/odyssey-difficulty-design.md"
        )

    instruction = decode(files.get("instruction.md", b""))
    if decoys and "ignore" not in instruction.lower() and "decoy" not in instruction.lower():
        f.notes.append(
            "decoy-like files exist; either cite them as ignore-paths or leave them "
            "as realistic clutter, and prove a decoy-only patch still fails hidden tests"
        )


def check_draft(draft: Optional[Dict], f: Findings) -> None:
    if not draft:
        f.notes.append("no draft loaded; difficultyExplanation was not checked")
        return
    title = str(draft.get("title") or "")
    objective = str(draft.get("objective") or "")
    combined = f"{title}\n{objective}"
    interview = interview_hits(combined)
    if interview:
        f.errors.append(
            "draft title/objective matches a textbook/interview exercise "
            f"({', '.join(interview)}); the probe measures recall"
        )
    explanation = str(draft.get("difficultyExplanation") or "")
    lowered = explanation.lower()
    if explanation and not any(w in lowered for w in TRAP_WORDS):
        f.warnings.append(
            "difficultyExplanation does not name a trap, wrong first attempt, "
            "hidden channel, decoy, or invariant; scale and hours are not trap difficulty"
        )
    if explanation and any(w in lowered for w in SCALE_ONLY) and not any(
        w in lowered for w in TRAP_WORDS
    ):
        f.errors.append(
            "difficultyExplanation reads as scale/time only. Trap difficulty is "
            "what a frontier model gets wrong; collection horizon is a separate "
            "bar (docs/odyssey-long-horizon.md) and does not replace traps"
        )
    exploits = str(draft.get("anticipatedExploits") or "").lower()
    if exploits and "visible" not in exploits and "hard-code" not in exploits and "hardcode" not in exploits:
        f.warnings.append(
            "anticipatedExploits does not mention a visible-only patch or hard-coding; "
            "those are the first two things the probe's agents will try"
        )
    for msg in horizon.horizon_errors(draft):
        f.errors.append(msg)
    for msg in horizon.horizon_warnings(draft):
        f.warnings.append(msg)


def scan(files: Dict[str, bytes], draft: Optional[Dict] = None) -> Findings:
    f = Findings()
    instruction = decode(files.get("instruction.md", b""))
    if instruction:
        check_instruction(instruction, f)
    else:
        f.warnings.append("instruction.md missing from bundle")
    check_grader(files, f)
    check_starting_state(files, f)
    check_draft(draft, f)
    f.notes.append(
        "author probes still required: V visible-only, D decoy-only, "
        "L one-layer, A almost-correct (docs/odyssey-difficulty-design.md)"
    )
    return f


def load_draft(path: Optional[Path]) -> Optional[Dict]:
    if path is None or not path.is_file():
        return None
    return draft_codec.parse_markdown(path.read_text(encoding="utf-8"))


def resolve(args: argparse.Namespace) -> Tuple[Dict[str, bytes], Optional[Dict], str]:
    if args.slug:
        slug = paths.check_slug(args.slug)
        bundle = paths.task_dir(slug)
        if not bundle.is_dir():
            raise SystemExit(f"no task directory at {paths.rel(bundle)}")
        draft = load_draft(paths.draft_path(slug))
        return read_tree(bundle), draft, slug
    if args.bundle:
        bundle = Path(args.bundle)
        if not bundle.is_dir():
            raise SystemExit("bundle must be an unpacked directory")
        draft = load_draft(Path(args.draft) if args.draft else bundle / "draft.md")
        return read_tree(bundle), draft, bundle.name
    raise SystemExit("provide --slug or a bundle directory")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a task for difficulty-design failures")
    parser.add_argument("bundle", nargs="?", help="Unpacked bundle directory")
    parser.add_argument("--slug", help="Resolve drafts/<slug>.md and tasks/<slug>/")
    parser.add_argument("--draft", help="Draft markdown (used with a bundle path)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (not used by package_task.py; errors already block)",
    )
    args = parser.parse_args()
    if args.slug:
        args.bundle = None
    elif args.bundle:
        pass
    else:
        parser.error("provide --slug or a bundle directory")

    files, draft, label = resolve(args)
    f = scan(files, draft)
    status = "PASS" if f.ok else "FAIL"
    print(f"[{status}] difficulty design ({label})")
    for msg in f.errors:
        print(f"  ERROR: {msg}")
    for msg in f.warnings:
        print(f"  WARN:  {msg}")
    for msg in f.notes:
        print(f"  NOTE:  {msg}")
    if f.ok and not f.warnings:
        print("  no structural easy-shape detected; still run probes V/D/L/A")
    if args.strict and f.warnings:
        return 1
    return 0 if f.ok else 1


if __name__ == "__main__":
    sys.exit(main())
