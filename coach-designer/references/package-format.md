# Portable coach package format

Read this file completely for create, refine, or migrate operations involving a package.

## Contents

- Package contents
- `manifest.json`
- `runner.md`
- `prompt.md`
- `curriculum.md`
- `state.md`
- Target cadence
- `migration.json`
- Source conflicts

## Package contents

Use this layout:

```text
<coach-id>/
├── manifest.json
├── runner.md
├── prompt.md
├── curriculum.md
├── state.md
└── migration.json    # migrations only
```

Coaches run manually: the learner starts a session and supplies the package root. A package has no deployments, scheduler adapters, or automations.

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`.

## `manifest.json`

Use JSON because it is dependency-free, machine-validatable, and broadly understood by AI agents and apps. Keep platform-specific settings out of the package.

Required shape:

```json
{
  "schema_version": 2,
  "id": "judgment-coach",
  "name": "Coach: Judgment",
  "status": "active",
  "version": 1,
  "runner_file": "runner.md",
  "prompt_file": "prompt.md",
  "curriculum_file": "curriculum.md",
  "state_file": "state.md",
  "schedule": {
    "enabled": false,
    "frequency": "weekly",
    "interval": 1,
    "start_date": null,
    "days": [],
    "local_time": null,
    "timezone": null
  },
  "session": {
    "minimum_minutes": 3,
    "maximum_minutes": 5,
    "interaction": "conversational"
  },
  "continuity": {
    "state_authority": "package",
    "read_before_session": true,
    "update_after_turn": true,
    "handoff_when_read_only": true
  },
  "privacy": "private"
}
```

### Field rules

- `schema_version`: Use `2`.
- `id`: Use lowercase ASCII letters, digits, and hyphens. Match the directory name.
- `name`: Use `Coach: <subject>` with the exact prefix and one space, a nonempty subject, and no leading or trailing whitespace. Preserve subject capitalization and acronyms; omit a redundant trailing "Coach". This is the canonical display name for the package document and app labels. Keep ids and directories unchanged.
- `status`: Use `draft`, `active`, `paused`, or `archived`. This describes intended source state.
- `version`: Start at `1`. Increment when coaching behavior changes. Do not increment for state-only updates.
- `runner_file`: Use a safe relative path, normally `runner.md`.
- `prompt_file`: Use a safe relative path, normally `prompt.md`.
- `curriculum_file`: Use a safe relative path, normally `curriculum.md`. Required.
- `state_file`: Use a safe relative path, normally `state.md`.
- `schedule`: Describes the target cadence, meaning how often the learner intends to run the coach. It never triggers a run. See Target cadence.
- `schedule.enabled`: Use `false`. Nothing runs automatically.
- `schedule.frequency`: Use `daily`, `weekly`, `monthly`, or `manual`. `manual` means no target cadence.
- `schedule.interval`: Use a positive integer. The target gap is `interval` periods of `frequency`.
- `schedule.start_date`, `schedule.days`, `schedule.local_time`, `schedule.timezone`: Optional and unused by apps. Use `null` or an empty list unless preserving a migrated source.
- `session.minimum_minutes` and `maximum_minutes`: Use positive integers with minimum no greater than maximum.
- `session.interaction`: Use `conversational`, `self-contained`, or `mixed`.
- `continuity.state_authority`: Use `package`; `state.md` is authoritative across agents.
- `continuity.read_before_session`: Require the runner to read state before coaching.
- `continuity.update_after_turn`: Require a write after every coaching turn, including turns that leave an interaction open.
- `continuity.handoff_when_read_only`: Require a complete state-file replacement block when the agent cannot write files.
- `privacy`: Use `private`, `internal`, or `public`. Prefer `private` for personal coaching.

Do not put model names, provider IDs, project IDs, working directories, notification settings, or native scheduler expressions in the manifest.

## Target cadence

Use `schedule` as the learner's intended rhythm, for example `weekly` with `interval` `1`. Apps such as Dashi compare it with the date of the last completed session in `state.md` to show whether the coach is on track, due soon, or overdue.

- Period: `daily` is 1 day, `weekly` is 7 days, `monthly` is 30 days. Multiply by `interval`.
- `manual` means no target; apps show only the last run.
- The last run is the newest entry under `## Last completed session`. Start each entry with a full ISO 8601 timestamp.

