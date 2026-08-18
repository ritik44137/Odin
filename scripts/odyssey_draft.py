#!/usr/bin/env python3
"""Markdown Odyssey drafts: one heading per form field, parsed back to a dict.

The platform form is filled by copy-paste. JSON is a poor authoring format for
that, so drafts live as Markdown. The JSON schema remains the validation source
of truth; this module is the codec between the two.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Heading text as it appears in the file, keyed by the schema field name.
HEADINGS: List[Tuple[str, str]] = [
    ("title", "Title"),
    ("workingSlug", "Working slug"),
    ("collectionFamily", "Collection family"),
    ("taskFamily", "Task family"),
    ("verifierFamily", "Verifier family"),
    ("objective", "Objective"),
    ("motivation", "Motivation"),
    ("difficultyExplanation", "Difficulty explanation"),
    ("expertTimeEstimateHours", "Expert time estimate (hours)"),
    ("environmentSummary", "Environment summary"),
    ("resourceEstimate", "Resource estimate"),
    ("networkRequirements", "Network requirements"),
    ("oracleStrategy", "Oracle strategy"),
    ("verificationStrategy", "Verification strategy"),
    ("binarySuccessCondition", "Binary success condition"),
    ("partialScoreStrategy", "Partial score strategy"),
    ("anticipatedExploits", "Anticipated exploits"),
    ("notes", "Notes (local only -- do not paste)"),
]

HEADING_BY_FIELD = {field: heading for field, heading in HEADINGS}

RESOURCE_KEYS = (
    "cpuMillis",
    "memoryMb",
    "storageMb",
    "gpuCount",
    "agentTimeoutSec",
    "verifierTimeoutSec",
)

PREAMBLE = """# Odyssey task draft

Copy each section **body** (not the `##` heading) into the matching field on the
Odyssey form. Use only keyboard-accessible ASCII (`->`, `^2`, `--`, `<=`,
straight quotes). The Notes section is local scratch and has no form counterpart.
"""

# Platform paste fields and agent-facing instruction.md may only use characters
# a standard keyboard can type: tab, CR, LF, and printable ASCII (0x20-0x7E).
_KEYBOARD_OK = frozenset(chr(i) for i in range(0x20, 0x7F)) | {"\t", "\n", "\r"}
_KEYBOARD_REPLACEMENTS = {
    "\u2192": "->",
    "\u2190": "<-",
    "\u2194": "<->",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u2014": "--",
    "\u2013": "-",
    "\u2212": "-",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u00d7": "*",
    "\u2026": "...",
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u00a0": "a normal space",
}


def is_keyboard_char(ch: str) -> bool:
    return ch in _KEYBOARD_OK


def iter_string_fields(obj: Any, prefix: str) -> Iterable[Tuple[str, str]]:
    """Yield (path, text) for every string nested under a draft-shaped object."""
    if isinstance(obj, str):
        yield prefix, obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from iter_string_fields(value, f"{prefix}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from iter_string_fields(value, f"{prefix}[{index}]")


def keyboard_ascii_violations(text: str, label: str, *, limit: int = 8) -> List[str]:
    """Describe the first non-keyboard characters in text, if any."""
    hits: List[str] = []
    extra = 0
    line = 1
    col = 1
    for ch in text:
        if not is_keyboard_char(ch):
            if len(hits) < limit:
                code = ord(ch)
                name = unicodedata.name(ch, "unknown character")
                replacement = _KEYBOARD_REPLACEMENTS.get(ch)
                hint = f"use {replacement}" if replacement else "replace with a keyboard equivalent"
                hits.append(
                    f"{label} contains non-keyboard character U+{code:04X} {name} "
                    f"at line {line} col {col} ({hint})"
                )
            else:
                extra += 1
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
    if extra:
        hits.append(f"{label} has {extra} more non-keyboard character(s)")
    return hits


_HEADING_RE = re.compile(r"^##[ \t]+(.+?)\s*$", re.MULTILINE)
_KV_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.*)$")


class DraftError(ValueError):
    pass


def resolve_field(name: str) -> str:
    """Map a heading or schema key to the schema field name."""
    field = _FIELD_BY_NORM.get(_norm(name))
    if field is None:
        raise DraftError(f"unknown draft field: {name!r}")
    return field


def _norm(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", heading.lower())


_FIELD_BY_NORM = {_norm(heading): field for field, heading in HEADINGS}
# Also accept the schema key itself as a heading, e.g. `## workingSlug`.
_FIELD_BY_NORM.update({_norm(field): field for field, _heading in HEADINGS})


def parse_markdown(text: str) -> Dict[str, Any]:
    """Turn a form-shaped Markdown draft into the dict the schema validates."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        raise DraftError("draft has no `##` field headings")

    sections: Dict[str, str] = {}
    for i, match in enumerate(matches):
        field = _FIELD_BY_NORM.get(_norm(match.group(1)))
        if field is None:
            raise DraftError(f"unknown draft heading: {match.group(1)!r}")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if field in sections:
            raise DraftError(f"duplicate heading for {field}")
        sections[field] = body

    draft: Dict[str, Any] = {}
    for field, _heading in HEADINGS:
        if field not in sections:
            continue
        body = sections[field]
        if field == "expertTimeEstimateHours":
            draft[field] = _parse_number(body, field)
        elif field == "resourceEstimate":
            draft[field] = _parse_resource(body)
        elif field == "networkRequirements":
            draft[field] = _parse_network(body)
        else:
            draft[field] = body
    return draft


