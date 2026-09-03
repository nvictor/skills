# Portable task package format

Read this file completely for create, refine, migrate, run, or deploy operations involving a package.

## Contents

- Package contents
- `manifest.json`
- `runner.md`
- `task.md`
- `state.md`
- `migration.json`
- Deployment adapters
- Source conflicts

## Package contents

Use this layout:

```text
<task-id>/
├── manifest.json
├── runner.md
├── task.md
├── state.md
├── migration.json    # migrations only
└── deployments/      # optional environment adapters
    └── <platform>.json
```

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`. Package roots are user-chosen; never assume a universal tasks directory.

## `manifest.json`

Create and refine packages with schema version 2. This manual package has no `schedule`:

```json
{
  "schema_version": 2,
  "id": "repository-health",
  "name": "Repository Health",
  "status": "active",
  "version": 1,
  "runner_file": "runner.md",
  "task_file": "task.md",
  "state_file": "state.md",
  "execution": {
    "minimum_minutes": 3,
    "maximum_minutes": 15,
    "interaction": "unattended"
  },
  "resources": [],
  "effects": {
    "policy": "deny-by-default",
    "allowed": []
  },
  "continuity": {
    "state_authority": "package",
    "read_before_run": true,
    "update_after_run": true,
    "handoff_when_read_only": true
  },
  "privacy": "private"
}
```

### Core fields

- `schema_version`: Use `2` for new or refined packages. Schema v1 remains readable only for compatibility.
- `id`: Use lowercase ASCII letters, digits, and single hyphens. Match the package directory.
- `name`: Use the human-facing task name.
- `status`: Use `draft`, `active`, `paused`, or `archived`. This records source intent and does not deploy anything.
- `version`: Start at `1`. Increment for behavior or execution-contract changes, not state-only updates or a behavior-preserving schema migration.
- `runner_file`, `task_file`, and `state_file`: Use safe relative paths inside the package.

### Optional schedule

Omit `schedule` for a manual/on-demand task. The package may be run only when explicitly invoked and has no portable scheduling intent.

Include `schedule` only when the user explicitly requests or the source already contains scheduling intent:

```json
"schedule": {
  "enabled": true,
  "frequency": "weekly",
  "interval": 1,
  "start_date": "2026-08-10",
  "days": ["monday"],
  "local_time": "08:00",
  "timezone": "America/New_York"
}
```

- `enabled`: Record intended scheduling state.
- `frequency`: Use `daily`, `weekly`, or `monthly`. Schema v2 never uses `manual`.
- `interval`: Use a positive integer.
- `start_date`: Use local `YYYY-MM-DD` when explicitly known. It is required when `interval` is greater than `1`; otherwise use `null` when unknown. An enabled monthly schedule requires it as an anchor.
- `days`: Use full lowercase weekday names for weekly schedules, or an empty list when not applicable.
- `local_time`: Use 24-hour `HH:MM` for enabled schedules. It may be `null` only when the schedule is disabled.
- `timezone`: Use an IANA timezone for enabled schedules. It may be `null` only when the schedule is disabled.

A scheduled package may also be run manually. Manual execution must not change, postpone, advance, or otherwise affect its schedule or next scheduled run.

### Schema-v1 compatibility

Validate schema-v1 packages with a deprecation warning rather than an error. They must retain the v1-required `schedule` object. Their frequency may be `daily`, `weekly`, `monthly`, or `manual`; an enabled v1 schedule cannot use `manual`. Create and refine only schema-v2 packages, and migrate a known v1 package when touching it.

### Execution

- `minimum_minutes` and `maximum_minutes`: Use positive integers with minimum no greater than maximum. Use `null` only in a `draft` migration when bounds cannot be verified; record the gap and do not impose a new limit.
- `interaction`: Use `unattended`, `interactive`, or `mixed`.

An unattended task must not depend on an answer during the run. An interactive task may pause with an open interaction. A mixed task may perform unattended work and request input only at an explicit gate.

### Resources

Declare logical resources without environment-specific bindings:

- `id`: Lowercase hyphenated identifier unique within the manifest.
- `kind`: Use `file`, `directory`, `service`, `tool`, `credential`, or `other`.
- `access`: Use `read`, `write`, `read-write`, or `invoke`.
- `required`: State whether execution must stop when unavailable.
- `description`: Explain purpose without embedding credentials.

Bind resources to paths, connectors, credential references, or tools in a deployment adapter or launcher. Never store secret values in the package.

### Effects

Use `deny-by-default`. Declare every intended effect:

```json
{
  "kind": "filesystem-write",
  "resource": "report-output",
  "purpose": "Create or update the generated report"
}
```

Allowed kinds are `filesystem-write`, `external-write`, `message-send`, and `command-execution`. `resource` must reference a compatible declared resource. The declaration limits intended behavior but does not grant host authority.

Read-only access belongs in `resources`; writes and executable commands also require an effect declaration. Describe human approval gates in `task.md`.

The required `state_file` write is continuity bookkeeping, not a task-domain effect. It never authorizes changes to other package files or resources.

### Continuity and privacy

- `state_authority`: Use `package`.
- `read_before_run`: Require state to be read before execution.
- `update_after_run`: Require an update after every attempted run, including blocked, no-op, partial, and failed outcomes.
- `handoff_when_read_only`: Require a complete replacement-state handoff when writing is unavailable.
- `privacy`: Use `private`, `internal`, or `public`.

## `runner.md`

Make `runner.md` the provider-neutral entrypoint. It must:

- resolve canonical files from the supplied package root or current directory
- read manifest, task instructions, and canonical state before execution
- resolve only the deployment adapter explicitly selected by the launcher
- check resources, host permissions, approval gates, effects, and idempotency before acting
- treat no-op, blocked, partial, failed, and successful outcomes distinctly
- verify the definition of done before claiming success
- update state after every attempted run
- reread state immediately before writing and merge newer evidence
- treat state as a compact current snapshot, never an append-only diary
- replace stale or superseded checkpoints, pending work, failures, and interactions instead of appending another event
- retain no more than ten recent outcomes
- preserve uncertain or partial external effects precisely
- leave manifest, task, runner, migration record, and adapters unchanged
- never alter scheduling during a run
- emit a complete replacement `state.md` under `State handoff` when writing is unavailable

Keep the runner generic and identical across packages whenever this contract is unchanged.

## `task.md`

For a new task, use these headings:

```markdown
# Purpose

