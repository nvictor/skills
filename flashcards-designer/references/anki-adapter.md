# Anki Adapter

One-way sync from the deck (Git) to Anki, done by `scripts/anki_sync.py`. Markdown owns card content. Anki owns review history. Edits made in Anki are not pulled back, so tell the user to edit cards in the repository.

The CLI is `anki` (package anki-cli 0.2.0, installed as a uv tool). It is not named `anki-cli`. Re-verify the behavior below after upgrading it.

## Model

Existing note types are used. No new note type is created.

| Deck card | Note type | Fields |
| --- | --- | --- |
| `Q:` and `A:` | `Basic` | `Front` = Q, `Back` = A plus a small source line, `ID` = card ID. Other fields (such as `Speak`) are left empty. |
| `C:` | `Cloze` | `Text` = C, `Back Extra` = source line, `ID` = card ID. |

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
- Moving an existing note to another deck when its folder changes. Cards previously synced from a top-level folder stay in the old deck if they are later nested deeper.
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

## Existing Anki decks (adopt, deferred)

Do this only when a specific deck is worth maintaining in Git.

- For backups or transfers that need media and review history, use Anki's built-in `.apkg` export.
- To move a deck into Markdown, read it with `cards --format json`, convert selected notes into a draft batch with `ID: pending`, and let the user approve it.
- After the batch is promoted, write the new card `ID` into the `ID` field of the original note so history stays attached and later syncs update it in place. Back up first.
- Do not export review history into Git.
