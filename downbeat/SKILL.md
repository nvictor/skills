---
name: downbeat
description: Build drum MIDI from written grooves, read EZdrummer projects, and control Logic Pro with the `downbeat` command. Use for turning GUS and PAL drum arrangements into MIDI clips, inspecting MIDI files by bar, batch editing and humanizing drum voices, staging clips for EZdrummer, reading a saved EZdrummer 3 project, and in Logic Pro for starting, opening, saving and describing a project, playback and recording, checking status, setting tempo, listing, creating, renaming, selecting, muting and soloing tracks, setting track volume and pan, creating markers, listing, adding, removing and bypassing plugins, listing MIDI ports, importing and bouncing audio files, importing MIDI files, listing, creating, renaming, moving, duplicating, splitting, joining, deleting, exporting and replacing regions, and listing, adding, deleting, changing, exporting and importing as JSON, transposing, quantizing or setting velocity of notes. Not for operating the EZdrummer window, sends, plugin settings, editing audio, or deleting tracks.
---

# downbeat

Three command groups. Source: `~/Developer/downbeat`.

- `downbeat midi`: drum arrangements and MIDI files. No app needed.
- `downbeat ezdrummer`: read saved EZdrummer 3 projects. No app needed.
- `downbeat logic`: control Logic Pro.

## Check for updates first

Once per session, before the first downbeat command:

```bash
~/.claude/skills/downbeat/scripts/check-update.sh
```

- Codex: the same script is in `~/.codex/skills/downbeat/scripts/`.
- This skill needs downbeat 0.2.0 or later.
- If it prints `update:` lines, show them and ask before running the commands. They pull, build and replace the installed binary.
- After an update to the skill, read this file again.
- A `note:` line means GitHub was not reached. Say so and continue.

## Drum arrangements

Format, drum map and edit rules: `~/Developer/downbeat/docs/arrangements.md`. Read it before writing a file.
Example: `~/Developer/downbeat/examples/artemis.json`.

- Take grooves from the song's diary (GUS) and the form from PAL. For Atalanta, follow `~/Projects/atalanta/AGENTS.md`.
- GUS gives positions only. Ask about velocities, flams and articulations the diary does not state.
- Repeat a groove with `use`, so it is edited in one place.

```bash
downbeat midi build song.json --output song-midi --per part
```

- `--per section` (default) writes one file per section. `--per part` writes `<section>/<clip>.mid`.
- `--replace` updates an earlier build. It stops if a built file was changed.
- Report the files it prints.

```bash
downbeat midi inspect song-midi/chorus/*.mid --arrangement song.json
```

- Check the result before the handoff. Positions count beats from 1: 3.5 is 3&. `f` marks a flam.
- Add `--json` for `sameAs`, which names a repeated bar.

```bash
downbeat midi edit song.json operations.json --dry-run
```

- Run the dry run first, then without `--dry-run`. Build again afterwards.
- If parts sharing a source would differ, the edit is refused. Ask the user: `"shared": "source"` or `"detach"`.

```bash
downbeat midi humanize song.json --section chorus --seed 7 --timing 0.01 --velocity 6
```

- Only when asked. Leave `--drop` out unless the user wants hits left out.
- `--clear` removes the rules of a section.

## EZdrummer

```bash
downbeat ezdrummer inspect "$HOME/Music/EZdrummer 3/song.ezd3p" --notes
```

- Reads the saved file only. Ask the user to save first.
- No command operates EZdrummer. Import clips, set the tempo and save in its window.
- Delete the staging folder only after the saved project reopens correctly, and the user agrees.

## Before any Logic Pro command

```bash
downbeat logic check
```

- Stop and report if it lists a problem.
- If `downbeat` is missing, ask the user to install it (see the repo README).
- Every `logic` command except `logic check`, `logic inspect`, `logic status`, `logic tempo get`, `logic track list`, `logic region list`, `logic project info` and `logic project template` drives the Logic Pro UI.
  Ask the user to keep hands off keyboard and mouse.

## New project

```bash
downbeat logic project new "Night Drive" --tempo 92 --signature 6/8 --key "A minor"
```

- Works with Logic Pro closed. `downbeat logic check` is not needed first.
- Saved in `~/Music/Logic` unless `--directory` says otherwise.
- All settings are optional. Meters: 3/4, 4/4, 5/4, 6/8, 7/8, 12/8. Tempo: whole numbers.
- Needs a template. If missing, ask the user to save an empty project and run
  `downbeat logic project template <path.logicx>`, or pass `--template`.