## Inputs and prerequisites

## Procedure

## Definition of done

## Idempotency and no-op behavior

## Failure and retry behavior

## Outputs

## State updates

## Constraints
```

Use logical resource identifiers. Keep schedules, paths, provider names, model settings, credentials, notifications, native scheduler syntax, and project identifiers outside this file.

During preservation migration, copy selected source instructions without behavioral rewriting. Record warnings and refine only in a separate pass.

## `state.md`

Use this baseline for new packages:

```markdown
# Task state

## Last attempted run

<!-- Keep one entry. Replace it after each attempted run. -->

- None recorded.

## Last successful run

<!-- Keep one entry. Replace it only after a verified successful run. -->

- None recorded.

## Current checkpoint

<!-- Keep only the current checkpoint. Replace or clear it when it changes. -->

- No checkpoint required.

## Recent outcomes

<!-- Keep at most 10 concise outcomes, newest first. -->

- None recorded.

## Pending work

<!-- Keep only unresolved work. Remove or replace resolved and superseded items. -->

- None.

## Known failures

<!-- Keep only failures that still affect retries or diagnosis. Remove obsolete items. -->

- None.

## Open interaction

<!-- Keep only the current incomplete interaction. Clear it when completed. -->

- None.
```

Treat state as a compact current snapshot, never an append-only diary:

- Record only observable facts.
- Replace stale or superseded checkpoints, pending work, failures, and interactions instead of appending another event.
- Keep at most ten recent outcomes, newest first, and fold older durable information into other sections.
- Distinguish completed work from incomplete interaction.
- Record timestamps with explicit timezone offsets when available.

During migration, preserve complete existing state. If none exists, use the baseline and record that no state source was imported. Normal run updates do not change migration provenance.

## `migration.json`

Create this file only for migrations. Its schema remains version 1:

```json
{
  "schema_version": 1,
  "migrated_at": "2026-08-07T00:00:00-04:00",
  "sources": [
    {
      "kind": "scheduled-task",
      "id": "source-task-id",
      "selected_task": true,
      "selected_state": false,
      "task_sha256": "<64 lowercase hexadecimal characters>",
      "packaged_task_sha256": "<64 lowercase hexadecimal characters>",
      "normalizations": [],
      "state_sha256": null
    }
  ],
  "behavior_changed": false,
  "state_changed": false,
  "deployment_changed": false,
  "warnings": []
}
```

Use a timezone-aware ISO 8601 timestamp. Select exactly one task source and at most one state source. Compute and record checksums and byte-only normalizations. Set all change flags accurately.

## Deployment adapters

Use optional JSON adapters for settings with no canonical equivalent, including:

- provider and native source identifiers
- absolute paths and logical resource bindings
- model, reasoning, working-directory, and environment settings
- notification and delivery policy
- native schedule expressions, retry, concurrency, and timeout settings
- the minimal launcher prompt

Do not duplicate canonical instructions, state, or portable schedule in an adapter. Another agent may ignore an adapter it cannot use.

## Source conflicts

When saved and deployed instructions differ:

1. Preserve both sources and compute both checksums.
2. Do not select one silently.
3. Ask which source is canonical.
4. Do not claim a lossless migration until the conflict is resolved.

When schedule, timezone, or enabled status cannot be verified, omit `schedule`, use `draft` status, preserve observed evidence in the adapter, and record a migration warning. Never infer an active schedule.
