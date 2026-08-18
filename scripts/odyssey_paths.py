#!/usr/bin/env python3
"""The repository layout, in one place.

One slug names a task everywhere it appears:

    drafts/<slug>.md       the draft, and nothing else
    tasks/<slug>/          the bundle root: exactly the files that get zipped
    zip/<slug>.zip         the archive that gets uploaded, and nothing else
    plans/<slug>.md        the pre-implementation bundle plan

The slug is chosen once, when the draft is created, and propagates unchanged. Every
script accepts `--slug` and resolves these paths itself, so no command needs a path
typed by hand and the three task directories cannot drift apart.
"""
import re
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent

DRAFTS_DIR = REPO_ROOT / "drafts"
TASKS_DIR = REPO_ROOT / "tasks"
ZIP_DIR = REPO_ROOT / "zip"
PLANS_DIR = REPO_ROOT / "plans"

TEMPLATES_DIR = REPO_ROOT / "templates"
SCHEMA_PATH = REPO_ROOT / "schemas" / "odyssey-task-draft.schema.json"
LEDGER_PATH = REPO_ROOT / "LEDGER.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MIN_LEN = 3
SLUG_MAX_LEN = 80

# The five paths the structure stage requires, relative to the bundle root.
REQUIRED_BUNDLE_PATHS = [
    "task.toml",
    "instruction.md",
    "environment/Dockerfile",
    "tests/test.sh",
    "solution/solve.sh",
]


class SlugError(ValueError):
    pass


def check_slug(slug: str) -> str:
    """Validate a slug against the same rule the draft form applies."""
    if not isinstance(slug, str) or not slug:
        raise SlugError("slug must be a non-empty string")
    if len(slug) < SLUG_MIN_LEN or len(slug) > SLUG_MAX_LEN:
        raise SlugError(f"slug must be {SLUG_MIN_LEN}-{SLUG_MAX_LEN} characters, got {len(slug)}")
    if not SLUG_RE.fullmatch(slug):
        raise SlugError(
            f"slug '{slug}' must be lowercase kebab-case: letters a-z, digits, and single hyphens"
        )
    return slug


def draft_path(slug: str) -> Path:
    return DRAFTS_DIR / f"{check_slug(slug)}.md"


def task_dir(slug: str) -> Path:
    return TASKS_DIR / check_slug(slug)


def zip_path(slug: str) -> Path:
    return ZIP_DIR / f"{check_slug(slug)}.zip"


def plan_path(slug: str) -> Path:
    return PLANS_DIR / f"{check_slug(slug)}.md"


def known_slugs() -> List[str]:
    """Every slug that has a draft, a task directory, or a zip."""
    slugs = set()
    if DRAFTS_DIR.is_dir():
        slugs.update(p.stem for p in DRAFTS_DIR.glob("*.md"))
    if TASKS_DIR.is_dir():
        slugs.update(p.name for p in TASKS_DIR.iterdir() if p.is_dir())
    if ZIP_DIR.is_dir():
        slugs.update(p.stem for p in ZIP_DIR.glob("*.zip"))
    return sorted(s for s in slugs if SLUG_RE.fullmatch(s))


def describe(slug: str) -> str:
    """A one-line status of which artifacts exist for a slug."""
    marks = [
        ("draft", draft_path(slug).is_file()),
        ("plan", plan_path(slug).is_file()),
        ("task", task_dir(slug).is_dir()),
        ("zip", zip_path(slug).is_file()),
    ]
    return "  ".join(f"{'+' if present else '-'}{name}" for name, present in marks)


def rel(path: Path) -> str:
    """Repo-relative path for display, falling back to the absolute path."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