## `runner.md`

Make `runner.md` the portable entrypoint. It must:

- resolve `manifest.json`, `prompt.md`, `curriculum.md`, and `state.md` from the package root supplied by the learner or current working directory
- read the manifest, behavioral prompt, curriculum, and canonical state before coaching
- treat `prompt.md` as behavior, `curriculum.md` as the topic map and sequencing guide, and `state.md` as the cross-agent continuity authority
- resume an open interaction from its recorded phase without automatically reteaching; use evidence or a focused clarification when legacy state lacks teaching details
- update state after every coaching turn, recording the current objective, interaction position, outstanding work, observed evidence, and remaining budget when an interaction is incomplete
- reread state immediately before writing and merge newer evidence rather than overwrite it
- treat state as a compact current snapshot, never an append-only diary
- retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim
- compact older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples
- replace stale or superseded statements instead of appending another event
- preserve evidence and avoid invented history
- avoid modifying the manifest, prompt, curriculum, runner, or migration record
- emit a complete replacement `state.md` in a clearly labeled handoff block when file writing is unavailable
- avoid discussing file mechanics unless access fails or a conflict needs user judgment

Keep the runner provider-neutral and identical across packages whenever the continuity contract is the same.

## `prompt.md`

Use the exact manifest `name` as the first heading in `prompt.md`. Keep required section headings below it. For standalone definitions, use the same naming format.

Make `prompt.md` the canonical behavioral instruction. It must:

- be provider-neutral
- be self-contained enough to paste into a capable AI agent
- use “session” rather than scheduler-specific language
- describe how to use available progress state without assuming proprietary memory
- point to `curriculum.md` for topics and sequencing instead of embedding the curriculum
- select guided learning, practice, or factual input gathering from learner requests and demonstrated familiarity
- introduce concepts in prerequisite order and assess understanding before dependent material
- adapt teaching and practice to observed performance without fixed question counts or mandatory readiness confirmations
- respect learner requests to pause or revisit material; pedagogical progress grants no authority for external actions
- pause at session limits without forcing mastery or advancement, and resume the saved phase
- contain only learner context that materially improves coaching
- exclude schedule syntax, model selection, notifications, project IDs, and machine-specific paths

## `curriculum.md`

Use the title `# <manifest name> curriculum`. Keep it stable: the runner never modifies it, and the learner or designer revises it deliberately. It holds what to teach and in what order; `prompt.md` holds how to coach; `state.md` holds where the learner stands.

Include:

- **Purpose:** the observable long-term capability.
- **Learning map:** the fewest strands or competencies needed, each with core ideas, practice, and progression criteria (what must be shown to advance).
- **Session rotation:** how modes and strands alternate, and what takes priority (open work, recorded gaps).
- **Review checkpoints:** when to revisit and when a skill counts as durable.
- **Current standing:** one line pointing to `state.md` as the live source. Never record progress or mastery here.

During a preservation migration, copy the selected source prompt without behavioral rewriting even when it violates these portability preferences. Record the violations as warnings and address them only in a later refinement.

Legacy interaction phases remain valid. Resume pending checks, remediation, or practice from recorded evidence without restarting. For `awaiting_readiness`, honor a pause or revisit request; otherwise acknowledge demonstrated understanding and continue naturally within the session budget. Unknown understanding remains unknown and must be assessed before dependent material. Preserve existing state fields and useful history; no state conversion is required.

## `state.md`

Use this structure for new packages:

