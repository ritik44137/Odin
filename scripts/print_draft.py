#!/usr/bin/env python3
"""Print one Odyssey form field, ready to paste.

    python3 scripts/print_draft.py --slug <slug> --field objective

Omit --field to list the form fields. The Notes section is never printed,
because the platform has no such field.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_draft as draft_codec  # noqa: E402
import odyssey_paths as paths  # noqa: E402

PASTE_FIELDS = [field for field, _heading in draft_codec.HEADINGS if field != "notes"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a draft field for pasting into the Odyssey form")
    parser.add_argument("--slug", help="Resolve drafts/<slug>.md")
    parser.add_argument("--draft", type=Path, help="Draft Markdown path")
    parser.add_argument("--field", help="Schema field name (e.g. objective) or heading (e.g. 'Working slug')")
    parser.add_argument("--list", action="store_true", help="List pasteable fields and exit")
    args = parser.parse_args()

    if args.list or not args.field:
        print("Paste these section bodies into the matching Odyssey form fields:\n")
        for field, heading in draft_codec.HEADINGS:
            if field == "notes":
                continue
            print(f"  {heading:28}  --field {field}")
        if not args.field:
            print("\nExample: python3 scripts/print_draft.py --slug three-way-merge-engine --field objective")
        return 0 if args.list or (args.slug is None and args.draft is None) else 0

    draft_file = args.draft
    if draft_file is None:
        if not args.slug:
            parser.error("provide --slug or --draft")
        draft_file = paths.draft_path(args.slug)
    data = draft_codec.load(draft_file)
    try:
        key = draft_codec.resolve_field(args.field)
    except draft_codec.DraftError as exc:
        print(exc, file=sys.stderr)
        return 1
    if key == "notes":
        print("Notes is local-only and has no Odyssey form field.", file=sys.stderr)
        return 2
    if key not in data:
        print(f"no field {args.field!r} in {paths.rel(draft_file)}", file=sys.stderr)
        return 1
    value = data[key]
    if key == "resourceEstimate":
        for k in draft_codec.RESOURCE_KEYS:
            if k in value:
                print(f"{k}: {value[k]}")
    elif key == "networkRequirements":
        print(f"mode: {value.get('mode', '')}")
        print(f"justification: {value.get('justification', '')}")
        hosts = value.get("hosts") or []
        print("hosts: " + (", ".join(hosts) if hosts else "(none)"))
    else:
        print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
