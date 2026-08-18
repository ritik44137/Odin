#!/usr/bin/env python3
"""Cheap local stand-in for the similarity/dedup funnel stage.

The platform rejects a task that sits too close to an existing one using an
embedding search over the whole corpus. That corpus is not available here, but
most self-inflicted near-duplicates are duplicates of your own earlier work, and
those are visible locally.

This compares a draft against every other draft under the corpus roots using
TF-IDF cosine similarity over character n-grams and word tokens, then reports the
nearest neighbours. Treat a high score as a prompt to change the problem, not the
wording: renaming a task does not make it novel.
"""
import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import odyssey_draft as draft_codec  # noqa: E402
import odyssey_paths as paths  # noqa: E402

REPO_ROOT = paths.REPO_ROOT
DEFAULT_CORPUS = ["drafts", "examples"]

# Fields that carry the conceptual identity of the task. Resource and network
# blocks are deliberately excluded; they are near-identical across good tasks.
COMPARED_FIELDS = (
    "title",
    "objective",
    "motivation",
    "difficultyExplanation",
    "environmentSummary",
    "oracleStrategy",
    "verificationStrategy",
    "binarySuccessCondition",
    "anticipatedExploits",
)

WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "that", "this",
    "for", "on", "with", "as", "by", "be", "are", "must", "not", "but", "from",
    "which", "than", "then", "so", "at", "can", "will", "any", "all", "if",
}


def draft_text(draft: Dict) -> str:
    parts = [str(draft.get(field, "")) for field in COMPARED_FIELDS]
    return "\n".join(parts).lower()


def features(text: str) -> Counter:
    words = [w for w in WORD_RE.findall(text) if w not in STOPWORDS and len(w) > 2]
    feats = Counter(words)
    feats.update(f"{a}_{b}" for a, b in zip(words, words[1:]))
    return feats


def cosine(a: Counter, b: Counter, idf: Dict[str, float]) -> float:
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    num = sum(a[t] * b[t] * idf.get(t, 0.0) ** 2 for t in shared)
    norm_a = math.sqrt(sum((a[t] * idf.get(t, 0.0)) ** 2 for t in a))
    norm_b = math.sqrt(sum((b[t] * idf.get(t, 0.0)) ** 2 for t in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return num / (norm_a * norm_b)


def collect_drafts(roots: List[Path], exclude: Path) -> List[Tuple[Path, Dict]]:
    found: List[Tuple[Path, Dict]] = []
    exclude = exclude.resolve()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.resolve() == exclude:
                continue
            if not _looks_like_draft_file(path):
                continue
            try:
                data = draft_codec.load(path)
            except (draft_codec.DraftError, UnicodeDecodeError, OSError):
                continue
            if isinstance(data, dict) and data.get("objective") and data.get("workingSlug"):
                found.append((path, data))
    return found


def _looks_like_draft_file(path: Path) -> bool:
    name = path.name.lower()
    if "schema" in name:
        return False
    suffix = path.suffix.lower()
    if suffix not in {".md", ".json"}:
        return False
    try:
        path.resolve().relative_to(paths.DRAFTS_DIR.resolve())
        under_drafts = True
    except ValueError:
        under_drafts = False
    return under_drafts or "draft" in name


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a draft against local drafts for novelty")
    parser.add_argument("draft", type=Path, nargs="?", help="Draft Markdown (or JSON) to check")
    parser.add_argument("--slug", help="Resolve drafts/<slug>.md automatically")
    parser.add_argument("--corpus", nargs="*", default=None, help="Directories of drafts to compare against")
    parser.add_argument("--threshold", type=float, default=0.55, help="Similarity above which the check fails")
    parser.add_argument("--top", type=int, default=5, help="How many neighbours to report")
    args = parser.parse_args()

    draft_file = args.draft
    if draft_file is None:
        if not args.slug:
            parser.error("provide a draft path or --slug")
        draft_file = paths.draft_path(args.slug)
        if not draft_file.is_file():
            parser.error(f"no draft at {paths.rel(draft_file)}")

    target = draft_codec.load(draft_file)
    roots = [Path(p) if Path(p).is_absolute() else REPO_ROOT / p for p in (args.corpus or DEFAULT_CORPUS)]
    corpus = collect_drafts(roots, draft_file)

    if not corpus:
        print("[PASS] novelty check: no other local drafts to compare against")
        print("  NOTE:  keep every draft under drafts/ so this check gains signal over time")
        return 0

    target_feats = features(draft_text(target))
    corpus_feats = [(path, features(draft_text(data)), data) for path, data in corpus]

    documents = [target_feats] + [f for _, f, _ in corpus_feats]
    total = len(documents)
    doc_freq: Counter = Counter()
    for doc in documents:
        doc_freq.update(set(doc))
    idf = {term: math.log(total / (1 + df)) + 1.0 for term, df in doc_freq.items()}

    scored = sorted(
        ((cosine(target_feats, f, idf), path, data) for path, f, data in corpus_feats),
        key=lambda item: item[0],
        reverse=True,
    )

    worst = scored[0][0]
    status = "FAIL" if worst >= args.threshold else "PASS"
    print(f"[{status}] novelty check against {len(corpus)} local draft(s), threshold {args.threshold:.2f}")
    for score, path, data in scored[: args.top]:
        flag = "  <-- too close" if score >= args.threshold else ""
        family = data.get("collectionFamily", "?")
        rel = path.relative_to(REPO_ROOT) if REPO_ROOT in path.resolve().parents else path
        print(f"  {score:.3f}  {rel} [{family}]{flag}")

    if status == "FAIL":
        print("  Change the underlying problem, not the wording: the similarity stage compares meaning.")
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
