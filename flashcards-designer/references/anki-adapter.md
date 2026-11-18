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
- Decks: `<parent>::<topic folder>`, with parent `repo` by default (`--parent`). Cards at the deck root go in the parent deck.
- Tags: `fc` and the topic. Tags are set on add only.
- Content is rendered to HTML: escaped, newlines as `<br>`, inline code as `<code>`, fenced code as `<pre><code>`. The source line shows the file name and section, not the hash.
- Retired cards are suspended, never deleted, so history is kept.
- Orphans (notes in the target deck whose ID is not in the deck) are reported and left alone.

## Commands

```bash
python3 scripts/anki_sync.py --root <deck-root> [--parent repo] plan
python3 scripts/anki_sync.py --root <deck-root> [--parent repo] apply --approved --backup-dir <dir> [--reset id1,id2]
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
- Moving an existing note to another deck when its topic folder changes.
- Cloze cards with several deletions (several cards per note). The script groups cards by note but this was not tested.

## Existing Anki decks (adopt, deferred)

Do this only when a specific deck is worth maintaining in Git.

- For backups or transfers that need media and review history, use Anki's built-in `.apkg` export.
- To move a deck into Markdown, read it with `cards --format json`, convert selected notes into a draft batch with `ID: pending`, and let the user approve it.
- After the batch is promoted, write the new card `ID` into the `ID` field of the original note so history stays attached and later syncs update it in place. Back up first.
- Do not export review history into Git.
