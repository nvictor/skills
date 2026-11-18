# Card Format

## File

One Markdown file per topic area at `<deck-root>/<topic>/<name>.md`. The deck root is a single folder holding the cards, `registry.json`, and `drafts/`. A file has an optional `# Title` and any number of cards. Each card starts with `## <short title>`.

```markdown
# Replication

## Quorum overlap

ID: replication-001
Q: When do read and write quorums overlap, and why does it matter?
A: When R + W > N. Every read then sees at least one replica holding the latest write.
Source: ../../docs/replication.md#Quorums sha256:3f2a9c1d44ab

## Retired example

ID: replication-002
Q: What does eventual consistency guarantee?
A: Replicas converge if updates stop.
Source: ../../docs/replication.md#Consistency sha256:91c0e2b7a1de
Retired: 2026-11-18 replaced-by: replication-005, replication-006
```

## Fields

- `ID:` unique and stable. Format `<prefix>-<NNN>`, prefix lowercase letters, digits, and hyphens, number at least three digits. Assigned only by `fcd.py`. Drafts use `ID: pending`.
- `Q:` and `A:` for basic and free-form cards. Values may continue over several lines until the next field or card. Fenced code blocks are preserved.
- `C:` for cloze cards, instead of `Q:` and `A:`. Contains at least one `{{c1::deletion}}`. Use only when a cloze suits the material.
- `X:` optional, only on `C:` cards. Answer-side explanation shown after the cloze is revealed (Anki `Back Extra`). Never put it in `C:`, which shows on the front.
- **Escaping.** A continuation line that starts with a field name and colon (`ID:`, `Q:`, `A:`, `C:`, `X:`, `Source:`, `Retired:`) or with `## ` would be read as a new field or card. Write it with one leading backslash (`\\A: Access`). The parser removes one backslash, so lines that already start with a backslash before such a prefix gain another. `fcd.py promote` and `anki_adopt.py` escape automatically. Lines inside code fences are never parsed and need no escape. The first line of a value (after `Q: `) never needs one.
- `Source:` required. See below.
- `Retired:` present only on retired cards. Format `<date>` or `<date> replaced-by: <ids>`. Retired cards stay in the file so their IDs and history are never lost, and sync suspends them.

Keep metadata minimal. Do not add tags, difficulty, or scheduling fields. Topic and file path carry grouping.

## Source

- File-backed: `<relative path>[#<locator>] sha256:<12 hex>`. The path is relative to the card file. The locator is a heading text (case-insensitive) or a line range `L10-40`. Without a locator, the whole file is hashed.
- Pasted or unsaved: `pasted: <short label>`. Staleness is unverifiable. Do not claim it was checked.

The hash covers the normalized text of the section: from the heading to the next heading of the same or higher level, ignoring trailing whitespace and blank-line runs. Generate it with `fcd.py source`. When the hash no longer matches, `check` reports `SOURCE_STALE`.

## Identity rules

- An ID never changes and is never reused, including after retirement.
- Editing a card keeps its ID.
- Splitting retires the original and gives each replacement a new ID.
- The registry's counters never decrease. If the registry is lost, the allocator falls back to the highest ID in the deck.

## Drafts

Proposed batches live in `drafts/` using the same format with `ID: pending`. `fcd.py promote` validates the batch, assigns IDs, appends the cards to the target file, and moves the draft to `drafts/_promoted/`.
