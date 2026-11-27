---
name: downbeat
description: Control Logic Pro and edit MIDI notes with the `downbeat` command. Use for starting, opening, saving and describing a project, playback and recording, checking status, setting tempo, listing, creating, renaming, selecting, muting and soloing tracks, setting track volume and pan, creating markers, listing and bypassing plugins, listing MIDI ports, importing MIDI files, listing, creating, renaming, moving, duplicating, deleting, exporting and replacing regions, and listing, adding, deleting, changing, exporting and importing as JSON, transposing, quantizing or setting velocity of notes. Not for sends, adding or removing plugins, plugin settings, audio editing, or deleting tracks.
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
- Every command except `midi ports`, `check`, `inspect`, `status`, `tempo get`, `track list`, `region list`, `project info` and `project template` drives the Logic Pro UI.
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

## Open, describe and save

```bash
downbeat project open "$HOME/Music/Logic/Night Drive.logicx"
```

```bash
downbeat project info --json
```

```bash
downbeat project save --project "Night Drive"
```

- `open` is refused while a project has unsaved changes.
- Run `save` only when the user asks.

## Playback

```bash
downbeat play
```

```bash
downbeat stop
```

```bash
downbeat record --project "Night Drive"
```

- Run `record` only when the user asks. End it with `stop`.
- Stop playback before an edit or an import.

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

```bash
downbeat track select "Bass" --project "Night Drive"
```

```bash
downbeat track mute "Bass" --project "Night Drive"
```

```bash
downbeat track solo "Bass" --off --project "Night Drive"
```

- `--off` unmutes or ends a solo.
- A solo hides mute states, so `mute` is refused until solo is off.

## Volume and pan

```bash
downbeat mixer volume "Bass" --db -6 --project "Night Drive"
```

```bash
downbeat mixer pan "Bass" --value -20 --project "Night Drive"
```

- Volume: up to `6`. `-inf` silences the track. Not for external MIDI tracks.
- Pan: `-64` (left) to `63` (right). `0` is the middle.
- Each command prints the value reached. Report that one.

## Markers

```bash
downbeat marker create "Chorus" --bar 9 --project "Night Drive"
```

- One marker per bar. No `#` in the name.
- There is no command to list, move or delete markers.

## MIDI ports

```bash
downbeat midi ports --json
```

Works without Logic Pro or `downbeat check`. A `source` is read from, a `destination` is written to.

## Plugins

```bash
downbeat plugin list "Bass" --json
```

```bash
downbeat plugin bypass "Bass" "Compressor" --project "Night Drive"
```

- The list includes the instrument. Bypassing it silences the track.
- `--off` turns the bypass off. A plugin is picked by name or by its number from the list.
- `list` selects the track while it reads, so it drives the UI.

## Import and delete

```bash
downbeat midi import drums.mid --bar 5 --project "Night Drive"
```

```bash
downbeat region delete --track 1 --bar 3 --project "Night Drive"
```

- `import` adds new tracks and keeps the project tempo.
- Confirm the target region with the user before `delete`.

## Address a region

```bash
downbeat region list --json
```

- Pick with `--track` (name or number), `--bar` (start bar) and `--region` (name).
- The options must match exactly one region.

## Create a region

```bash
downbeat region create --track "Bass" --bar 1 --bars 4 --name "Verse" --project "Night Drive"
```

- Makes an empty region. Fill it with `note import`.
- Software instrument and external MIDI tracks only. The bars must be free.
- `--bars` defaults to 1, `--name` to the track name.

## Rename a region

```bash
downbeat region rename "Chorus" --region "Verse" --project "Night Drive"
```

The new name comes first. The options pick the region.

## Move and duplicate a region

```bash
downbeat region duplicate --region "Chorus" --to-bar 9 --project "Night Drive"
```

```bash
downbeat region move --region "Chorus" --bar 9 --to-bar 17 --project "Night Drive"
```

- Same track only. The target bars must be free.
- `--bar` picks the source. `--to-bar` is the destination.
- The copy keeps the name. Afterwards, pick a region with `--bar` too.

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
downbeat note add --track 1 --bar 3 --project MySong --pitch F#3 --beat 0 --duration 0.5 --velocity 100
```

```bash
downbeat note delete --track 1 --bar 3 --project MySong --id 2
```

```bash
downbeat note update --track 1 --bar 3 --project MySong --id 2 --pitch D3 --velocity 90
```

```bash
downbeat note velocity --track 1 --bar 3 --project MySong --value 100
```

```bash
downbeat note quantize --track 1 --bar 3 --project MySong --division 1/16
```

- `note add`: `--pitch` is a name (middle C is `C3`) or 0 to 127. `--beat` counts from 0.
  The note must end inside the region and not overlap the same pitch.
- `note delete` and `note update`: take `--id` from a fresh `note list`. Ids change after every edit, so list again before the next one.
- `note update`: give at least one of `--pitch`, `--beat`, `--duration`, `--velocity`. The rest stays.

To write or rewrite many notes, use JSON. One import is much faster than many single edits:

```bash
downbeat note export --track 1 --bar 3 > /tmp/notes.json
```

```bash
downbeat note import /tmp/notes.json --track 1 --bar 3 --project MySong
```

- Format: `{"notes": [{"pitch": 60, "beat": 0, "duration": 1, "velocity": 100}]}`.
- `pitch` is a number. `beat` and `duration` are quarter notes from the region start.
- `velocity` and `releaseVelocity` are optional.
- `import` replaces every note. Other events stay.

For changes to other events, export the MIDI file, edit it, then import:

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
- A region with several MIDI channels can be read but not edited.
- A region on a muted track, or silenced by a solo, cannot be read or edited. Report it.
- A failed replace undoes its own steps. If the message says it could not restore,
  tell the user to use Undo in Logic Pro.
- Never save an existing project unprompted. The user decides. `project new` saves only the project it creates.

## Limits

- Tested on Logic Pro 13.0, English UI.
- Automation and other unlisted region settings may be lost on replace.
- Off-screen regions may not be listed or selected.
- Recorded pitch bend denser than 1/256 note is thinned.
- Not available: deleting tracks, moving regions between tracks.
