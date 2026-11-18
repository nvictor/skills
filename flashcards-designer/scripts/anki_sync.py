#!/usr/bin/env python3
"""One-way sync of a flashcards-designer deck to Anki through the `anki` CLI.

Markdown owns card content. Anki owns review history. Notes are matched by the
`ID` field, which must exist on the Basic and Cloze note types.

  plan   read only: what would change
  apply  perform the plan (requires --approved and --backup-dir)

Mapping:
  Q/A card -> Basic: Front=Q, Back=A + source line, ID
  C card   -> Cloze: Text=C, Back Extra=X (if any) + source line, ID
  Deck     -> <parent>::<folder path>, nested (core/sre/x.md -> anki::repo::core::sre)
  Tags     -> fc and the folder path as one hierarchical tag (core::sre)
  Retired cards are suspended.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fcd  # noqa: E402

ANKI = os.environ.get("ANKI_CLI", "anki")
COL = os.environ.get("ANKI_COL")  # optional collection file, e.g. a test copy
SUSPENDED_QUEUE = -1
ROOT_DECK = "anki"  # every deck this skill creates lives under this deck
REQUIRED_FIELDS = {"basic": ["Front", "Back", "ID"], "cloze": ["Text", "Back Extra", "ID"]}


class SyncError(Exception):
    pass


def require_root_deck(parent: str) -> None:
    if parent != ROOT_DECK and not parent.startswith(ROOT_DECK + "::"):
        raise SyncError(f"parent deck {parent!r} must be {ROOT_DECK!r} or a deck under it ({ROOT_DECK}::...)")


# ---------------------------------------------------------------- Anki CLI


def anki(*args: str) -> dict:
    cmd = [ANKI, "--format", "json", *(["--col", COL] if COL else []), *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        out = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        raise SyncError(f"anki {args[0]}: unparseable output: {r.stdout[:200]!r} {r.stderr[:200]!r}")
    if r.returncode != 0 or not out.get("ok", False):
        err = out.get("error", {}).get("message") or r.stderr.strip() or "unknown error"
        raise SyncError(f"anki {' '.join(args[:2])}: {err}")
    return out["data"]


def anki_running() -> bool:
    return subprocess.run(["pgrep", "-x", "Anki"], capture_output=True).returncode == 0


# --------------------------------------------------------------- rendering

_FENCE = re.compile(r"^```[^\n]*\n(.*?)\n?^```[ \t]*$", re.MULTILINE | re.DOTALL)


def _inline(text: str) -> str:
    esc = html.escape(text, quote=False)
    esc = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", esc)
    return esc.replace("\n", "<br>")


def render_html(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _FENCE.finditer(text):
        before = text[pos : m.start()].strip("\n")
        if before:
            out.append(_inline(before))
        out.append(f"<pre><code>{html.escape(m.group(1), quote=False)}</code></pre>")
        pos = m.end()
    rest = text[pos:].strip("\n")
    if rest:
        out.append(_inline(rest))
    value = "".join(out)
    # The CLI treats an argument starting with "--" as a flag.
    return "<span></span>" + value if value.startswith("--") else value


def source_label(src: str) -> str:
    m = fcd.SOURCE_RE.match(src)
    if m:
        name = Path(m.group("path")).name
        return name + (f"#{m.group('loc')}" if m.group("loc") else "")
    return re.sub(r"^pasted:\s*", "", src)


# ------------------------------------------------------------------ model


@dataclass
class Desired:
    id: str
    kind: str  # basic | cloze
    deck: str
    tags: list[str]
    retired: bool
    fields: dict[str, str]
    title: str = ""


@dataclass
class Existing:
    note: int
    notetype: str
    cards: list[dict] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)


def desired_notes(root: Path, parent: str) -> list[Desired]:
    errors = [f for f in fcd.check_deck(root) if f["severity"] == "error"]
    if errors:
        raise SyncError("deck has errors; run fcd.py check and fix them first")
    out: list[Desired] = []
    for f in fcd.card_files(root):
        parts = f.relative_to(root).parts
        folders = parts[:-1]
        deck = "::".join([parent, *folders])
        tag = "::".join(re.sub(r"\s+", "_", p) for p in folders)  # hierarchical tag, no spaces
        for c in fcd.parse_cards(f):
            src = f'<small>{html.escape(source_label(c.fields["Source"]), quote=False)}</small>'
            if "C" in c.fields:
                extra = render_html(c.fields["X"]) + "<br>" if c.fields.get("X") else ""
                kind, fields = "cloze", {
                    "Text": render_html(c.fields["C"]),
                    "Back Extra": extra + src,
                    "ID": c.id,
                }
            else:
                kind, fields = "basic", {
                    "Front": render_html(c.fields["Q"]),
                    "Back": render_html(c.fields["A"]) + "<br>" + src,
                    "ID": c.id,
                }
            out.append(Desired(c.id, kind, deck, ["fc"] + ([tag] if tag else []), c.retired, fields, c.title))
    return out


def notetype_fields(name: str) -> list[str]:
    d = anki("notetype", "--name", name)
    return [f if isinstance(f, str) else f["name"] for f in d["fields"]]


def check_notetypes(names: dict[str, str]) -> None:
    for kind, nt in names.items():
        have = notetype_fields(nt)
        missing = [f for f in REQUIRED_FIELDS[kind] if f not in have]
        if missing:
            raise SyncError(f"note type {nt!r} lacks field(s) {missing}; add them with `anki notetype:field:add`")


def dump_existing(parent: str, names: dict[str, str]) -> dict[str, Existing]:
    data = anki("cards", "--query", f'deck:"{parent}"', "--limit", "0")
    field_names = {nt: notetype_fields(nt) for nt in set(names.values())}
    notes: dict[int, Existing] = {}
    for item in data["items"]:
        nt = item["notetype_name"]
        if nt not in field_names:
            continue
        e = notes.setdefault(item["note"], Existing(item["note"], nt, [], dict(zip(field_names[nt], item["fields"]))))
        e.cards.append({"cardId": item["cardId"], "queue": item["queue"], "reps": item.get("reps", 0)})
    by_id: dict[str, Existing] = {}
    for e in notes.values():
        cid = e.fields.get("ID", "").strip()
        if not cid:
            continue
        if cid in by_id:
            raise SyncError(f"duplicate ID {cid} in Anki (notes {by_id[cid].note}, {e.note}); resolve before syncing")
        by_id[cid] = e
    return by_id


# ------------------------------------------------------------------- plan


@dataclass
class Plan:
    adds: list[Desired] = field(default_factory=list)
    updates: list[tuple[Desired, Existing, dict]] = field(default_factory=list)
    suspends: list[tuple[Desired, Existing]] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    unchanged: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not (self.adds or self.updates or self.suspends)


def make_plan(desired: list[Desired], existing: dict[str, Existing], names: dict[str, str]) -> Plan:
    plan = Plan()
    ids = set()
    for d in desired:
        ids.add(d.id)
        e = existing.get(d.id)
        if d.retired:
            if e and any(c["queue"] != SUSPENDED_QUEUE for c in e.cards):
                plan.suspends.append((d, e))
            continue
        if e is None:
            plan.adds.append(d)
        elif e.notetype != names[d.kind]:
            plan.errors.append(f"{d.id}: card kind changed ({e.notetype} -> {names[d.kind]}); retire and recreate it")
        else:
            diff = {k: (e.fields.get(k, ""), v) for k, v in d.fields.items() if k != "ID" and e.fields.get(k, "") != v}
            if diff:
                plan.updates.append((d, e, diff))
            else:
                plan.unchanged += 1
    plan.orphans = sorted(set(existing) - ids)
    return plan


def _short(s: str, n: int = 60) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "..."


def format_plan(plan: Plan) -> str:
    lines = [
        f"add {len(plan.adds)}, update {len(plan.updates)}, suspend {len(plan.suspends)}, "
        f"unchanged {plan.unchanged}, orphans {len(plan.orphans)}, errors {len(plan.errors)}"
    ]
    for d in plan.adds:
        lines.append(f"  ADD      {d.id:28} -> {d.deck} ({d.kind})")
    for d, e, diff in plan.updates:
        lines.append(f"  UPDATE   {d.id:28} note {e.note}, reps {sum(c['reps'] for c in e.cards)}; reset candidate if the question or answer meaning changed")
        for k, (old, new) in diff.items():
            lines.append(f"             {k}: {_short(old)!r} -> {_short(new)!r}")
    for d, e in plan.suspends:
        lines.append(f"  SUSPEND  {d.id:28} note {e.note}")
    for o in plan.orphans:
        lines.append(f"  ORPHAN   {o} (in Anki, not in the deck; left alone)")
    for err in plan.errors:
        lines.append(f"  ERROR    {err}")
    return "\n".join(lines)


# ------------------------------------------------------------------ apply


def preflight(backup_dir: Path) -> Path:
    st = anki("status")
    if not COL and st.get("backend") == "direct" and anki_running():
        raise SyncError("Anki is running and the backend is direct; quit Anki first")
    src = Path(COL or st["collection"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"{src.stem}-{dt.datetime.now():%Y%m%d-%H%M%S}{src.suffix}"
    shutil.copy2(src, dest)
    return dest


def apply_plan(plan: Plan, names: dict[str, str], resets: list[str], summary: list[str]) -> None:
    for deck in sorted({d.deck for d in plan.adds}):
        anki("deck:create", "--name", deck)
    groups: dict[tuple[str, str], list[Desired]] = {}
    for d in plan.adds:
        groups.setdefault((d.deck, d.kind), []).append(d)
    for (deck, kind), items in groups.items():
        # Anki requires every field of the note type, including ones we do not manage (e.g. Speak).
        blank = {name: "" for name in notetype_fields(names[kind])}
        payload = [{**blank, **d.fields, "tags": d.tags} for d in items]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(payload, fh)
        try:
            res = anki("note:bulk", "--deck", deck, "--notetype", names[kind], "--file", fh.name)
        finally:
            os.unlink(fh.name)
        for d, nid in zip(items, res["ids"]):
            summary.append(f"{'FAILED ' if nid is None else 'added  '} {d.id}")
    for d, e, diff in plan.updates:
        args = ["note:edit", "--id", str(e.note)]
        for k, (_, new) in diff.items():
            args += [f"--{k}", new]
        anki(*args)
        summary.append(f"updated {d.id}")
    for d, e in plan.suspends:
        for c in e.cards:
            if c["queue"] != SUSPENDED_QUEUE:
                anki("card:suspend", "--id", str(c["cardId"]))
        summary.append(f"suspended {d.id}")
    updated = {d.id: e for d, e, _ in plan.updates}
    for rid in resets:
        if rid not in updated:
            summary.append(f"skipped reset {rid}: not an updated card")
            continue
        for c in updated[rid].cards:
            anki("card:reset", "--id", str(c["cardId"]))
        summary.append(f"reset   {rid}")


# -------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="deck root")
    ap.add_argument("--parent", default="anki::repo", help="parent Anki deck (default: anki::repo)")
    ap.add_argument("--basic-notetype", default="Basic")
    ap.add_argument("--cloze-notetype", default="Cloze")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="show what would change (read only)")
    p = sub.add_parser("apply", help="perform the plan")
    p.add_argument("--approved", action="store_true", help="the user approved this plan")
    p.add_argument("--backup-dir", required=True, help="where to copy the collection before writing")
    p.add_argument("--reset", default="", help="comma separated card IDs whose progress to reset (updated cards only)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    names = {"basic": args.basic_notetype, "cloze": args.cloze_notetype}
    try:
        require_root_deck(args.parent)
        check_notetypes(names)
        desired = desired_notes(root, args.parent)
        plan = make_plan(desired, dump_existing(args.parent, names), names)
        print(format_plan(plan))
        if plan.errors:
            return 1
        if args.cmd == "plan":
            return 0
        if not args.approved:
            raise SyncError("apply needs --approved; show the plan to the user first")
        if plan.empty and not args.reset:
            print("nothing to do")
            return 0
        backup = preflight(Path(args.backup_dir))
        print(f"backup: {backup}")
        summary: list[str] = []
        apply_plan(plan, names, [s.strip() for s in args.reset.split(",") if s.strip()], summary)
        print("\n".join(summary))
        after = make_plan(desired, dump_existing(args.parent, names), names)
        print("verify: " + ("plan is empty" if after.empty else "NOT EMPTY\n" + format_plan(after)))
        return 0 if after.empty and not any(s.startswith("FAILED") for s in summary) else 1
    except (SyncError, fcd.FcdError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
