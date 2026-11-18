# Anki Adapter

One-way sync from the deck (Git) to Anki. Markdown owns card content. Anki owns review history. Edits made in Anki are not pulled back, so tell the user to edit cards in the repository.

The CLI is `anki` (package anki-cli 0.2.0, installed as a uv tool). It is not named `anki-cli`. Verify each command below against `anki <command> --help` and the installed version before relying on it.

## Facts verified against anki-cli 0.2.0, direct backend

- `notetype:create --name N --field A --field B ... --template T --front '...' --back '...'` creates a custom note type.
- `deck:create --name "A::B"` creates a deck, with hierarchy. The name is a flag, not positional.
- `note:add --deck D --notetype N --tags "a b" --Field value ...` adds a note. Fields are dynamic flags named after the note type's fields. A value that starts with `--` is rejected.
- `note:edit --id N --Field value` updates fields in place. `--tags` replaces tags.
- `note:bulk --deck D --notetype N --file cards.json` adds notes from a JSON array of flat objects (`{"ID": ..., "Front": ..., "Back": ..., "tags": [...]}`). It succeeds partially: failed items return `null` in `ids`.
- Duplicates are detected on the first field of the note type, and `note:add` refuses a duplicate with the existing note ID.
- Field search is not supported. `ID:x` fails. Do not look cards up by field.
- `cards --query "deck:D" --format json` returns every card with its `fields` (in note type order), `tags`, `reps`, and `lapses`, plus `note` (note ID) and `cardId`.
- `note:delete` and `deck:delete` need `--yes`.
- There is no command to delete a note type.

## Not verified yet

- Whether the `direct` backend is safe while Anki is open. Assume it is not.
- `card:suspend` and `card:reset` usage and effect. Read `--help` and test on a throwaway deck before the first real use.
- Cloze note types. Sync basic cards first.
- Exposure or setting of note GUIDs. Do not rely on GUIDs. Use the `ID` field.

## Setup

Create once, with the `ID` field first so duplicate detection works on it:

```bash
anki notetype:create --name RepoCard --field ID --field Front --field Back --field Source \
  --template Card --front '{{Front}}' \
  --back '{{FrontSide}}<hr id=answer>{{Back}}<br><small>{{Source}}</small>'
```

Use a dedicated parent deck so repository cards never mix with existing cards, for example `repo::<deck-name>`.

## Preflight

1. `anki --format plain status` must report `ok=True`. Note the backend.
2. If the backend is `direct`, require Anki to be closed: `pgrep -x Anki` must print nothing. Otherwise require a working AnkiConnect connection. Do not write otherwise.
3. Copy the collection file reported by `status` to a backup location before the first write of the session, and report the path.

## Plan (read only)

1. Select cards: approved deck cards under the chosen files. Never drafts.
2. Dump the target deck: `anki --format json cards --query 'notetype:RepoCard deck:"repo::<name>"'`. Build a map from the `ID` field (first entry of `fields`) to `note` (note ID). If any ID appears twice, abort and report it.
3. Compare each non-retired deck card with its note:
   - not in Anki: **add**
   - in Anki with different Front, Back, or Source: **update**
   - identical: no-op
4. For each retired card present in Anki and not suspended: **suspend**. Retired cards absent from Anki are skipped.
5. Report Anki notes whose `ID` is not in the deck as **orphans**. Never delete them.
6. For each update, say whether it is substantive (changes what is tested or the correct answer). Those are reset candidates. Run `card:reset` only with explicit approval for that card.
7. Show the counts and every update and suspension. Wait for approval.

## Apply

1. Render fields. Anki fields are HTML: escape `&`, `<`, `>`, convert newlines to `<br>`, and convert fenced code to `<pre><code>`. Use the same renderer for add and update so the comparison in the plan stays stable.
2. Add new cards with one `note:bulk` call and tags `repo` plus the topic. Check `ids` for `null` and report each failure with its card ID.
3. Update with `note:edit --id <note> --Front ... --Back ... --Source ...`.
4. Suspend retired cards with `card:suspend`, verified as above. Suspension removes them from review and keeps their history.
5. Re-dump and re-plan. A correct sync leaves an empty plan.

## Acceptance checks

Run these on a throwaway deck before trusting the adapter, and again after any CLI upgrade:

- Sync the same batch twice. The second run adds nothing and creates no duplicates.
- Edit a reviewed card and sync. Its schedule (`reps`, due date) survives.
- Retire a card by splitting it and sync. The original stops appearing in reviews and its history remains.

## Existing Anki decks (adopt, deferred)

Do this only when a specific deck is worth maintaining in Git.

- For backups or transfers that need media and review history, use Anki's built-in `.apkg` export.
- To move a deck into Markdown, read it with `cards --format json`, convert selected notes into a draft batch with `ID: pending`, and let the user approve it.
- After the batch is promoted, write the new card `ID` into the original note so history stays attached. This needs a note type with an `ID` field. Check how to add one without losing data before attempting it, and back up first.
- Do not export review history into Git.
