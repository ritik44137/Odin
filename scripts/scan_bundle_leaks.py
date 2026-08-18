#!/usr/bin/env python3
"""Scan a bundle for the mechanical ways an anti-gaming promise gets broken.

The draft's anticipatedExploits field claims the held-out data and grading logic
are sealed. The most common ways that claim turns out to be false are structural
and detectable without running anything:

  - the Dockerfile copies tests/ or solution/ into the image, so /app contains
    the answer key or the reference implementation
  - a held-out fixture is byte-identical to a file the agent can read
  - instruction.md quotes expected outputs verbatim
  - the verifier grades against a file inside /app, which the agent can rewrite
  - tests/ has no held-out portion at all, so there is no visible/hidden split

Findings are advisory where a legitimate design could explain them, and errors
where the seal is definitively broken.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_paths as paths  # noqa: E402

HIDDEN_DIR_HINTS = ("hidden", "held_out", "heldout", "private", "sealed", "secret")
COPY_RE = re.compile(r"^\s*(?:COPY|ADD)\s+(?P<args>.+)$", re.IGNORECASE | re.MULTILINE)
APP_FIXTURE_RE = re.compile(r"/app/[\w./-]*(expected|golden|answer|fixture|reference)[\w./-]*", re.IGNORECASE)
TEXT_SUFFIXES = {
    ".py", ".sh", ".txt", ".md", ".json", ".toml", ".yaml", ".yml", ".cfg", ".ini",
    ".js", ".ts", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".sql", ".csv",
}


@dataclass
class Findings:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def read_bundle(path: Path) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    if path.is_dir():
        for item in path.rglob("*"):
            if item.is_file():
                files[item.relative_to(path).as_posix()] = item.read_bytes()
    elif path.is_file() and path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if not info.is_dir():
                    files[info.filename] = zf.read(info)
    else:
        raise SystemExit("bundle must be a directory or a .zip file")

    if "task.toml" not in files:
        roots = {name.split("/", 1)[0] for name in files if "/" in name}
        if len(roots) == 1 and all("/" in name for name in files):
            files = {name.split("/", 1)[1]: blob for name, blob in files.items()}
    return files


def decode(blob: bytes) -> str:
    return blob.decode("utf-8", errors="ignore")


def is_texty(name: str) -> bool:
    return Path(name).suffix.lower() in TEXT_SUFFIXES


def check_dockerfile(files: Dict[str, bytes], f: Findings) -> None:
    dockerfile = files.get("environment/Dockerfile")
    if dockerfile is None:
        f.warnings.append("environment/Dockerfile is missing, so image contents could not be inspected")
        return

    text = decode(dockerfile)
    for match in COPY_RE.finditer(text):
        args = match.group("args").strip()
        sources = [a for a in args.split() if not a.startswith("--")][:-1]
        for src in sources:
            normalized = src.strip('"\'')
            if normalized.startswith("./"):
                normalized = normalized[2:]
            parts = [p for p in normalized.split("/") if p not in ("", ".")]
            if ".." in parts:
                f.errors.append(
                    f"environment/Dockerfile copies '{src}' from outside the build context, "
                    "which can pull the verifier or reference solution into the image"
                )
                continue
            head = parts[0] if parts else normalized
            if head in {"tests", "solution"}:
                f.errors.append(
                    f"environment/Dockerfile copies '{src}' into the image; "
                    f"{head}/ is agent-readable once it lands in /app"
                )
            if normalized in {".", "*", "./"} or not parts:
                f.warnings.append(
                    f"environment/Dockerfile copies '{src}' wholesale; confirm nothing under the build "
                    "context leaks expected outputs into /app"
                )


def check_duplicate_content(files: Dict[str, bytes], f: Findings) -> None:
    """A held-out file that is byte-identical to an agent-readable one is not held out."""
    sealed = {name: blob for name, blob in files.items() if name.startswith(("tests/", "solution/"))}
    visible = {name: blob for name, blob in files.items() if name.startswith("environment/")}
    if not sealed or not visible:
        return

    visible_by_hash: Dict[str, List[str]] = {}
    for name, blob in visible.items():
        if len(blob) < 64:
            continue
        visible_by_hash.setdefault(hashlib.sha256(blob).hexdigest(), []).append(name)

    for name, blob in sealed.items():
        if len(blob) < 64:
            continue
        digest = hashlib.sha256(blob).hexdigest()
        for twin in visible_by_hash.get(digest, []):
            f.errors.append(f"{name} is byte-identical to {twin}, which is baked into the image")


def check_instruction_leaks(files: Dict[str, bytes], f: Findings) -> None:
    instruction = files.get("instruction.md")
    if instruction is None:
        return
    lines = {
        line.strip()
        for line in decode(instruction).splitlines()
        if len(line.strip()) >= 40 and not line.strip().startswith(("#", "-", "*", ">"))
    }
    if not lines:
        return

    hidden_text = "\n".join(
        decode(blob)
        for name, blob in files.items()
        if name.startswith("tests/") and is_texty(name) and any(h in name.lower() for h in HIDDEN_DIR_HINTS)
    )
    if not hidden_text:
        return
    for line in sorted(lines):
        if line in hidden_text:
            f.warnings.append(
                f"instruction.md repeats a long line verbatim from a held-out test file: {line[:70]!r}"
            )


def check_verifier_surface(files: Dict[str, bytes], f: Findings) -> None:
    test_sh = files.get("tests/test.sh")
    if test_sh is None:
        f.errors.append("tests/test.sh is missing, so the verifier surface could not be checked")
        return

    text = decode(test_sh)
    hits = sorted({m.group(0) for m in APP_FIXTURE_RE.finditer(text)})
    for hit in hits:
        f.warnings.append(
            f"tests/test.sh grades against '{hit}' inside /app, which the agent can overwrite; "
            "keep expected outputs under tests/"
        )

    if re.search(r"\bpip\s+install\b|\bnpm\s+(?:install|i)\b|\bapt-get\s+install\b", text):
        f.warnings.append(
            "tests/test.sh installs packages at grade time; the verifier phase may be sealed, "
            "so bake those dependencies into the image instead"
        )

    sealed_names = [n for n in files if n.startswith("tests/") and n != "tests/test.sh"]
    if not sealed_names:
        f.warnings.append(
            "tests/ contains only test.sh, so there is no held-out material to seal; "
            "the visible/hidden split the review bar expects is missing"
        )
        return

    hidden_names = [n for n in sealed_names if any(h in n.lower() for h in HIDDEN_DIR_HINTS)]
    visible_names = [n for n in sealed_names if "visible" in n.lower() or "public" in n.lower()]
    if not hidden_names:
        f.warnings.append(
            "no file under tests/ is named to mark it as held out (hidden/held_out/private); "
            "state the visible/hidden split explicitly so a reviewer can see it"
        )
    if not visible_names:
        f.notes.append(
            "no file under tests/ is marked visible; if the agent gets no public checks to aim at, "
            "say so deliberately in verificationStrategy"
        )


def check_stale_artifacts(files: Dict[str, bytes], f: Findings) -> None:
    """Compiled bytecode in a bundle can shadow the source the grader means to run."""
    compiled = sorted(
        name for name in files
        if "__pycache__" in name.split("/") or name.endswith((".pyc", ".pyo"))
    )
    if compiled:
        shown = ", ".join(compiled[:3]) + (f", and {len(compiled) - 3} more" if len(compiled) > 3 else "")
        f.warnings.append(
            f"bundle contains compiled Python artifacts ({shown}); stale bytecode can shadow the source "
            "the grader intends to run. scripts/package_task.py drops these, but a hand-made zip will not"
        )


def check_solution_surface(files: Dict[str, bytes], f: Findings) -> None:
    solution_files = [n for n in files if n.startswith("solution/")]
    if not solution_files:
        f.errors.append("no files under solution/, so the oracle cannot run")
        return
    solve = files.get("solution/solve.sh")
    if solve is None:
        return
    text = decode(solve)
    if re.search(r"\b(curl|wget|git\s+clone|pip\s+download)\b", text):
        f.warnings.append(
            "solution/solve.sh appears to fetch from the network; the oracle runs under the same "
            "sealed rollout posture as the agent and would fail offline"
        )
    if "tests/" in text or "/odyssey/tests" in text:
        f.errors.append(
            "solution/solve.sh references the verifier under tests/; the reference must solve the "
            "task, not read or edit the grader"
        )


def resolve_bundle(bundle: Optional[Path], slug: Optional[str]) -> Path:
    if bundle is not None:
        return bundle
    if slug is None:
        raise SystemExit("provide a bundle path or --slug")
    resolved = paths.check_slug(slug)
    if paths.task_dir(resolved).is_dir():
        return paths.task_dir(resolved)
    if paths.zip_path(resolved).is_file():
        return paths.zip_path(resolved)
    raise SystemExit(f"no task directory or zip found for slug '{resolved}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan an Odyssey bundle for leaked held-out material")
    parser.add_argument("bundle", type=Path, nargs="?", help="Bundle directory or ZIP")
    parser.add_argument("--slug", help="Resolve tasks/<slug>/ automatically")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    files = read_bundle(resolve_bundle(args.bundle, args.slug))
    f = Findings()

    check_dockerfile(files, f)
    check_duplicate_content(files, f)
    check_instruction_leaks(files, f)
    check_verifier_surface(files, f)
    check_solution_surface(files, f)
    check_stale_artifacts(files, f)

    status = "PASS" if f.ok else "FAIL"
    print(f"[{status}] bundle leak scan ({len(files)} files)")
    for msg in f.errors:
        print(f"  ERROR: {msg}")
    for msg in f.warnings:
        print(f"  WARN:  {msg}")
    for msg in f.notes:
        print(f"  NOTE:  {msg}")
    if f.ok and not f.warnings and not f.notes:
        print("  no leaked held-out material detected")

    if args.strict and f.warnings:
        return 1
    return 0 if f.ok else 1


if __name__ == "__main__":
    sys.exit(main())