```markdown
# Coach state

## Last completed session

<!-- Keep at most 10 entries, newest first. Preserve each retained entry verbatim. -->

- None recorded.

## Demonstrated strengths

<!-- Use one line per strength: total observation count plus up to 3 recent dated examples. -->

- None recorded.

## Recurring gaps

<!-- Use one line per gap: total observation count plus up to 3 recent dated examples. -->

- None recorded.

## Current difficulty

<!-- Keep only the current level and its evidence. Replace superseded statements. -->

- Baseline not established.

## Recent modes and scenarios

<!-- Keep a compact recent rotation. Remove entries that no longer prevent repetition. -->

- None recorded.

## Skills due for review

<!-- Keep only skills currently due. Remove each item after review. -->

- None recorded.

## Next useful target

<!-- Keep one current target. Replace it when the target changes. -->

- Select the first useful concept or practice objective from the learner's request and demonstrated familiarity.

## Open interaction

<!-- Keep only the current incomplete interaction: objective, interaction position, outstanding work, observed evidence, and remaining budget. Clear it when completed. -->

- None.
```

Treat this file as mutable canonical state. Treat state as a compact current snapshot, never an append-only diary:

- Update it only from observable evidence and after every coaching turn.
- Keep incomplete interactions distinct from completed sessions.
- Retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim.
- Compact older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples.
- Replace stale or superseded statements instead of appending another event.

Add an optional `## Curriculum standing` section after `Next useful target` when a coach has a curriculum. Keep one line per strand or competency: evidence so far and the next level. Do not infer mastery from coverage.

Keep teaching position inside `Open interaction`; no new manifest schema is required. Legacy phases such as `awaiting_readiness` remain valid; resume them naturally without imposing that gate on future concepts. Record unknown evidence or readiness as unknown, never as success or consent. Resume outstanding checks, repairs, or practice attempts without automatically restarting instruction. If legacy state records `awaiting_readiness`, honor any learner request to pause, otherwise continue naturally after acknowledging demonstrated understanding. Reteach only when requested or justified by evidence. A budget pause is distinct from concept completion.

Existing states without these details remain compatible. Preserve useful history and derive only what evidence supports; ask one focused clarification if needed. Do not reset learner progress to populate new fields.

During migration, preserve the entire existing state. If it does not match the standard headings, keep it intact and let the validator report a warning. Normalize it only in a separate refinement that demonstrably retains all useful evidence.

## `migration.json`

Create this file only when migrating existing material:

```json
{
  "schema_version": 1,
  "migrated_at": "2026-08-06T00:00:00Z",
  "sources": [
    {
      "kind": "scheduled-coach",
      "id": "judgment-coach",
      "selected_prompt": true,
      "selected_state": true,
      "prompt_sha256": "<64 lowercase hexadecimal characters>",
      "state_sha256": "<64 lowercase hexadecimal characters or null>"
    }
  ],
  "behavior_changed": false,
  "state_changed": false,
  "warnings": []
}
```

Use an ISO 8601 timestamp with a timezone. Describe sources without requiring a particular provider. Mark exactly one source as `selected_prompt`. Mark at most one source as `selected_state`; omit a state selection when no prior state exists. Compute checksums from the selected source bytes before copying. The state checksum records the imported baseline; normal runner updates may later change `state.md`.

Set `behavior_changed` to `true` for any intentional prompt behavior change, including renamed modes, altered feedback, different session bounds, or changed starting behavior. Formatting-only line-ending normalization may remain `false` when explicitly recorded in `warnings`.

Set `state_changed` to `true` when migration or refinement intentionally reorganizes or summarizes imported state. Keep it `false` during preservation-first migration. Normal evidence-based runner updates do not rewrite migration history and need not change this field.

`deployment_changed` is a legacy field. Accept it in existing records; omit it from new ones.

## Source conflicts

When saved and previously deployed prompts differ:

1. Do not select one silently.
2. Compute and report both checksums.
3. Preserve both sources until the user chooses the canonical prompt.
4. Do not claim a lossless migration until the conflict is resolved.

When a definition has no clear active use, use `draft` unless the user clearly marked it `archived`. Never infer that it should become active.
