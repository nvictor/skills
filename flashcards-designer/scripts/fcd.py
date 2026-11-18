#!/usr/bin/env python3
"""Deterministic helper for the flashcards-designer skill.

Owns the parts of a deck that must not depend on an agent's judgment:
ID allocation, source hashing, structural checks, retirement, and promotion
of approved draft batches into the deck. Standard library only.

Everything lives in one deck root folder:
  <topic>/<name>.md       approved cards (the deck)
  registry.json           per-prefix ID counters (never decrease)
  drafts/*.md             proposed batches (not part of the deck)
  drafts/_promoted/       drafts already promoted
"drafts" is a reserved name and cannot be a topic.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

FIELD_RE = re.compile(r"^(ID|Q|A|C|X|Source|Retired):[ \t]?(.*)$")
# A continuation line that looks like a field or card heading is written with one
# extra leading backslash, and read back with one removed.
ESCAPABLE_RE = re.compile(r"^(\\*)((?:ID|Q|A|C|X|Source|Retired):|## )")
ID_RE = re.compile(r"^(?P<prefix>[a-z0-9][a-z0-9-]*)-(?P<num>\d{3,})$")
PREFIX_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SOURCE_RE = re.compile(
    r"^(?P<path>[^\s#]+)(?:#(?P<loc>.*?))?\s+sha256:(?P<hash>[0-9a-f]{8,64})$"
)
PASTED_RE = re.compile(r"^pasted:\s*\S")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINES_RE = re.compile(r"^L(\d+)-(\d+)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
YES_NO_RE = re.compile(
    r"^(is|are|was|were|does|do|did|can|could|will|would|should|has|have|had)\b",
    re.IGNORECASE,
)
HASH_LEN = 12
DRAFTS_DIR = "drafts"
MAX_ANSWER_WORDS = 60
MAX_ANSWER_LINES = 5


class FcdError(Exception):
    pass


# ---------------------------------------------------------------- parsing


class Card:
    def __init__(self, file: Path, title: str, line: int):
        self.file = file
        self.title = title
        self.line = line
        self.fields: dict[str, str] = {}
        self.field_lines: dict[str, int] = {}
        self.repeated: list[str] = []

    @property
    def id(self) -> str | None:
        return self.fields.get("ID") or None

    @property
    def retired(self) -> bool:
        return "Retired" in self.fields


def parse_cards(path: Path) -> list[Card]:
    cards: list[Card] = []
    cur: Card | None = None
    field: str | None = None
    in_fence = False
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if cur and field:
                cur.fields[field] += "\n" + line
            continue
        if not in_fence and line.startswith("## "):
            cur = Card(path, line[3:].strip(), i)
            cards.append(cur)
            field = None
            continue
        if cur is None:
            continue
        m = None if in_fence else FIELD_RE.match(line)
        if m:
            field = m.group(1)
            if field in cur.fields:
                cur.repeated.append(field)
            cur.fields[field] = m.group(2)
            cur.field_lines[field] = i
        elif field:
            if not in_fence:
                m = ESCAPABLE_RE.match(line)
                if m and m.group(1):
                    line = line[1:]
            cur.fields[field] += "\n" + line
    for c in cards:
        c.fields = {k: v.strip() for k, v in c.fields.items()}
    return cards


def escape_value(value: str) -> str:
    """Escape continuation lines (outside code fences) that the parser would misread."""
    lines = value.split("\n")
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        elif i and not in_fence and ESCAPABLE_RE.match(line):
            lines[i] = "\\" + line
    return "\n".join(lines)


def render_card(title: str, card_id: str, fields: dict[str, str]) -> str:
    out = [f"## {title}", "", f"ID: {card_id}"]
    if "C" in fields:
        out.append(f"C: {escape_value(fields['C'])}")
        if fields.get("X"):
            out.append(f"X: {escape_value(fields['X'])}")
    else:
        out.append(f"Q: {escape_value(fields['Q'])}")
        out.append(f"A: {escape_value(fields['A'])}")
    out.append(f"Source: {fields['Source']}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- hashing


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_section(text: str, locator: str | None) -> str | None:
    if not locator:
        return text
    lm = LINES_RE.match(locator)
    lines = text.splitlines()
    if lm:
        a, b = int(lm.group(1)), int(lm.group(2))
        if a < 1 or a > b or a > len(lines):
            return None
        return "\n".join(lines[a - 1 : b])
    in_fence = False
    level = None
    out: list[str] = []
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
        h = None if in_fence else HEADING_RE.match(line)
        if level is None:
            if h and h.group(2).strip().lower() == locator.strip().lower():
                level = len(h.group(1))
                out.append(line)
        else:
            if h and len(h.group(1)) <= level:
                break
            out.append(line)
    return "\n".join(out) if level is not None else None


def section_hash(source: Path, locator: str | None) -> tuple[str, str | None]:
    """Return (status, hash). status: ok | missing-file | missing-section."""
    if not source.is_file():
        return "missing-file", None
    text = source.read_text(encoding="utf-8", errors="replace")
    section = extract_section(text, locator)
    if section is None:
        return "missing-section", None
    digest = hashlib.sha256(normalize(section).encode("utf-8")).hexdigest()
    return "ok", digest[:HASH_LEN]


def source_value(card_file: Path, source: Path, locator: str | None) -> str:
    status, digest = section_hash(source, locator)
    if status != "ok":
        raise FcdError(f"cannot hash source {source}: {status}")
    rel = _relpath(source, card_file.parent)
    loc = f"#{locator}" if locator else ""
    return f"{rel}{loc} sha256:{digest}"


def _relpath(target: Path, start: Path) -> str:
    import os

    return os.path.relpath(target.resolve(), start.resolve())


# --------------------------------------------------------------- registry


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def registry_path(root: Path) -> Path:
    return root / "registry.json"


def load_registry(root: Path) -> dict:
    p = registry_path(root)
    if not p.exists():
        return {"version": 1, "counters": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def save_registry(root: Path, reg: dict) -> None:
    p = registry_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def card_files(root: Path) -> list[Path]:
    drafts = root / DRAFTS_DIR
    return sorted(
        f for f in root.rglob("*.md")
        if not inside(drafts, f) and not any(part.startswith(".") for part in f.relative_to(root).parts)
    )


def deck_max_numbers(root: Path) -> dict[str, int]:
    seen: dict[str, int] = {}
    for f in card_files(root):
        for c in parse_cards(f):
            m = ID_RE.match(c.id or "")
            if m:
                p = m.group("prefix")
                seen[p] = max(seen.get(p, 0), int(m.group("num")))
    return seen


def allocate(root: Path, prefix: str, count: int) -> list[str]:
    if not PREFIX_RE.match(prefix):
        raise FcdError(f"invalid ID prefix: {prefix!r}")
    if count < 1:
        raise FcdError("count must be at least 1")
    reg = load_registry(root)
    start = max(reg["counters"].get(prefix, 0), deck_max_numbers(root).get(prefix, 0))
    ids = [f"{prefix}-{start + n:03d}" for n in range(1, count + 1)]
    reg["counters"][prefix] = start + count
    save_registry(root, reg)
    return ids


# ------------------------------------------------------------------ check


def _finding(sev, code, card_or_file, msg):
    if isinstance(card_or_file, Card):
        return {
            "severity": sev,
            "code": code,
            "file": str(card_or_file.file),
            "line": card_or_file.line,
            "id": card_or_file.id,
            "message": msg,
        }
    return {
        "severity": sev,
        "code": code,
        "file": str(card_or_file),
        "line": 0,
        "id": None,
        "message": msg,
    }


def _norm_q(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def check_deck(root: Path) -> list[dict]:
    findings: list[dict] = []
    by_id: dict[str, list[Card]] = {}
    questions: dict[str, list[Card]] = {}
    reg = load_registry(root)
    for f in card_files(root):
        for c in parse_cards(f):
            for dup in c.repeated:
                findings.append(_finding("error", "FIELD_REPEATED", c, f"field {dup} repeated"))
            cid = c.id
            if not cid:
                findings.append(_finding("error", "ID_MISSING", c, "card has no ID"))
            elif not ID_RE.match(cid):
                findings.append(_finding("error", "ID_MALFORMED", c, f"bad ID {cid!r}"))
            else:
                by_id.setdefault(cid, []).append(c)
            is_cloze = "C" in c.fields
            if "X" in c.fields and not is_cloze:
                findings.append(_finding("error", "EXTRA_WITHOUT_CLOZE", c, "X: is only valid on C: cards"))
            if is_cloze:
                if "{{c" not in c.fields["C"]:
                    findings.append(_finding("error", "CLOZE_NO_DELETION", c, "C: has no {{c1::...}}"))
            else:
                for req in ("Q", "A"):
                    if not c.fields.get(req):
                        findings.append(_finding("error", "FIELD_MISSING", c, f"missing {req}:"))
            if not c.fields.get("Source"):
                findings.append(_finding("error", "FIELD_MISSING", c, "missing Source:"))
            if c.retired:
                continue
            q = c.fields.get("Q", "")
            if q:
                questions.setdefault(_norm_q(q), []).append(c)
                if YES_NO_RE.match(q.strip()):
                    findings.append(_finding("warning", "POSSIBLE_YES_NO", c, "question may be yes/no"))
            a = c.fields.get("A", "")
            if len(a.split()) > MAX_ANSWER_WORDS or a.count("\n") + 1 > MAX_ANSWER_LINES:
                findings.append(_finding("warning", "ANSWER_OVERLOADED", c, "answer is long; consider splitting"))
            findings.extend(_check_source(c))
    for cid, cards in by_id.items():
        if len(cards) > 1:
            where = ", ".join(f"{k.file.name}:{k.line}" for k in cards)
            findings.append(_finding("error", "ID_DUPLICATE", cards[0], f"{cid} appears {len(cards)} times ({where})"))
    for cards in questions.values():
        if len(cards) > 1:
            ids = ", ".join(k.id or "?" for k in cards)
            findings.append(_finding("warning", "QUESTION_DUPLICATE", cards[0], f"same question in: {ids}"))
    maxes = deck_max_numbers(root)
    for prefix, high in maxes.items():
        if reg["counters"].get(prefix, 0) < high:
            findings.append(
                _finding("error", "REGISTRY_BEHIND", registry_path(root),
                         f"counter for {prefix!r} is below deck max {high}; IDs could be reused")
            )
    return findings


def _check_source(c: Card) -> list[dict]:
    src = c.fields.get("Source", "")
    if not src:
        return []
    if PASTED_RE.match(src):
        return [_finding("info", "SOURCE_UNVERIFIABLE", c, "pasted source; staleness cannot be checked")]
    m = SOURCE_RE.match(src)
    if not m:
        return [_finding("error", "SOURCE_MALFORMED", c,
                         "expected '<path>[#<locator>] sha256:<hash>' or 'pasted: <label>'")]
    path = (c.file.parent / m.group("path")).resolve()
    status, digest = section_hash(path, m.group("loc"))
    if status == "missing-file":
        return [_finding("warning", "SOURCE_MISSING", c, f"source file not found: {m.group('path')}")]
    if status == "missing-section":
        return [_finding("warning", "SOURCE_SECTION_MISSING", c, f"section not found: {m.group('loc')}")]
    if not digest.startswith(m.group("hash")[:HASH_LEN]):
        return [_finding("warning", "SOURCE_STALE", c, "source section changed since card was written")]
    return []


# --------------------------------------------------------------- mutation


def find_card(root: Path, card_id: str) -> Card:
    hits = [c for f in card_files(root) for c in parse_cards(f) if c.id == card_id]
    if not hits:
        raise FcdError(f"no card with ID {card_id}")
    if len(hits) > 1:
        raise FcdError(f"duplicate ID {card_id}; run check first")
    return hits[0]


def _rewrite_line(card: Card, field: str, new_line: str | None, insert_after: int | None = None):
    lines = card.file.read_text(encoding="utf-8").splitlines()
    if field in card.field_lines:
        idx = card.field_lines[field] - 1
        if new_line is None:
            raise FcdError("internal: cannot delete line")
        lines[idx] = new_line
    else:
        lines.insert(insert_after, new_line)
    card.file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def refresh_source(root: Path, card_id: str) -> str:
    c = find_card(root, card_id)
    src = c.fields.get("Source", "")
    m = SOURCE_RE.match(src)
    if not m:
        raise FcdError(f"{card_id}: Source is not file-backed; nothing to refresh")
    new = source_value(c.file, (c.file.parent / m.group("path")), m.group("loc"))
    _rewrite_line(c, "Source", f"Source: {new}")
    return new


def retire(root: Path, card_id: str, replaced_by: list[str], date: str) -> None:
    c = find_card(root, card_id)
    if c.retired:
        raise FcdError(f"{card_id} is already retired")
    value = f"{date}" + (f" replaced-by: {', '.join(replaced_by)}" if replaced_by else "")
    after = c.field_lines.get("Source") or c.field_lines.get("ID")
    _rewrite_line(c, "Retired", f"Retired: {value}", insert_after=after)


def promote(root: Path, draft: Path, target: Path, prefix: str | None) -> list[tuple[str, str]]:
    drafts_dir = root / DRAFTS_DIR
    if not inside(drafts_dir, draft) or not draft.is_file():
        raise FcdError("draft must be a file under drafts/")
    if not inside(root, target) or inside(drafts_dir, target) or target.suffix != ".md":
        raise FcdError("target must be a .md file under the deck root, outside drafts/")
    prefix = prefix or re.sub(r"[^a-z0-9]+", "-", target.stem.lower()).strip("-")
    cards = parse_cards(draft)
    if not cards:
        raise FcdError("draft contains no cards (expected '## Title' blocks)")
    for c in cards:
        cid = c.fields.get("ID", "pending")
        if cid not in ("", "pending"):
            raise FcdError(f"draft card '{c.title}' already has ID {cid}")
        if "Retired" in c.fields:
            raise FcdError(f"draft card '{c.title}' must not be retired")
        has_body = "C" in c.fields or ("Q" in c.fields and "A" in c.fields)
        if not has_body or not c.fields.get("Source"):
            raise FcdError(f"draft card '{c.title}' needs Q+A (or C) and Source")
    ids = allocate(root, prefix, len(cards))
    blocks = [render_card(c.title, i, c.fields) for c, i in zip(cards, ids)]
    body = "\n".join(blocks)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_text(encoding="utf-8").rstrip("\n")
        target.write_text(existing + "\n\n" + body, encoding="utf-8")
    else:
        title = target.stem.replace("-", " ").title()
        target.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    done = drafts_dir / "_promoted"
    done.mkdir(parents=True, exist_ok=True)
    draft.rename(done / draft.name)
    return [(c.title, i) for c, i in zip(cards, ids)]


# -------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="deck root (default: current directory)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("alloc", help="reserve N IDs for a prefix")
    p.add_argument("prefix")
    p.add_argument("-n", type=int, default=1)

    p = sub.add_parser("source", help="print a Source value with a fresh hash")
    p.add_argument("card_file")
    p.add_argument("source_file")
    p.add_argument("--locator", help="heading text or L<start>-<end>")

    p = sub.add_parser("check", help="validate the deck (read only)")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("refresh", help="recompute a card's source hash after review")
    p.add_argument("id")

    p = sub.add_parser("retire", help="mark a card retired")
    p.add_argument("id")
    p.add_argument("--replaced-by", default="", help="comma separated IDs")

    p = sub.add_parser("promote", help="move an approved draft batch into the deck")
    p.add_argument("draft")
    p.add_argument("target", help="deck file under the deck root, e.g. <topic>/<name>.md")
    p.add_argument("--prefix")

    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.cmd == "alloc":
            print("\n".join(allocate(root, args.prefix, args.n)))
        elif args.cmd == "source":
            print(source_value(Path(args.card_file), Path(args.source_file), args.locator))
        elif args.cmd == "check":
            findings = check_deck(root)
            if args.json:
                print(json.dumps(findings, indent=2))
            else:
                for f in findings:
                    where = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
                    print(f"{f['severity'].upper():7} {f['code']:22} {f['id'] or '-':24} {where}  {f['message']}")
                counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("error", "warning", "info")}
                print(f"-- {counts['error']} errors, {counts['warning']} warnings, {counts['info']} info")
            return 1 if any(f["severity"] == "error" for f in findings) else 0
        elif args.cmd == "refresh":
            print(refresh_source(root, args.id))
        elif args.cmd == "retire":
            ids = [s.strip() for s in args.replaced_by.split(",") if s.strip()]
            retire(root, args.id, ids, dt.date.today().isoformat())
            print(f"retired {args.id}")
        elif args.cmd == "promote":
            for title, cid in promote(root, Path(args.draft).resolve(), Path(args.target).resolve(), args.prefix):
                print(f"{cid}\t{title}")
    except FcdError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
