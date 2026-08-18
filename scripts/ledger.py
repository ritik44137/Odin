#!/usr/bin/env python3
"""Track submitted tasks and bundle content hashes.

Two platform rules make a local record worth keeping: a byte-identical bundle is
blocked by content hash, and near-duplicates are rejected by the similarity
stage. Recording every submission means you can tell before requesting an upload
URL whether a bundle is a true revision and which slugs a new idea sits near.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_paths as paths  # noqa: E402

REPO_ROOT = paths.REPO_ROOT
# The ledger sits at the repo root: drafts/, tasks/, and zip/ each hold exactly one
# kind of artifact, so bookkeeping does not belong in any of them.
LEDGER_PATH = paths.LEDGER_PATH

STATUSES = ("drafting", "submitted", "in_review", "approved", "rejected", "revision_requested")


def load_ledger() -> List[Dict]:
    if not LEDGER_PATH.is_file():
        return []
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{LEDGER_PATH} is not valid JSON: {exc}")
    return data if isinstance(data, list) else []


def save_ledger(entries: List[Dict]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_slug_paths(args: argparse.Namespace) -> None:
    """Fill in --draft and --bundle from --slug when they were not given."""
    if not getattr(args, "slug", None):
        return
    slug = paths.check_slug(args.slug)
    if args.draft is None:
        args.draft = paths.draft_path(slug)
    if args.bundle is None and paths.zip_path(slug).is_file():
        args.bundle = paths.zip_path(slug)


def cmd_add(args: argparse.Namespace) -> int:
    resolve_slug_paths(args)
    if args.draft is None:
        raise SystemExit("provide --draft or --slug")
    if not args.draft.is_file():
        raise SystemExit(f"no draft at {paths.rel(args.draft)}")

    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    slug = draft.get("workingSlug")
    if not slug:
        raise SystemExit("draft has no workingSlug")
    if getattr(args, "slug", None) and args.slug != slug:
        raise SystemExit(
            f"slug mismatch: --slug is '{args.slug}' but {paths.rel(args.draft)} declares workingSlug '{slug}'"
        )

    entries = load_ledger()
    entry = {
        "workingSlug": slug,
        "title": draft.get("title", ""),
        "collectionFamily": draft.get("collectionFamily", ""),
        "taskFamily": draft.get("taskFamily", ""),
        "verifierFamily": draft.get("verifierFamily", ""),
        "status": args.status,
        "recordedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "draftPath": str(args.draft),
    }

    if args.bundle:
        if not args.bundle.is_file():
            raise SystemExit(f"bundle not found: {args.bundle}")
        digest = sha256_file(args.bundle)
        size = args.bundle.stat().st_size
        clash = next((e for e in entries if e.get("bundleSha256") == digest), None)
        if clash:
            print(
                f"[FAIL] this bundle is byte-identical to the one recorded for "
                f"'{clash['workingSlug']}' on {clash['recordedAt']}; a resubmission would be hash-blocked"
            )
            return 1
        entry["bundleSha256"] = digest
        entry["bundleBytes"] = size
        if size > 512 * 1024 * 1024:
            print(f"[WARN] bundle is {size / 1024 / 1024:.1f} MiB, above the 512 MiB upload limit")

    entries.append(entry)
    save_ledger(entries)
    print(f"[PASS] recorded '{slug}' as {args.status} in {LEDGER_PATH.relative_to(REPO_ROOT)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = load_ledger()
    if not entries:
        print("ledger is empty")
        return 0
    width = max(len(e.get("workingSlug", "")) for e in entries)
    for entry in entries:
        if args.status and entry.get("status") != args.status:
            continue
        digest = entry.get("bundleSha256", "")
        short = digest[:12] if digest else "-"
        print(
            f"{entry.get('workingSlug', ''):<{width}}  {entry.get('status', ''):<18}  "
            f"{entry.get('collectionFamily', ''):<24}  {short}  {entry.get('recordedAt', '')}"
        )
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    entries = load_ledger()
    matches = [e for e in entries if e.get("workingSlug") == args.slug]
    if not matches:
        raise SystemExit(f"no ledger entry for slug '{args.slug}'")
    matches[-1]["status"] = args.status
    if args.reason:
        matches[-1]["reason"] = args.reason
    save_ledger(entries)
    print(f"[PASS] '{args.slug}' is now {args.status}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Record and inspect Odyssey task submissions")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Record a draft, optionally with the bundle that was uploaded")
    add.add_argument("--slug", default=None, help="Resolve drafts/<slug>.md and zip/<slug>.zip automatically")
    add.add_argument("--draft", type=Path, default=None)
    add.add_argument("--bundle", type=Path, default=None, help="Path to the uploaded ZIP")
    add.add_argument("--status", choices=STATUSES, default="submitted")
    add.set_defaults(func=cmd_add)

    listing = sub.add_parser("list", help="Show recorded tasks")
    listing.add_argument("--status", choices=STATUSES, default=None)
    listing.set_defaults(func=cmd_list)

    status = sub.add_parser("set-status", help="Update the outcome of a recorded task")
    status.add_argument("--slug", required=True)
    status.add_argument("--status", choices=STATUSES, required=True)
    status.add_argument("--reason", default=None, help="Reviewer reason, for later reference")
    status.set_defaults(func=cmd_set_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
