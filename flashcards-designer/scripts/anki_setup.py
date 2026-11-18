#!/usr/bin/env python3
"""Capture and restore the Anki styling that flashcards-designer cards rely on.

Narrow scope: the Basic and Cloze note types (fields, templates, CSS) and the
scheduler options of the parent deck. The snapshot ships with the skill, at
assets/anki-setup.json, so it is the default on every machine that has the skill.

  capture  read Anki, write the snapshot
  plan     read only: what restore would change on this Anki
  restore  apply the plan (requires --approved and --backup-dir)

Not covered: Anki preferences, add-ons, FSRS parameters, media, other note
types, and other decks' options. Use AnkiWeb sync or a collection backup for
those.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anki_sync  # noqa: E402
from anki_sync import SyncError, anki  # noqa: E402

DEFAULT_SNAPSHOT = Path(__file__).resolve().parent.parent / "assets" / "anki-setup.json"
DEFAULT_NOTETYPES = ["Basic", "Cloze"]
OPTION_KEYS = [
    "new_per_day",
    "reviews_per_day",
    "desired_retention",
    "maximum_review_interval",
    "learn_steps",
    "relearn_steps",
]
OPTION_FLAGS = {
    "new_per_day": "--new-per-day",
    "reviews_per_day": "--reviews-per-day",
    "desired_retention": "--desired-retention",
    "maximum_review_interval": "--maximum-review-interval",
    "learn_steps": "--learn-steps",
    "relearn_steps": "--relearn-steps",
}


# ---------------------------------------------------------------- reading


def _items(data) -> list[dict]:
    return data["items"] if isinstance(data, dict) and "items" in data else data


def read_notetype(name: str) -> dict:
    d = anki("notetype", "--name", name)
    templates = sorted(d["templates"].items(), key=lambda kv: kv[1].get("ord", 0))
    return {
        "kind": d["kind"],
        "fields": [f if isinstance(f, str) else f["name"] for f in d["fields"]],
        "templates": {n: {"front": t["Front"], "back": t["Back"]} for n, t in templates},
        "css": anki("notetype:css", "--notetype", name)["css"],
    }


def in_tree(name: str, parent: str) -> bool:
    return name == parent or name.startswith(parent + "::")


def read_deck_options(parent: str) -> dict:
    cfg = anki("deck:config", "--deck", parent)
    decks = _items(anki("decks"))
    others = [d["name"] for d in decks if d.get("config_id") == cfg["config_id"] and not in_tree(d["name"], parent)]
    return {
        "deck": parent,
        "preset_name": cfg["config_name"],
        "config": {k: cfg["config"][k] for k in OPTION_KEYS},
        "shared_with_other_decks": len(others),
    }


def capture(parent: str, names: list[str]) -> dict:
    return {
        "version": 1,
        "captured": dt.date.today().isoformat(),
        "notetypes": {n: read_notetype(n) for n in names},
        "deck_options": read_deck_options(parent),
    }


# ------------------------------------------------------------------- plan


@dataclass
class Step:
    action: str
    target: str
    detail: str = ""
    args: list[list[str]] = field(default_factory=list)  # anki commands to run, in order
    blocked: str = ""  # reason it will not run


def _short(s: str, n: int = 50) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "..."


def _steps_create(name: str, spec: dict) -> list[Step]:
    tnames = list(spec["templates"])
    first = spec["templates"][tnames[0]]
    args = ["notetype:create", "--name", name, "--kind", spec["kind"]]
    for f in spec["fields"]:
        args += ["--field", f]
    args += ["--template", tnames[0], "--front", first["front"], "--back", first["back"], "--css", spec["css"]]
    steps = [Step("CREATE", name, f"{spec['kind']}, fields {spec['fields']}", [args])]
    for t in tnames[1:]:
        steps.append(
            Step("TEMPLATE+", f"{name}/{t}", "", [["notetype:template:add", "--notetype", name, "--template", t,
                                                    "--front", spec["templates"][t]["front"], "--back", spec["templates"][t]["back"]]])
        )
    return steps


def _steps_update(name: str, spec: dict, cur: dict) -> tuple[list[Step], list[str]]:
    steps: list[Step] = []
    warnings: list[str] = []
    if cur["kind"] != spec["kind"]:
        return [Step("ERROR", name, f"kind is {cur['kind']}, snapshot has {spec['kind']}", blocked="kind mismatch")], warnings
    missing = [f for f in spec["fields"] if f not in cur["fields"]]
    for f in missing:
        steps.append(Step("FIELD+", f"{name}.{f}", "", [["notetype:field:add", "--notetype", name, "--field", f]]))
    if cur["fields"] + missing != spec["fields"]:
        warnings.append(f"{name}: field order differs from the snapshot ({cur['fields'] + missing} vs {spec['fields']}); not reordered")
    for t, want in spec["templates"].items():
        have = cur["templates"].get(t)
        if have is None:
            steps.append(Step("TEMPLATE+", f"{name}/{t}", "", [["notetype:template:add", "--notetype", name, "--template", t,
                                                                  "--front", want["front"], "--back", want["back"]]]))
        elif have != want:
            parts = [k for k in ("front", "back") if have[k] != want[k]]
            steps.append(Step("TEMPLATE~", f"{name}/{t}", f"{'+'.join(parts)} differs: {_short(have[parts[0]])!r} -> {_short(want[parts[0]])!r}",
                              [["notetype:template:edit", "--notetype", name, "--template", t,
                                "--front", want["front"], "--back", want["back"]]]))
    if cur["css"] != spec["css"]:
        steps.append(Step("CSS~", name, f"{len(cur['css'])} -> {len(spec['css'])} chars", [["notetype:css", "--notetype", name, "--set", spec["css"]]]))
    return steps, warnings


def _fmt(v) -> str:
    return ",".join(f"{x:g}" for x in v) if isinstance(v, list) else str(v)


def _steps_options(spec: dict, allow_shared: bool) -> list[Step]:
    parent = spec["deck"]
    decks = _items(anki("decks"))
    steps: list[Step] = []
    mine = next((d for d in decks if d["name"] == parent), None)
    if mine is None:
        steps.append(Step("DECK+", parent, "", [["deck:create", "--name", parent]]))
        preset_id = next((d["config_id"] for d in decks if d["name"] == "Default"), 1)
        shared = sum(1 for d in decks if d.get("config_id") == preset_id)
        current = None
    else:
        cfg = anki("deck:config", "--deck", parent)
        shared = sum(1 for d in decks if d.get("config_id") == cfg["config_id"] and not in_tree(d["name"], parent))
        current = cfg["config"]
    diff = {k: v for k, v in spec["config"].items() if current is None or current.get(k) != v}
    if not diff:
        return steps
    args = ["deck:config:set", "--deck", parent]
    for k, v in diff.items():
        args += [OPTION_FLAGS[k], _fmt(v)]
    detail = ", ".join(f"{k}={_fmt(v)}" for k, v in diff.items())
    blocked = ""
    if shared and not allow_shared:
        blocked = f"preset is shared with {shared} other deck(s); rerun with --allow-shared-options to change it for all of them"
    steps.append(Step("OPTIONS~", parent, detail, [args], blocked))
    return steps


def make_plan(snap: dict, allow_shared: bool) -> tuple[list[Step], list[str]]:
    existing = {n["name"] for n in _items(anki("notetypes"))}
    steps: list[Step] = []
    warnings: list[str] = []
    for name, spec in snap["notetypes"].items():
        if name not in existing:
            steps += _steps_create(name, spec)
        else:
            s, w = _steps_update(name, spec, read_notetype(name))
            steps += s
            warnings += w
    if snap.get("deck_options"):
        steps += _steps_options(snap["deck_options"], allow_shared)
    return steps, warnings


def format_plan(steps: list[Step], warnings: list[str]) -> str:
    runnable = sum(1 for s in steps if not s.blocked)
    lines = [f"{runnable} change(s) to apply, {len(steps) - runnable} blocked, {len(warnings)} warning(s)"]
    for s in steps:
        lines.append(f"  {s.action:9} {s.target}" + (f"  {s.detail}" if s.detail else ""))
        if s.blocked:
            lines.append(f"            BLOCKED: {s.blocked}")
    lines += [f"  WARNING   {w}" for w in warnings]
    return "\n".join(lines)


def apply_steps(steps: list[Step]) -> list[str]:
    done = []
    for s in steps:
        if s.blocked:
            done.append(f"skipped {s.action} {s.target}")
            continue
        for a in s.args:
            anki(*a)
        done.append(f"done    {s.action} {s.target}")
    return done


# -------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT), help="snapshot file (default: the skill's assets/anki-setup.json)")
    ap.add_argument("--parent", default="anki::repo", help="parent Anki deck whose options are captured")
    ap.add_argument("--notetype", action="append", help="note type to include (repeatable; default Basic and Cloze)")
    ap.add_argument("--col", help="collection file to use instead of the default (for testing on a copy)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("capture", help="write the snapshot from this Anki")
    p = sub.add_parser("plan", help="show what restore would change (read only)")
    p.add_argument("--allow-shared-options", action="store_true")
    p = sub.add_parser("restore", help="apply the snapshot to this Anki")
    p.add_argument("--allow-shared-options", action="store_true",
                   help="allow changing a scheduler preset shared with other decks")
    p.add_argument("--approved", action="store_true")
    p.add_argument("--backup-dir")
    args = ap.parse_args(argv)

    if args.col:
        anki_sync.COL = args.col
    path = Path(args.snapshot).resolve()
    try:
        if args.cmd == "capture":
            snap = capture(args.parent, args.notetype or DEFAULT_NOTETYPES)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            opt = snap["deck_options"]
            print(f"wrote {path}")
            print(f"note types: {', '.join(snap['notetypes'])}; deck options of {opt['deck']} "
                  f"(preset {opt['preset_name']!r}, shared with {opt['shared_with_other_decks']} other deck(s))")
            return 0
        if not path.is_file():
            raise SyncError(f"no snapshot at {path}; run capture on the source machine first")
        snap = json.loads(path.read_text(encoding="utf-8"))
        steps, warnings = make_plan(snap, args.allow_shared_options)
        print(format_plan(steps, warnings))
        if args.cmd == "plan":
            return 0
        if not args.approved or not args.backup_dir:
            raise SyncError("restore needs --approved and --backup-dir; show the plan to the user first")
        if not any(not s.blocked for s in steps):
            print("nothing to do")
            return 0
        print(f"backup: {anki_sync.preflight(Path(args.backup_dir))}")
        print("\n".join(apply_steps(steps)))
        after, _ = make_plan(snap, args.allow_shared_options)
        left = [s for s in after if not s.blocked]
        print("verify: " + ("plan is empty" if not left else "NOT EMPTY\n" + format_plan(after, [])))
        return 0 if not left else 1
    except (SyncError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