- `downbeat logic project template` prints the current template's path.
- Refused while a project has unsaved changes. Report it. Never save or discard for the user.

## Open, describe and save

```bash
downbeat logic project open "$HOME/Music/Logic/Night Drive.logicx"
```

```bash
downbeat logic project info --json
```

```bash
downbeat logic project save --project "Night Drive"
```

- `open` is refused while a project has unsaved changes.
- Run `save` only when the user asks.

## Playback

```bash
downbeat logic play
```

```bash
downbeat logic stop
```

```bash
downbeat logic record --project "Night Drive"
```

- Run `logic record` only when the user asks. End it with `logic stop`.
- Stop playback before an edit or an import.

## Status and tempo

```bash
downbeat logic status --json
```

```bash
downbeat logic tempo set 92 --project "Night Drive"
```

`logic tempo set` does not save.

## Tracks

```bash
downbeat logic track list --json
```

```bash
downbeat logic track create --type instrument --name "Bass" --project "Night Drive"
```

```bash
downbeat logic track rename 1 "Drums" --project "Night Drive"
```

- Types: `instrument`, `audio`, `external` (MIDI). A new track goes after the selected one.
- `<track>` is a name or a number. Numbers change when tracks are added.
- Neither command saves the project.

```bash
downbeat logic track select "Bass" --project "Night Drive"
```

```bash
downbeat logic track mute "Bass" --project "Night Drive"
```

```bash
downbeat logic track solo "Bass" --off --project "Night Drive"
```

- `--off` unmutes or ends a solo.
- A solo hides mute states, so `mute` is refused until solo is off.

## Volume and pan

```bash
downbeat logic mixer volume "Bass" --db -6 --project "Night Drive"
```

```bash
downbeat logic mixer pan "Bass" --value -20 --project "Night Drive"
```

- Volume: up to `6`. `-inf` silences the track. Not for external MIDI tracks.
- Pan: `-64` (left) to `63` (right). `0` is the middle.
- Each command prints the value reached. Report that one.

## Markers

```bash
downbeat logic marker create "Chorus" --bar 9 --project "Night Drive"
```

- One marker per bar. No `#` in the name.
- There is no command to list, move or delete markers.

## MIDI ports

```bash
downbeat midi ports --json
```

Works without Logic Pro or `downbeat logic check`. A `source` is read from, a `destination` is written to.

## Plugins

```bash
downbeat logic plugin list "Bass" --json
```

```bash
downbeat logic plugin add "Bass" "Limiter" --project "Night Drive"
```

```bash
downbeat logic plugin remove "Bass" "Limiter" --project "Night Drive"
```

```bash
downbeat logic plugin bypass "Bass" "Compressor" --project "Night Drive"
```

- The list follows the signal: instrument first, then effects. Numbers change after `add` and `remove`.
- `add` adds an effect at the end. It cannot add an instrument. Use the name in Logic's menu; `--format "Dual Mono"` picks a format.
- `remove` loses the plugin's settings. Confirm with the user first.
- Bypassing or removing the instrument silences the track.
- A `null` bypass state means Logic does not report it. Tell the user to check the Mixer.
- `--off` turns the bypass off. A plugin is picked by name or by its number from the list.
- `list` selects the track while it reads, so it drives the UI.

## Audio files

```bash
downbeat logic audio import take.wav --track "Vocals" --bar 5 --project "Night Drive"
```

```bash
downbeat logic audio export --track "Vocals" --output vocals.wav
```

- `import` needs an audio track and free bars.
- `export` bounces one track to WAVE, starting at the project start. Other export settings are the ones Logic last used. A muted track still exports its audio.
- `logic region delete`, `move`, `duplicate` and `rename` work on audio regions too.

## Import and delete

```bash
downbeat logic midi import drums.mid --bar 5 --project "Night Drive"
```

```bash
downbeat logic region delete --track 1 --bar 3 --project "Night Drive"
```

- `import` adds new tracks and keeps the project tempo.
- Confirm the target region with the user before `delete`.

## Address a region

```bash
downbeat logic region list --json
```

- Pick with `--track` (name or number), `--bar` (start bar) and `--region` (name).
- The options must match exactly one region.

## Create a region

```bash
downbeat logic region create --track "Bass" --bar 1 --bars 4 --name "Verse" --project "Night Drive"
```

- Makes an empty region. Fill it with `logic note import`.
- Software instrument and external MIDI tracks only. The bars must be free.
- `--bars` defaults to 1, `--name` to the track name.

