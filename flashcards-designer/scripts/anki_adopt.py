#!/usr/bin/env python3
"""Adopt an existing Anki deck into a flashcards-designer deck, keeping review history.

History lives on the Anki cards. This script never recreates them: it drafts
Markdown from the existing notes, and after the draft is promoted it writes the
new card ID into each original note and moves the cards under the sync parent.

  draft  read only: write drafts/<file>.md from the notes of one Anki deck
  link   plan, or with --approved write IDs into the notes and move the cards

Flow:
  1. anki_adopt.py draft --deck anki::core::sre --folder core/sre --prefix sre
  2. user reviews the draft, then: fcd.py promote <draft> core/sre/sre.md --prefix sre
  3. anki_adopt.py link --deck anki::core::sre --folder core/sre            (plan)
     anki_adopt.py link --deck anki::core::sre --folder core/sre --approved --backup-dir <dir>
  4. anki_sync.py plan   (expect updates only, no adds)

  speak  for cards linked before S: existed: anki_adopt.py speak --folder <a/b> [--write]

Cloze Back Extra becomes the optional X: field, Basic Speak the optional S: field. Only Basic and Cloze notes whose text survives a Markdown round trip unchanged
are drafted. Everything else is listed as skipped and stays untouched in Anki.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anki_sync  # noqa: E402
import fcd  # noqa: E402
from anki_sync import SyncError, anki, notetype_fields, render_html  # noqa: E402

TITLE_PREFIX = "anki-note-"
TITLE_RE = re.compile(rf"^{TITLE_PREFIX}(\d+)$")
# Anki field -> card field. Optional fields may be empty.
FIELD_MAP = {"basic": {"Front": "Q", "Back": "A", "Speak": "S"}, "cloze": {"Text": "C", "Back Extra": "X"}}
OPTIONAL = {"Back Extra", "Speak"}
KINDS = {"Basic": "basic", "Cloze": "cloze"}


@dataclass
class Note:
    id: int
    kind: str
    fields: dict[str, str]
    cards: list[dict]


def to_markdown(h: str) -> str:
    return html.unescape(re.sub(r"<br\s*/?>", "\n", h))


def target_deck(parent: str, folder: str) -> str:
    parts = [p for p in re.split(r"[/:]+", folder) if p]
    return "::".join([parent, *parts])


def fetch_notes(deck: str, names: dict[str, str]) -> list[Note]:
    """Notes with a card directly in `deck` (subdecks excluded)."""
    data = anki("cards", "--query", f'deck:"{deck}" -deck:"{deck}::*"', "--limit", "0")
    fields = {nt: notetype_fields(nt) for nt in set(names.values())}
    notes: dict[int, Note] = {}
    for it in data["items"]:
        nt = it["notetype_name"]
        if nt not in fields:
            continue
        n = notes.setdefault(it["note"], Note(it["note"], KINDS[nt], dict(zip(fields[nt], it["fields"])), []))
        n.cards.append({"cardId": it["cardId"], "deck": it["deckName"]})
    return sorted(notes.values(), key=lambda n: n.id)


_TAG_RE = re.compile(r"<(?!br\s*/?>)[^>]*>", re.IGNORECASE)


def render_only_change(raw: str) -> bool:
    """True when sync would only reformat plain text: no markup in the field except <br>."""
    return not _TAG_RE.search(raw)


_STRIPPABLE_RE = re.compile(r"</?(?:div|span|strong|b|em|i|u)(?:\s[^>]*)?>", re.IGNORECASE)


def strip_markup(raw: str) -> str:
    """Drop formatting wrappers (div, span, bold, italic, underline). Block ends become <br>."""
    out = re.sub(r"(?:</div\s*>\s*)+", "<br>", raw, flags=re.IGNORECASE)
    out = _STRIPPABLE_RE.sub("", out)
    out = out.replace("&nbsp;", " ")
    return re.sub(r"(?:<br\s*/?>)+$", "", out.strip(), flags=re.IGNORECASE)


def adoptable(n: Note, accept_render: bool = False, strip: bool = False) -> tuple[dict[str, str] | None, str]:
    """Return (markdown fields keyed Q/A/C, "") or (None, reason).

    accept_render also adopts fields that only differ because sync renders
    plain text differently (for example `code` in backticks becomes <code>).
    strip also drops formatting wrappers (div, span, bold, italic, underline) first. Other
    markup (images, links, lists, tables, sound) still skips the note. Implies accept_render.
    """
    accept_render = accept_render or strip
    if n.fields.get("ID", "").strip():
        return None, "already has an ID"
    out: dict[str, str] = {}
    for anki_field, md_field in FIELD_MAP[n.kind].items():
        raw = n.fields.get(anki_field, "")
        if strip:
            raw = strip_markup(raw)
        md = to_markdown(raw).strip("\n")
        if not md.strip():
            if anki_field in OPTIONAL:
                continue
            return None, f"{anki_field} is empty"
        if render_html(md) != raw and not (accept_render and render_only_change(raw)):
            return None, f"{anki_field} would change on sync (markup, media, or whitespace)"
        out[md_field] = md
    return out, ""


def draft_block(n: Note, md: dict[str, str]) -> str:
    lines = [f"## {TITLE_PREFIX}{n.id}", "", "ID: pending"]
    lines += [f"{k}: {fcd.escape_value(v)}" for k, v in md.items()]
    return "\n".join(lines) + "\n"


def survives_parse(block: str, md: dict[str, str]) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.md"
        p.write_text(block, encoding="utf-8")
        cards = fcd.parse_cards(p)
    return len(cards) == 1 and all(cards[0].fields.get(k, "").strip() == v.strip() for k, v in md.items())


def build_draft(notes: list[Note], accept_render: bool = False, strip: bool = False) -> tuple[str, list[int], list[tuple[int, str]]]:
    blocks: list[str] = []
    ids: list[int] = []
    skipped: list[tuple[int, str]] = []
    for n in notes:
        md, why = adoptable(n, accept_render, strip)
        if md is None:
            skipped.append((n.id, why))
            continue
        block = draft_block(n, md)
        if not survives_parse(block, md):
            skipped.append((n.id, "text clashes with the card file syntax"))
            continue
        blocks.append(block)
        ids.append(n.id)
    return "\n".join(blocks), ids, skipped


def cmd_draft(args, names) -> int:
    notes = fetch_notes(args.deck, names)
    body, ids, skipped = build_draft(notes, args.accept_render, args.strip_markup)
    if not ids:
        print(f"no adoptable notes in {args.deck!r} ({len(skipped)} skipped)")
        return 1
    root = Path(args.root).resolve()
    out = root / fcd.DRAFTS_DIR / f"import-{args.prefix}.md"
    if out.exists():
        raise SyncError(f"{out} already exists; promote or remove it first")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"drafted {len(ids)} of {len(notes)} notes -> {out}")
    for nid, why in skipped:
        print(f"  SKIP {nid}: {why}")
    folder = [p for p in re.split(r"[/:]+", args.folder) if p]
    target = root.joinpath(*folder, f"{args.prefix}.md")
    print(f"next: python3 scripts/fcd.py --root {root} promote {out} {target} --prefix {args.prefix}")
    return 0


# ------------------------------------------------------------------- link


def promoted(root: Path, folder: str) -> dict[int, str]:
    """note id -> card ID, for imported cards promoted into `folder`."""
    want = tuple(p for p in re.split(r"[/:]+", folder) if p)
    out: dict[int, str] = {}
    for f in fcd.card_files(root):
        if f.relative_to(root).parts[:-1] != want:
            continue
        for c in fcd.parse_cards(f):
            m = TITLE_RE.match(c.title)
            cid = c.fields.get("ID", "")
            if m and cid not in ("", "pending") and not c.retired:
                out[int(m.group(1))] = cid
    return out


def plan_link(
    notes: list[Note], ids: dict[int, str], dest: str, linked: set[str] | None = None
) -> tuple[list[tuple[Note, str]], list[str]]:
    """`linked` holds card IDs already present in Anki; those need no work and are not errors."""
    linked = linked or set()
    by_note = {n.id: n for n in notes}
    todo: list[tuple[Note, str]] = []
    problems: list[str] = []
    for nid, cid in sorted(ids.items()):
        n = by_note.get(nid)
        if n is None and cid in linked:
            continue
        if n is None:
            problems.append(f"{cid}: note {nid} not found directly in the source deck")
        elif n.fields.get("ID", "").strip() == cid:
            continue  # already linked, nothing to write
        elif n.fields.get("ID", "").strip() not in ("", cid):
            problems.append(f"{cid}: note {nid} already has ID {n.fields['ID']!r}")
        else:
            todo.append((n, cid))
    return todo, problems


def cmd_link(args, names) -> int:
    root = Path(args.root).resolve()
    anki_sync.require_root_deck(args.parent)
    dest = target_deck(args.parent, args.folder)
    ids = promoted(root, args.folder)
    if not ids:
        raise SyncError(f"no promoted import cards (titles {TITLE_PREFIX}<note id>) under {args.folder!r}")
    linked = set(anki_sync.dump_existing(args.parent, names))
    todo, problems = plan_link(fetch_notes(args.deck, names), ids, dest, linked)
    moves = sum(1 for n, _ in todo for c in n.cards if c["deck"] != dest)
    print(f"set ID on {len(todo)} notes, move {moves} cards to {dest}, problems {len(problems)}")
    for n, cid in todo:
        print(f"  LINK {cid:12} note {n.id}, {len(n.cards)} cards")
    for p in problems:
        print(f"  ERROR {p}")
    if problems:
        return 1
    if not args.approved:
        return 0
    if not args.backup_dir:
        raise SyncError("link needs --backup-dir with --approved")
    print(f"backup: {anki_sync.preflight(Path(args.backup_dir))}")
    if moves:
        anki("deck:create", "--name", dest)
    for n, cid in todo:
        anki("note:edit", "--id", str(n.id), "--ID", cid)
        for c in n.cards:
            if c["deck"] != dest:
                anki("card:move", "--id", str(c["cardId"]), "--deck", dest)
    print(f"linked {len(todo)} notes. Now run anki_sync.py --root {root} --parent {args.parent} plan")
    return 0


# ------------------------------------------------------------ speak backfill


def cmd_speak(args, names) -> int:
    """Copy non-empty Speak values from Anki into S: lines of already-linked Basic cards."""
    root = Path(args.root).resolve()
    want = tuple(p for p in re.split(r"[/:]+", args.folder) if p)
    existing = anki_sync.dump_existing(args.parent, names)
    todo = skipped = 0
    for f in fcd.card_files(root):
        if f.relative_to(root).parts[:-1] != want:
            continue
        inserts: list[tuple[int, str]] = []
        for c in fcd.parse_cards(f):
            e = existing.get(c.id or "")
            if c.retired or "C" in c.fields or "S" in c.fields or e is None:
                continue
            raw = e.fields.get("Speak", "")
            if not raw.strip():
                continue
            md = to_markdown(raw).strip("\n")
            if render_html(md) != raw:
                skipped += 1
                print(f"  SKIP {c.id}: Speak would change on sync")
                continue
            inserts.append((c.field_lines["Source"] - 1, f"S: {fcd.escape_value(md)}"))
        if inserts and args.write:
            lines = f.read_text(encoding="utf-8").splitlines()
            for idx, line in sorted(inserts, reverse=True):
                lines.insert(idx, line)
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
        todo += len(inserts)
    print(f"{'wrote' if args.write else 'would add'} S: to {todo} cards, skipped {skipped}")
    if todo and not args.write:
        print("rerun with --write to edit the card files (Git only; Anki is not changed)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="deck root")
    ap.add_argument("--basic-notetype", default="Basic")
    ap.add_argument("--cloze-notetype", default="Cloze")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("draft", "link"):
        p = sub.add_parser(name)
        p.add_argument("--deck", required=True, help="existing Anki deck, e.g. anki::core::sre")
        p.add_argument("--folder", required=True, help="target folder in the deck root, e.g. core/sre")
    d = sub.choices["draft"]
    d.add_argument("--prefix", required=True, help="ID prefix, also the draft and target file name")
    d.add_argument("--accept-render", action="store_true",
                   help="also adopt plain-text fields that sync would render differently (backticks become <code>)")
    d.add_argument("--strip-markup", action="store_true",
                   help="drop div, span, bold, italic, underline wrappers (formatting is lost); implies --accept-render")
    s = sub.add_parser("speak", help="copy Speak values from Anki into S: lines (edits card files only)")
    s.add_argument("--folder", required=True)
    s.add_argument("--parent", default="anki::repo")
    s.add_argument("--write", action="store_true")
    k = sub.choices["link"]
    k.add_argument("--parent", default="anki::repo", help="sync parent deck (default: anki::repo)")
    k.add_argument("--approved", action="store_true")
    k.add_argument("--backup-dir")
    args = ap.parse_args(argv)
    names = {"basic": args.basic_notetype, "cloze": args.cloze_notetype}
    try:
        anki_sync.check_notetypes(names)
        return {"draft": cmd_draft, "link": cmd_link, "speak": cmd_speak}[args.cmd](args, names)
    except (SyncError, fcd.FcdError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
