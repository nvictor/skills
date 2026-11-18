#!/usr/bin/env python3
"""Capture and restore the Anki styling that flashcards-designer cards rely on.

Narrow scope: the Basic and Cloze note types (fields, templates, CSS) and the
scheduler options of the parent deck. The snapshot ships with the skill, at
assets/anki-setup.json, so it is the default on every machine that has the skill.

  doctor   read only: check this machine and say how to fix what is wrong
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
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anki_sync  # noqa: E402
import fcd  # noqa: E402
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
    if snap.get("deck_options"):
        anki_sync.require_root_deck(snap["deck_options"]["deck"])
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


# ----------------------------------------------------------------- doctor


@dataclass
class Check:
    level: str  # OK | WARN | FAIL
    name: str
    message: str
    fix: str = ""


def run_doctor(snapshot: Path, root: Path | None, parent: str) -> list[Check]:
    out: list[Check] = []
    ok = lambda n, m: out.append(Check("OK", n, m))  # noqa: E731
    bad = lambda n, m, f="": out.append(Check("FAIL", n, m, f))  # noqa: E731
    warn = lambda n, m, f="": out.append(Check("WARN", n, m, f))  # noqa: E731

    if sys.version_info >= (3, 9):
        ok("python", sys.version.split()[0])
    else:
        bad("python", f"{sys.version.split()[0]} is too old", "install Python 3.9 or newer")
    try:
        anki_sync.require_root_deck(parent)
        ok("parent deck", parent)
    except SyncError as e:
        bad("parent deck", str(e), "pass --parent anki::repo")
    if not shutil.which(anki_sync.ANKI):
        bad("anki cli", f"`{anki_sync.ANKI}` not found on PATH", "uv tool install anki-cli")
        return out
    try:
        st = anki("status")
    except SyncError as e:
        bad("anki status", str(e), "open Anki once so it creates a profile, quit it, then retry")
        return out
    ok("anki cli", f"backend={st.get('backend')}, profile={st.get('profile')}")
    if st.get("backend") == "direct" and not anki_sync.COL and anki_sync.anki_running():
        warn("anki running", "Anki is open; writes are refused while it is open (direct backend)", "quit Anki before sync or restore")
    else:
        ok("anki closed", "writes are allowed")
    if not snapshot.is_file():
        bad("snapshot", f"missing {snapshot}", "run `capture` on a machine that has your setup, then commit it")
        return out
    snap = json.loads(snapshot.read_text(encoding="utf-8"))
    try:
        steps, warnings = make_plan(snap, allow_shared=True)
    except SyncError as e:
        bad("snapshot", str(e))
        return out
    note_steps = [s for s in steps if not s.action.startswith(("OPTIONS", "DECK"))]
    option_steps = [s for s in steps if s.action.startswith(("OPTIONS", "DECK"))]
    if note_steps:
        bad("note types", f"{len(note_steps)} difference(s) from the snapshot: " + ", ".join(f"{s.action} {s.target}" for s in note_steps[:6]),
            "python3 scripts/anki_setup.py plan, then restore --approved --backup-dir <dir> --allow-shared-options")
    else:
        ok("note types", "Basic and Cloze match the snapshot")
    if option_steps:
        warn("deck options", ", ".join(f"{s.action} {s.target}" for s in option_steps),
             "restore --approved --backup-dir <dir> --allow-shared-options (changes the shared preset)")
    else:
        ok("deck options", f"{parent} matches the snapshot")
    for w in warnings:
        warn("snapshot", w)
    if root is not None:
        if not root.is_dir():
            bad("deck root", f"{root} does not exist", f"mkdir -p {root}  (use a company-approved repo for work decks)")
        else:
            findings = fcd.check_deck(root)
            errors = [f for f in findings if f["severity"] == "error"]
            n = sum(len(fcd.parse_cards(f)) for f in fcd.card_files(root))
            if errors:
                bad("deck root", f"{n} card(s), {len(errors)} error(s)", f"python3 scripts/fcd.py --root {root} check")
            else:
                ok("deck root", f"{n} card(s), 0 errors")
    return out


def format_doctor(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        lines.append(f"{c.level:5} {c.name}: {c.message}")
        if c.fix:
            lines.append(f"      fix: {c.fix}")
    fails = sum(1 for c in checks if c.level == "FAIL")
    lines.append("ready" if not fails else f"{fails} problem(s) to fix")
    return "\n".join(lines)


# -------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT), help="snapshot file (default: the skill's assets/anki-setup.json)")
    ap.add_argument("--parent", default="anki::repo", help="parent Anki deck whose options are captured")
    ap.add_argument("--notetype", action="append", help="note type to include (repeatable; default Basic and Cloze)")
    ap.add_argument("--col", help="collection file to use instead of the default (for testing on a copy)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("doctor", help="check this machine (read only)")
    p.add_argument("--root", help="also check this deck root")
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
        if args.cmd == "doctor":
            checks = run_doctor(path, Path(args.root).resolve() if args.root else None, args.parent)
            print(format_doctor(checks))
            return 1 if any(c.level == "FAIL" for c in checks) else 0
        anki_sync.require_root_deck(args.parent)
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