## Rename a region

```bash
downbeat logic region rename "Chorus" --region "Verse" --project "Night Drive"
```

The new name comes first. The options pick the region.

## Move and duplicate a region

```bash
downbeat logic region duplicate --region "Chorus" --to-bar 9 --project "Night Drive"
```

```bash
downbeat logic region move --region "Chorus" --bar 9 --to-bar 17 --project "Night Drive"
```

- Same track only. The target bars must be free.
- `--bar` picks the source. `--to-bar` is the destination.
- The copy keeps the name. Afterwards, pick a region with `--bar` too.

## Split and join

```bash
downbeat logic region split --region "Chorus" --at-bar 13 --project "Night Drive"
```

```bash
downbeat logic region join --region "Chorus" --bar 9 --project "Night Drive"
```

- `split` cuts at the start of a bar. `--notes keep|shorten|split` handles crossing MIDI notes.
  Prefer the default `keep`. After `split`, downbeat cannot read the second part.
- `join` takes the region and the next one that touches it.

## Read

```bash
downbeat logic note list --track 1 --bar 3 --json
```

- `beat` counts quarter notes from the region start, from 0.
- Middle C (pitch 60) is `C3`.
- `id` is valid for this listing only.
- Reading exports the region, so it drives the UI too.

## Edit

Edits replace the region. `--project` must name the front project.
Confirm the project name and the target region with the user before the first edit.

```bash
downbeat logic note transpose --track 1 --bar 3 --project MySong --semitones=-2
```

```bash
downbeat logic note add --track 1 --bar 3 --project MySong --pitch F#3 --beat 0 --duration 0.5 --velocity 100
```

```bash
downbeat logic note delete --track 1 --bar 3 --project MySong --id 2
```

```bash
downbeat logic note update --track 1 --bar 3 --project MySong --id 2 --pitch D3 --velocity 90
```

```bash
downbeat logic note velocity --track 1 --bar 3 --project MySong --value 100
```

```bash
downbeat logic note quantize --track 1 --bar 3 --project MySong --division 1/16
```

- `logic note add`: `--pitch` is a name (middle C is `C3`) or 0 to 127. `--beat` counts from 0.
  The note must end inside the region and not overlap the same pitch.
- `logic note delete` and `logic note update`: take `--id` from a fresh `logic note list`. Ids change after every edit, so list again before the next one.
- `logic note update`: give at least one of `--pitch`, `--beat`, `--duration`, `--velocity`. The rest stays.

To write or rewrite many notes, use JSON. One import is much faster than many single edits:

```bash
downbeat logic note export --track 1 --bar 3 > /tmp/notes.json
```

```bash
downbeat logic note import /tmp/notes.json --track 1 --bar 3 --project MySong
```

- Format: `{"notes": [{"pitch": 60, "beat": 0, "duration": 1, "velocity": 100}]}`.
- `pitch` is a number. `beat` and `duration` are quarter notes from the region start.
- `velocity` and `releaseVelocity` are optional.
- `import` replaces every note. Other events stay.

For changes to other events, export the MIDI file, edit it, then import:

```bash
downbeat logic region export --track 1 --bar 3 --output /tmp/part.mid
```

```bash
downbeat logic region import /tmp/part-edited.mid --track 1 --bar 3 --project MySong
```

- Keep the exported file's start events and end-of-track tick, so the length stays the same.
- The region takes the track name stored in the file.

## Refusals and failures

- A region with Loop, Mute, transpose, velocity offset, delay, quantize, dynamics,
  gate time or pitch source set is refused. Report it. Do not change settings yourself.
- A region with a custom color is refused too. An edit finds this at the end and undoes itself.
- MIDI export, import and note commands need a region that starts and ends on a bar line.
  `delete`, `move`, `duplicate` and `rename` accept any region; `--bar` is the bar it starts in.
- A region with several MIDI channels can be read but not edited.
- A region on a muted track, or silenced by a solo, cannot be read or edited. Report it.
- A failed replace undoes its own steps. If the message says it could not restore,
  tell the user to use Undo in Logic Pro.
- Never save an existing project unprompted. The user decides. `logic project new` saves only the project it creates.

## Limits

- Tested on Logic Pro 13.0, English UI.
- Automation and other unlisted region settings may be lost on replace.
- Off-screen regions may not be listed or selected.
- Recorded pitch bend denser than 1/256 note is thinned.
- Not available: deleting tracks, moving regions between tracks.