def _parse_number(body: str, field: str) -> float:
    line = body.splitlines()[0].strip() if body else ""
    try:
        value = float(line)
    except ValueError as exc:
        raise DraftError(f"{field} must be a number, got {line!r}") from exc
    if value == int(value) and "." not in line:
        return int(value)
    return value


def _parse_kv_block(body: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    pending_key: Optional[str] = None
    pending_lines: List[str] = []

    def flush() -> None:
        nonlocal pending_key, pending_lines
        if pending_key is None:
            return
        out[pending_key] = "\n".join(pending_lines).strip()
        pending_key = None
        pending_lines = []

    for raw in body.splitlines():
        match = _KV_RE.match(raw)
        if match and (pending_key is None or match.group(1) not in ("",)):
            # A new key starts a new entry. Continuation lines are those that
            # do not look like `key: value` with a known-looking key.
            flush()
            pending_key = match.group(1)
            pending_lines = [match.group(2)]
        elif pending_key is not None:
            pending_lines.append(raw)
        elif raw.strip():
            raise DraftError(f"expected `key: value` line, got {raw!r}")
    flush()
    return out


def _parse_resource(body: str) -> Dict[str, int]:
    kv = _parse_kv_block(body)
    unknown = sorted(set(kv) - set(RESOURCE_KEYS))
    if unknown:
        raise DraftError(f"unknown resourceEstimate keys: {', '.join(unknown)}")
    parsed: Dict[str, int] = {}
    for key, raw in kv.items():
        try:
            parsed[key] = int(raw.strip())
        except ValueError as exc:
            raise DraftError(f"resourceEstimate.{key} must be an integer, got {raw!r}") from exc
    return parsed


def _parse_network(body: str) -> Dict[str, Any]:
    kv = _parse_kv_block(body)
    allowed = {"mode", "justification", "hosts"}
    unknown = sorted(set(kv) - allowed)
    if unknown:
        raise DraftError(f"unknown networkRequirements keys: {', '.join(unknown)}")
    mode = kv.get("mode", "").strip()
    justification = kv.get("justification", "").strip()
    hosts_raw = kv.get("hosts", "").strip()
    hosts: List[str] = []
    if hosts_raw and hosts_raw.lower() not in {"(none)", "none", "-"}:
        for part in re.split(r"[\n,]+", hosts_raw):
            item = part.strip()
            if item:
                hosts.append(item)
    return {"mode": mode, "justification": justification, "hosts": hosts}


def render_markdown(draft: Dict[str, Any]) -> str:
    """Write a dict back to the copy-paste Markdown form."""
    parts = [PREAMBLE.rstrip(), ""]
    for field, heading in HEADINGS:
        if field not in draft:
            continue
        parts.append(f"## {heading}")
        parts.append("")
        value = draft[field]
        if field == "resourceEstimate":
            for key in RESOURCE_KEYS:
                if key in value:
                    parts.append(f"{key}: {value[key]}")
        elif field == "networkRequirements":
            parts.append(f"mode: {value.get('mode', '')}")
            parts.append(f"justification: {value.get('justification', '')}")
            hosts = value.get("hosts") or []
            parts.append("hosts: " + (", ".join(hosts) if hosts else "(none)"))
        else:
            parts.append(str(value).rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def load(path: Path) -> Dict[str, Any]:
    """Load a draft from Markdown or, for older files, JSON."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise DraftError(f"draft file not found: {path}") from None
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DraftError(f"invalid JSON in draft file {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise DraftError(f"draft {path} is not a JSON object")
        return data
    try:
        return parse_markdown(text)
    except DraftError:
        # A `.md` path that is actually JSON, or a typo heading, should still
        # produce a useful error rather than a JSON traceback.
        raise


def dump(path: Path, draft: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(draft), encoding="utf-8")
