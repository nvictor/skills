# Anki Adapter

One-way sync from the deck (Git) to Anki, done by `scripts/anki_sync.py`. Markdown owns card content. Anki owns review history. Edits made in Anki are not pulled back, so tell the user to edit cards in the repository.

The CLI is `anki` (package anki-cli 0.2.0, installed as a uv tool). It is not named `anki-cli`. Re-verify the behavior below after upgrading it.

## Model

Existing note types are used. No new note type is created.

| Deck card | Note type | Fields |
| --- | --- | --- |
| `Q:` and `A:` | `Basic` | `Front` = Q, `Back` = A plus a small source line, `ID` = card ID. Other fields (such as `Speak`) are left empty. |
| `C:` (and optional `X:`) | `Cloze` | `Text` = C, `Back Extra` = X (if any) then the source line, `ID` = card ID. |

- Both note types need an `ID` field. Add it once with `anki notetype:field:add --notetype Basic --field ID` (and `Cloze`). This forces a one-time full sync with AnkiWeb.
- Notes are matched by the `ID` field, never by question text.
- Decks: `<parent>::<folder path>`, nested to any depth, with parent `anki::repo` by default (`--parent`). `core/sre/x.md` goes to `anki::repo::core::sre`. Cards at the deck root go in the parent deck. Every deck this skill creates must be `anki` or under `anki::`; the scripts refuse any other parent.
- Tags: `fc` and the folder path as one hierarchical tag (`core::sre`). Anki matches `tag:core` against child tags too. Spaces in folder names become `_` in the tag. Tags are set on add only.
- Content is rendered to HTML: escaped, newlines as `<br>`, inline code as `<code>`, fenced code as `<pre><code>`. The source line shows the file name and section, not the hash.
- Retired cards are suspended, never deleted, so history is kept.
- Orphans (notes in the target deck whose ID is not in the deck) are reported and left alone.

## Commands

```bash
python3 scripts/anki_sync.py --root <deck-root> [--parent anki::repo] plan
python3 scripts/anki_sync.py --root <deck-root> [--parent anki::repo] apply --approved --backup-dir <dir> [--reset id1,id2]
```

- `plan` is read only. It prints counts, then every add, update (old and new field text), suspension, orphan, and error.
- `apply` re-plans, refuses without `--approved` and `--backup-dir`, copies the collection into the backup directory, applies the plan, then re-plans. A correct sync ends with `verify: plan is empty`. The exit code is non-zero on any failure.
- `--reset` runs `card:reset` on the named cards, only if they were updated in this run.
- It refuses to run if `fcd.py check` reports errors, if a required field is missing from a note type, if Anki has two notes with the same ID, or if the backend is `direct` while Anki is running.

## Procedure

1. Run `fcd.py check`. Fix errors first.
2. Run `plan`. Show the user the plan.
3. For each update, say whether it changes what the card tests or its correct answer. Those are reset candidates. Run with `--reset <id>` only for cards the user explicitly approves.
4. After approval, quit Anki (direct backend), then run `apply --approved --backup-dir <dir>` and report the backup path, each result line, and the verify line.
5. Report failures by card ID. A failed add usually means the note type rejected the fields or Anki found a duplicate question.

## Verified against anki-cli 0.2.0 (direct backend)

- Sync twice: the second run changes nothing and creates no duplicates.
- Edit a card and sync: the note and card IDs are unchanged, so the schedule survives.
- Retire a card and sync: the card is suspended (`queue` -1) and a re-plan is empty.
- `card:reset` runs on an updated card.
- Add of Basic and Cloze notes, including HTML in fields.
- `note:add` and `note:bulk` require every field of the note type, including unmanaged ones. The script fills them with empty strings.
- `note:bulk` reports failures only as `null` IDs with no message. Use `note:add` to see the reason.
- Field search is unsupported (`ID:x` fails). The script dumps the target deck and matches IDs itself.
- Argument values starting with `--` are rejected. The script prefixes them with an empty span.

## Not verified

- Whether the `direct` backend is safe while Anki is open. The script refuses.
- Review history preservation across an update for a card that has real reviews (only a card with zero reviews was tested; IDs stay the same, so the schedule should too).
- Mobile and AnkiWeb behavior after the `ID` field is added.
- `anki_sync.py` moving an existing note when its folder changes (it does not; only `anki_adopt.py link` moves cards, once). Cards previously synced from a top-level folder stay in the old deck if they are later nested deeper.
- Nested deck creation against a real Anki collection (`deck:create` with a `::` path). Covered by a unit test only.
- Cloze cards with several deletions (several cards per note). The script groups cards by note but this was not tested.

## Setup snapshot (new computer or fresh Anki)

`scripts/anki_setup.py` saves and restores what the synced cards depend on, in `assets/anki-setup.json` inside the skill. It ships with the skill, so it is the default on every machine that has the skill. Use `--snapshot <file>` for another one:

