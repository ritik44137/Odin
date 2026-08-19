#!/usr/bin/env python3
"""Verify a task, then and only then write `zip/<slug>.zip`.

The zip is the last artifact produced, because inspection submits a bundle that
passes automatically: there is no confirmation step later where a mistake can be
caught. So every gate that can run locally runs first, and the archive is written
only if they all pass.

Gates, in order:
  1. draft and bundle structure, and consistency between the two
  2. anti-gaming leak scan
  3. difficulty design (heuristic; does not replace the probe)
  4. novelty against the local corpus
  5. oracle and nop, with --with-oracle (needs Docker)
  6. the archive is re-validated after it is written, since path safety and the
     512 MiB limit are properties of the archive rather than the directory
"""
import argparse
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_paths as paths  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
EXIT_INFRA = 3

# Never ship editor or interpreter droppings inside a graded bundle.
EXCLUDED_NAMES = {".DS_Store", ".gitkeep", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp"}


def run_gate(name: str, cmd: List[str]) -> Tuple[str, int]:
    print(f"\n############ {name}")
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return name, result.returncode


def should_exclude(rel_parts: Tuple[str, ...], suffix: str) -> bool:
    return any(part in EXCLUDED_NAMES for part in rel_parts) or suffix in EXCLUDED_SUFFIXES


def collect_files(task_dir: Path) -> List[Path]:
    return sorted(
        path
        for path in task_dir.rglob("*")
        if path.is_file() and not should_exclude(path.relative_to(task_dir).parts, path.suffix)
    )


def write_zip(task_dir: Path, target: Path, nested_root: str = "") -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    files = collect_files(task_dir)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            rel = path.relative_to(task_dir).as_posix()
            arcname = f"{nested_root}/{rel}" if nested_root else rel
            info = zipfile.ZipInfo(arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Preserve the executable bit: the harness runs test.sh and solve.sh.
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = (0o100000 | mode) << 16
            zf.writestr(info, path.read_bytes())
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a task and package it into zip/<slug>.zip")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--with-oracle", action="store_true", help="also run the oracle and nop checks (needs Docker)")
    parser.add_argument("--nested-root", default="", help="wrap the archive in a top-level directory of this name")
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        default=True,
        help="package despite warnings (default); use --strict to refuse",
    )
    parser.add_argument("--strict", dest="allow_warnings", action="store_false", help="refuse to package on any warning")
    parser.add_argument("--record", action="store_true", help="record the packaged zip in the ledger")
    args = parser.parse_args()

    try:
        slug = paths.check_slug(args.slug)
    except paths.SlugError as exc:
        raise SystemExit(f"invalid slug: {exc}")

    draft = paths.draft_path(slug)
    task_dir = paths.task_dir(slug)
    target = paths.zip_path(slug)

    if not draft.is_file():
        raise SystemExit(f"no draft at {paths.rel(draft)}; run scripts/new_task.py --slug {slug} first")
    if not task_dir.is_dir():
        raise SystemExit(f"no task directory at {paths.rel(task_dir)}")
    for required in paths.REQUIRED_BUNDLE_PATHS:
        if not (task_dir / required).is_file():
            raise SystemExit(f"{paths.rel(task_dir)} is missing the required path {required}")

    strict = ["--strict"] if not args.allow_warnings else []
    gates = [
        ("structure and consistency", [sys.executable, str(SCRIPTS / "validate_odyssey_task.py"),
                                       "--slug", slug, *strict]),
        ("anti-gaming leak scan", [sys.executable, str(SCRIPTS / "scan_bundle_leaks.py"), "--slug", slug, *strict]),
        ("difficulty design", [sys.executable, str(SCRIPTS / "check_difficulty_design.py"), "--slug", slug]),
        ("novelty", [sys.executable, str(SCRIPTS / "check_novelty.py"), "--slug", slug]),
    ]
    if args.with_oracle:
        gates.append(("oracle and nop", [sys.executable, str(SCRIPTS / "run_oracle_nop.py"), "--slug", slug]))

    failures: List[str] = []
    not_measured: List[str] = []
    for name, cmd in gates:
        _, code = run_gate(name, cmd)
        if code == EXIT_INFRA:
            not_measured.append(name)
        elif code != 0:
            failures.append(name)

    if not args.with_oracle:
        not_measured.append("oracle and nop (not requested; pass --with-oracle)")

    print("\n############ packaging")
    if failures:
        for item in failures:
            print(f"FAILED: {item}")
        print(f"\nnot packaging {paths.rel(target)}: fix the failures above first")
        return 1

    count = write_zip(task_dir, target, args.nested_root.strip("/"))
    size_mb = target.stat().st_size / 1024 / 1024
    print(f"wrote {paths.rel(target)} ({count} files, {size_mb:.2f} MiB)")

    _, code = run_gate("archive re-validation", [
        sys.executable, str(SCRIPTS / "validate_odyssey_task.py"),
        "--draft", str(draft), "--bundle", str(target), *strict,
    ])
    if code != 0:
        target.unlink(missing_ok=True)
        print(f"\nthe archive failed validation and was deleted; fix {paths.rel(task_dir)} and re-run")
        return 1

    if args.record:
        run_gate("ledger", [sys.executable, str(SCRIPTS / "ledger.py"), "add", "--slug", slug, "--status", "submitted"])

    print("\n############ summary")
    for item in not_measured:
        print(f"NOT MEASURED: {item}")
    print(f"verified and packaged: {paths.rel(target)}")
    if not args.with_oracle:
        print("The oracle and nop pair was not run. Do not upload until it has passed at least once.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
