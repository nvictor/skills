# Portable coach package format

Read this file completely for create, refine, or migrate operations involving a package.

## Contents

- Package contents
- `manifest.json`
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
  "schema_version": 1,
  "id": "judgment-coach",
  "name": "Judgment Coach",
  "status": "active",
  "version": 1,
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
    "read_before_session": true,
    "update_after_session": true
  },
  "privacy": "private"
}
```

### Field rules

- `schema_version`: Use `1`.
- `id`: Use lowercase ASCII letters, digits, and hyphens. Match the directory name.
- `name`: Use the human-facing coach name.
- `status`: Use `draft`, `active`, `paused`, or `archived`. This describes intended source state and does not itself deploy anything.
- `version`: Start at `1`. Increment when coaching behavior changes. Do not increment for state-only updates.
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
- `continuity`: State whether the runner should read state before and update it after a session.
- `privacy`: Use `private`, `internal`, or `public`. Prefer `private` for personal coaching.

Do not put model names, provider IDs, project IDs, working directories, notification settings, or native scheduler expressions in the manifest. Store those in an optional platform adapter under `deployments/` or in live deployment configuration.

## `deployments/`

Use optional deployment adapters to preserve settings that have no portable equivalent, such as a provider's model identifier, reasoning level, project target, execution environment, working directory, or notification policy.

Keep each adapter as JSON named for its platform. It may preserve a native source ID for audit and update operations. Do not duplicate the behavioral prompt, progress state, or portable schedule in an adapter; reference the canonical package files instead. Another agent may ignore an adapter it cannot use.

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

- None recorded.

## Demonstrated strengths

- None recorded.

## Recurring gaps

- None recorded.

## Current difficulty

- Baseline not established.

## Recent modes and scenarios

- None recorded.

## Skills due for review

- None recorded.

## Next useful target

- Establish a baseline with the first bounded exercise.

## Open interaction

- None.
```

Update state only from observable evidence. Keep incomplete interactions distinct from completed sessions. Preserve enough recent history to avoid mechanical repetition while keeping the record compact.

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

Use an ISO 8601 timestamp with a timezone. Describe sources without requiring a particular provider. Mark exactly one source as `selected_prompt`. Mark at most one source as `selected_state`; omit a state selection when no prior state exists. Compute checksums from the selected source bytes before copying. The validator verifies unchanged destination files against them.

Set `behavior_changed` to `true` for any intentional prompt behavior change, including renamed modes, altered feedback, different session bounds, or changed starting behavior. Formatting-only line-ending normalization may remain `false` when explicitly recorded in `warnings`.

Set `state_changed` to `true` when the destination state is intentionally reorganized or summarized. Keep it `false` during preservation-first migration. Preserve the original state separately before any later normalization.

Set `deployment_changed` to `true` only if a live scheduled task was changed. Package creation alone leaves it `false`.

## Source conflicts

When saved and deployed prompts differ:

1. Do not select one silently.
2. Compute and report both checksums.
3. Preserve both sources until the user chooses the canonical prompt.
4. Do not claim a lossless migration until the conflict is resolved.

When a definition exists without a live deployment, use `draft` unless the user clearly marked it `archived`. Never infer that it should become active.
