# Portable coach package format

Read this file completely for create, refine, or migrate operations involving a package.

## Contents

- Package contents
- `manifest.json`
- `runner.md`
- `prompt.md`
- `state.md`
- `migration.json`
- `deployments/`
- Source conflicts

## Package contents

Use this layout:

```text
<coach-id>/
├── manifest.json
├── runner.md
├── prompt.md
├── state.md
├── migration.json    # migrations only
└── deployments/      # optional platform adapters
    └── <platform>.json
```

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`.

## `manifest.json`

Use JSON because it is dependency-free, machine-validatable, and broadly understood by AI agents and schedulers. Keep platform-specific settings outside the canonical core files.

Required shape:

```json
{
  "schema_version": 2,
  "id": "judgment-coach",
  "name": "Judgment Coach",
  "status": "active",
  "version": 1,
  "runner_file": "runner.md",
  "prompt_file": "prompt.md",
  "state_file": "state.md",
  "schedule": {
    "enabled": true,
    "frequency": "weekly",
    "interval": 1,
    "start_date": "2026-07-20",
    "days": ["monday", "thursday"],
    "local_time": "07:20",
    "timezone": "America/New_York"
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
- `name`: Use the human-facing coach name.
- `status`: Use `draft`, `active`, `paused`, or `archived`. This describes intended source state and does not itself deploy anything.
- `version`: Start at `1`. Increment when coaching behavior changes. Do not increment for state-only updates.
- `runner_file`: Use a safe relative path, normally `runner.md`.
- `prompt_file`: Use a safe relative path, normally `prompt.md`.
- `state_file`: Use a safe relative path, normally `state.md`.
- `schedule.enabled`: Set whether the intended recurring schedule is enabled.
- `schedule.frequency`: Use `daily`, `weekly`, `monthly`, or `manual`.
- `schedule.interval`: Use a positive integer.
- `schedule.start_date`: Use local calendar date `YYYY-MM-DD` when the source has an explicit start date. It is required when `interval` is greater than `1` so another scheduler can reproduce the recurrence phase. Use `null` when the source has no explicit anchor.
- `schedule.days`: Use full lowercase weekday names. Use an empty list when not applicable.
- `schedule.local_time`: Use 24-hour `HH:MM`, or `null` when the schedule is manual or disabled.
- `schedule.timezone`: Use an explicit IANA timezone, or `null` only when the schedule is manual or disabled. Preserve the source timezone during migration even when it appears incorrect; add a warning instead.
- `session.minimum_minutes` and `maximum_minutes`: Use positive integers with minimum no greater than maximum.
- `session.interaction`: Use `conversational`, `self-contained`, or `mixed`.
- `continuity.state_authority`: Use `package`; `state.md` is authoritative across agents.
- `continuity.read_before_session`: Require the runner to read state before coaching.
- `continuity.update_after_turn`: Require a write after every coaching turn, including turns that leave an interaction open.
- `continuity.handoff_when_read_only`: Require a complete state-file replacement block when the agent cannot write files.
- `privacy`: Use `private`, `internal`, or `public`. Prefer `private` for personal coaching.

Do not put model names, provider IDs, project IDs, working directories, notification settings, or native scheduler expressions in the manifest. Store those in an optional platform adapter under `deployments/` or in live deployment configuration.

## `deployments/`

Use optional deployment adapters to preserve settings that have no portable equivalent, such as a provider's model identifier, reasoning level, project target, execution environment, working directory, or notification policy.

Keep each adapter as JSON named for its platform. It may preserve a native source ID for audit and update operations. Do not duplicate the behavioral prompt, progress state, or portable schedule in an adapter; reference the canonical package files instead. Another agent may ignore an adapter it cannot use.

Use a minimal platform launcher as the deployed prompt. The launcher supplies the package root and tells the agent to follow `runner.md`. Machine-specific paths belong in this launcher or adapter, not in canonical files.

## `runner.md`

Make `runner.md` the portable entrypoint. It must:

- resolve `manifest.json`, `prompt.md`, and `state.md` from the package root supplied by the launcher or current working directory
- read the manifest, behavioral prompt, and canonical state before coaching
- treat `prompt.md` as behavior and `state.md` as the cross-agent continuity authority
- update state after every coaching turn, recording an open interaction when the session is incomplete
- reread state immediately before writing and merge newer evidence rather than overwrite it
- treat state as a compact current snapshot, never an append-only diary
- retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim
- compact older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples
- replace stale or superseded statements instead of appending another event
- preserve evidence and avoid invented history
- avoid modifying the manifest, prompt, runner, migration record, or deployment adapters
- emit a complete replacement `state.md` in a clearly labeled handoff block when file writing is unavailable
- avoid discussing file mechanics unless access fails or a conflict needs user judgment

Keep the runner provider-neutral and identical across packages whenever the continuity contract is the same.

## `prompt.md`

Make `prompt.md` the canonical behavioral instruction. It must:

- be provider-neutral
- be self-contained enough to paste into a capable AI agent
- use “session” rather than scheduler-specific language
- describe how to use available progress state without assuming proprietary memory
- contain only learner context that materially improves coaching
- exclude schedule syntax, model selection, notifications, project IDs, and machine-specific paths

During a preservation migration, copy the selected source prompt without behavioral rewriting even when it violates these portability preferences. Record the violations as warnings and address them only in a later refinement.

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

- Establish a baseline with the first bounded exercise.

## Open interaction

<!-- Keep only the current incomplete interaction. Clear it when completed. -->

- None.
```

Treat this file as mutable canonical state. Treat state as a compact current snapshot, never an append-only diary:

- Update it only from observable evidence and after every coaching turn.
- Keep incomplete interactions distinct from completed sessions.
- Retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim.
- Compact older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples.
- Replace stale or superseded statements instead of appending another event.

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
  "deployment_changed": false,
  "warnings": []
}
```

Use an ISO 8601 timestamp with a timezone. Describe sources without requiring a particular provider. Mark exactly one source as `selected_prompt`. Mark at most one source as `selected_state`; omit a state selection when no prior state exists. Compute checksums from the selected source bytes before copying. The state checksum records the imported baseline; normal runner updates may later change `state.md`.

Set `behavior_changed` to `true` for any intentional prompt behavior change, including renamed modes, altered feedback, different session bounds, or changed starting behavior. Formatting-only line-ending normalization may remain `false` when explicitly recorded in `warnings`.

Set `state_changed` to `true` when migration or refinement intentionally reorganizes or summarizes imported state. Keep it `false` during preservation-first migration. Normal evidence-based runner updates do not rewrite migration history and need not change this field.

Set `deployment_changed` to `true` only if a live scheduled task was changed. Package creation alone leaves it `false`.

## Source conflicts

When saved and deployed prompts differ:

1. Do not select one silently.
2. Compute and report both checksums.
3. Preserve both sources until the user chooses the canonical prompt.
4. Do not claim a lossless migration until the conflict is resolved.

When a definition exists without a live deployment, use `draft` unless the user clearly marked it `archived`. Never infer that it should become active.