- Basic and Cloze: fields, templates (front and back), and CSS.
- Scheduler options of the parent deck (`anki::repo`): new per day, reviews per day, desired retention, maximum interval, learn and relearn steps.

```bash
python3 scripts/anki_setup.py capture        # on the source machine
python3 scripts/anki_setup.py plan           # on the new machine, read only
python3 scripts/anki_setup.py restore --approved --backup-dir <dir> [--allow-shared-options]
```

- Restore creates missing note types, adds missing fields and templates, and sets templates and CSS that differ. It never reorders or removes fields. It warns when field order differs.
- **Shared presets.** Scheduler options belong to a preset, and a preset is usually shared by every deck. Changing it changes all of them, so restore blocks the options step unless `--allow-shared-options` is given. On a fresh install this is normally what you want. On a populated collection, check the plan first.
- Verified on a copy of the collection (`--col`): create (normal and cloze), field add, template add, template edit, CSS set, deck create, and options set.
- Not covered: Anki preferences, add-ons, FSRS parameters, media, other note types, and other decks' options. AnkiWeb sync or a collection backup carries those.
- Restore only styles the note types. Cards still come from `anki_sync.py`.

## New machine

Run `python3 scripts/anki_setup.py doctor [--root <deck-root>]` first and after each step. It is read only and prints the exact fix for each problem. Then:

1. Install the CLI: `uv tool install anki-cli` (needs the user's approval).
2. Open Anki once so it creates a profile, then quit it.
3. `doctor` again. Fix anything listed.
4. `python3 scripts/anki_setup.py plan`, show it, then `restore --approved --backup-dir <dir> --allow-shared-options` on approval. A fresh install has no other decks, so the shared preset is safe to change.
5. Create the deck root in the right repository (see below) and generate cards.
6. Sync with `anki_sync.py plan`, then `apply --approved --backup-dir <dir>` with Anki closed.

Work machines:

- Use a company-approved repository for the deck root and a company-approved agent.
- The work Anki collection is separate from the personal one. Do not sign in to a personal AnkiWeb account on it.
- Ask whether company policy allows work cards in any Anki cloud sync before enabling one.
- Each deck root has its own `registry.json`, so IDs on two machines do not collide.

## Adopting an existing deck

Do this only when a specific deck is worth maintaining in Git. History stays on the original Anki cards. The script never recreates them. It writes the new card `ID` into the original note and moves the cards under the sync parent.

```bash
python3 scripts/anki_adopt.py --root <deck-root> draft --deck anki::core::sre --folder core/sre --prefix sre
python3 scripts/fcd.py --root <deck-root> promote <deck-root>/drafts/import-sre.md <deck-root>/core/sre/sre.md --prefix sre
python3 scripts/anki_adopt.py --root <deck-root> link --deck anki::core::sre --folder core/sre             # plan
python3 scripts/anki_adopt.py --root <deck-root> link --deck anki::core::sre --folder core/sre --approved --backup-dir <dir>
python3 scripts/anki_sync.py --root <deck-root> plan                                                         # updates only, no adds
```

- `draft` is read only for Anki. It writes `drafts/import-<prefix>.md` with `ID: pending`, one card per note, titled `anki-note-<note id>`. The title is how `link` finds the note, so do not rename it. Source is `pasted: imported from Anki`. A cloze note's `Back Extra` becomes the card's `X:` field, so it is kept and still shows on the answer side only.
- Show the user the draft and the skipped list before promoting.
- Only `Basic` and `Cloze` notes are drafted, and only if `render_html(markdown)` equals the stored field exactly, so sync will not rewrite their text. Skipped, and left untouched in Anki: notes that already have an ID, and notes with images or other markup that does not round trip. Lines that look like fields (an acronym list such as `C: ...`, `A: ...`) are escaped in the draft, see card-format.md. Subdecks of `--deck` are not included. Run `draft` for each one.
- `link` without `--approved` is a plan. With `--approved --backup-dir` it backs up, creates the target deck, sets `ID` on each note, and moves its cards with `card:move` to `<parent>::<folder path>` (`--parent` defaults to `anki::repo`). The parent must be `anki` or under it.
- After `link`, sync shows one update per note (the source line on the back) and no adds. Do not pass `--reset` for them.
- The folder decides the destination. To keep cards where they are, use `--parent` and `--folder` that reproduce the current deck (for example `--parent anki::core --folder sre`).
- Do not export review history into Git. For backups or transfers that need media and history, use Anki's `.apkg` export.

Verified on a copy of the collection (`ANKI_COL`) with a 41-note, 103-card, 829-review cloze deck: 31 notes adopted (10 more with Back Extra content were skipped before `X:` existed), 76 cards moved to `anki::repo::core::sre`. Card IDs, due, interval, ease, reps, and lapses were identical before and after, the review log entries were still attached, and a second sync was empty. Not verified: Basic notes on real data, notes with several cards in different decks, and FSRS memory state (only the fields above were compared).
