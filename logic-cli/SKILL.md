---
name: logic-cli
description: Read and edit MIDI notes in a running Logic Pro project with the `logic` command. Use for listing regions and notes, transposing, setting velocity, quantizing, or exporting and replacing a MIDI region in Logic Pro. Not for transport, mixing, plugins, audio, or creating tracks and regions.
---

# Logic CLI

Edit MIDI regions in Logic Pro through the `logic` command.
Source: `~/Developer/logic-cli`.

## Before any command

```bash
logic check
```

- Stop and report if it lists a problem.
- If `logic` is missing, ask the user to install it (see the repo README).
- Every command except `check`, `inspect` and `region list` drives the Logic Pro UI.
  Ask the user to keep hands off keyboard and mouse.

## Address a region

```bash
logic region list --json
```

- Pick with `--track` (name or number), `--bar` (start bar) and `--region` (name).
- The options must match exactly one region.

## Read

```bash
logic note list --track 1 --bar 3 --json
```

- `beat` counts quarter notes from the region start, from 0.
- Middle C (pitch 60) is `C3`.
- `id` is valid for this listing only.
- Reading exports the region, so it drives the UI too.

## Edit

Edits replace the region. `--project` must name the front project.
Confirm the project name and the target region with the user before the first edit.

```bash
logic note transpose --track 1 --bar 3 --project MySong --semitones=-2
```

```bash
logic note velocity --track 1 --bar 3 --project MySong --value 100
```

```bash
logic note quantize --track 1 --bar 3 --project MySong --division 1/16
```

For other changes, export, edit the file, then import:

```bash
logic region export --track 1 --bar 3 --output /tmp/part.mid
```

```bash
logic region import /tmp/part-edited.mid --track 1 --bar 3 --project MySong
```

- Keep the exported file's start events and end-of-track tick, so the length stays the same.
- The region takes the track name stored in the file.

## Refusals and failures

- A region with Loop, Mute, transpose, velocity offset, delay, quantize, dynamics,
  gate time or pitch source set is refused. Report it. Do not change settings yourself.
- A region with a custom color is refused too. An edit finds this at the end and undoes itself.
- Regions must start and end on a bar line.
- A failed replace undoes its own steps. If the message says it could not restore,
  tell the user to use Undo in Logic Pro.
- Never save the project. The user decides.

## Limits

- Tested on Logic Pro 13.0, English UI, 4/4 and 3/4.
- Automation and other unlisted region settings may be lost on replace.
- Off-screen tracks or regions may not be listed.
- Recorded pitch bend denser than 1/256 note is thinned.
- Not available: adding or deleting single notes by command, creating regions or tracks.
