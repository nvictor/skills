---
name: downbeat
description: Create Logic Pro projects and read and edit MIDI notes with the `downbeat` command. Use for starting a project with a tempo, meter and key, checking status, setting tempo, listing, creating and renaming tracks, listing regions and notes, transposing, setting velocity, quantizing, or exporting and replacing a MIDI region. Not for playback, mixing, plugins, audio editing, deleting tracks, or creating regions.
---

# downbeat

Start projects and edit MIDI regions in Logic Pro through the `downbeat` command.
Source: `~/Developer/downbeat`.

## Before any command

```bash
downbeat check
```

- Stop and report if it lists a problem.
- If `downbeat` is missing, ask the user to install it (see the repo README).
- Every command except `check`, `inspect`, `status`, `tempo get`, `track list`, `region list` and `project template` drives the Logic Pro UI.
  Ask the user to keep hands off keyboard and mouse.

## New project

```bash
downbeat project new "Night Drive" --tempo 92 --signature 6/8 --key "A minor"
```

- Works with Logic Pro closed. `downbeat check` is not needed first.
- Saved in `~/Music/Logic` unless `--directory` says otherwise.
- All settings are optional. Meters: 3/4, 4/4, 5/4, 6/8, 7/8, 12/8. Tempo: whole numbers.
- Needs a template. If missing, ask the user to save an empty project and run
  `downbeat project template <path.logicx>`, or pass `--template`.
- Refused while a project has unsaved changes. Report it. Never save or discard for the user.

## Status and tempo

```bash
downbeat status --json
```

```bash
downbeat tempo set 92 --project "Night Drive"
```

`tempo set` does not save.

## Tracks

```bash
downbeat track list --json
```

```bash
downbeat track create --type instrument --name "Bass" --project "Night Drive"
```

```bash
downbeat track rename 1 "Drums" --project "Night Drive"
```

- Types: `instrument`, `audio`, `external` (MIDI). A new track goes after the selected one.
- `<track>` is a name or a number. Numbers change when tracks are added.
- Neither command saves the project.

## Address a region

```bash
downbeat region list --json
```

- Pick with `--track` (name or number), `--bar` (start bar) and `--region` (name).
- The options must match exactly one region.

## Read

```bash
downbeat note list --track 1 --bar 3 --json
```

- `beat` counts quarter notes from the region start, from 0.
- Middle C (pitch 60) is `C3`.
- `id` is valid for this listing only.
- Reading exports the region, so it drives the UI too.

## Edit

Edits replace the region. `--project` must name the front project.
Confirm the project name and the target region with the user before the first edit.

```bash
downbeat note transpose --track 1 --bar 3 --project MySong --semitones=-2
```

```bash
downbeat note velocity --track 1 --bar 3 --project MySong --value 100
```

```bash
downbeat note quantize --track 1 --bar 3 --project MySong --division 1/16
```

For other changes, export, edit the file, then import:

```bash
downbeat region export --track 1 --bar 3 --output /tmp/part.mid
```

```bash
downbeat region import /tmp/part-edited.mid --track 1 --bar 3 --project MySong
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
- Never save an existing project. The user decides. `project new` saves only the project it creates.

## Limits

- Tested on Logic Pro 13.0, English UI.
- Automation and other unlisted region settings may be lost on replace.
- Off-screen regions may not be listed or selected.
- Recorded pitch bend denser than 1/256 note is thinned.
- Not available: adding or deleting single notes by command, creating regions, deleting tracks.
