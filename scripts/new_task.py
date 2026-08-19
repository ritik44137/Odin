#!/usr/bin/env python3
"""Create the directories and starting files for one task.

The slug is chosen here, once, and propagates: `drafts/<slug>.md`,
`plans/<slug>.md`, `tasks/<slug>/`, and later `zip/<slug>.zip`.

This scaffolds only. The draft still has to be written to the standard the draft
form expects, and the bundle still has to be implemented; both are left as
templates that the validator will reject until they are real, which is deliberate.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_draft as draft_codec  # noqa: E402
import odyssey_paths as paths  # noqa: E402

TEMPLATE_MAP = {
    "task.toml": "odyssey-task-toml.template.toml",
    "instruction.md": "odyssey-instruction.template.md",
    "tests/test.sh": "odyssey-test.template.sh",
    "solution/solve.sh": "odyssey-solve.template.sh",
}

APP_PLACEHOLDER = """# Starting state

Replace this directory with the code the agent finds in /app at the start of the
rollout: the real module layout, the incomplete or broken implementation, and any
developer-facing documentation that a real repository would carry.
"""


def write(path: Path, content: str, executable: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)
    return paths.rel(path)


def build_draft(slug: str, title: str, collection_family: str, task_family: str, verifier_family: str) -> str:
    template = draft_codec.parse_markdown(
        (paths.TEMPLATES_DIR / "odyssey-task-draft.template.md").read_text(encoding="utf-8")
    )
    template["title"] = title
    template["workingSlug"] = slug
    template["collectionFamily"] = collection_family
    template["taskFamily"] = task_family
    template["verifierFamily"] = verifier_family
    template["notes"] = (
        "Local scratch only; the Odyssey form has no notes field. Do not paste this section."
    )
    return draft_codec.render_markdown(template)


def build_plan(slug: str, title: str, collection_family: str, task_family: str, verifier_family: str) -> str:
    template = (paths.TEMPLATES_DIR / "odyssey-bundle-plan.template.md").read_text(encoding="utf-8")
    return (
        template.replace("- **Title:**", f"- **Title:** {title}")
        .replace("- **Working slug:**", f"- **Working slug:** {slug}")
        .replace("- **Collection family:**", f"- **Collection family:** {collection_family}")
        .replace("- **Task family:**", f"- **Task family:** {task_family}")
        .replace("- **Verifier family:**", f"- **Verifier family:** {verifier_family}")
    )


def main() -> int:
    schema = json.loads(paths.SCHEMA_PATH.read_text(encoding="utf-8"))
    enums = schema["properties"]

    parser = argparse.ArgumentParser(description="Scaffold a new Odyssey task from a slug")
    parser.add_argument("--slug", required=True, help="lowercase-kebab slug, chosen from the task idea")
    parser.add_argument("--title", default=None, help="human-readable title (defaults to the slug, spaced)")
    parser.add_argument("--collection-family", default="Library clone", choices=enums["collectionFamily"]["enum"])
    parser.add_argument("--task-family", default="feature_development", choices=enums["taskFamily"]["enum"])
    parser.add_argument("--verifier-family", default="programmatic", choices=enums["verifierFamily"]["enum"])
    parser.add_argument("--force", action="store_true", help="overwrite files that already exist")
    args = parser.parse_args()

    try:
        slug = paths.check_slug(args.slug)
    except paths.SlugError as exc:
        raise SystemExit(f"invalid slug: {exc}")

    title = args.title or slug.replace("-", " ").capitalize()

    draft = paths.draft_path(slug)
    plan = paths.plan_path(slug)
    task = paths.task_dir(slug)

    existing = [p for p in (draft, plan, task) if p.exists()]
    if existing and not args.force:
        for path in existing:
            print(f"already exists: {paths.rel(path)}", file=sys.stderr)
        raise SystemExit("refusing to overwrite; pass --force if that is what you want")

    created: List[str] = []
    created.append(write(draft, build_draft(slug, title, args.collection_family, args.task_family, args.verifier_family)))
    created.append(write(plan, build_plan(slug, title, args.collection_family, args.task_family, args.verifier_family)))

    for rel_path, template_name in TEMPLATE_MAP.items():
        content = (paths.TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
        if rel_path == "task.toml":
            content = content.replace("replace-with-task-title", title).replace("replace-with-working-slug", slug)
            content = content.replace('collection_family = "Library clone"', f'collection_family = "{args.collection_family}"')
            content = content.replace('task_family = "feature_development"', f'task_family = "{args.task_family}"')
            content = content.replace('verifier_family = "programmatic"', f'verifier_family = "{args.verifier_family}"')
        created.append(write(task / rel_path, content, executable=rel_path.endswith(".sh")))

    created.append(write(task / "environment" / "Dockerfile", (paths.TEMPLATES_DIR / "odyssey-dockerfile.template").read_text(encoding="utf-8")))
    created.append(write(task / "environment" / "app" / "README.md", APP_PLACEHOLDER))
    created.append(write(task / "tests" / "visible" / ".gitkeep", ""))
    created.append(write(task / "tests" / "hidden" / ".gitkeep", ""))

    print(f"scaffolded '{slug}':")
    for item in created:
        print(f"  {item}")
    print()
    print("Next, in order:")
    print(f"  1. write the draft in {paths.rel(draft)} to the standard the draft form expects")
    print(f"  2. python3 scripts/check_novelty.py --slug {slug}")
    print(f"  3. python3 scripts/validate_odyssey_task.py --slug {slug}")
    print(f"  4. fill in {paths.rel(plan)}, then implement {paths.rel(task)}/")
    print(f"  5. scripts/preflight.sh --slug {slug} --with-oracle")
    print(f"  6. python3 scripts/package_task.py --slug {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
