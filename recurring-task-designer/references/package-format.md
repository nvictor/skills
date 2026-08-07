# Portable recurring-task package format

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

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`.

## `manifest.json`

Use schema version 1:

```json
{
  "schema_version": 1,
  "id": "weekly-repository-health",
  "name": "Weekly Repository Health",
  "status": "active",
  "version": 1,
  "runner_file": "runner.md",
  "task_file": "task.md",
  "state_file": "state.md",
  "schedule": {
    "enabled": true,
    "frequency": "weekly",
    "interval": 1,
    "start_date": "2026-08-10",
    "days": ["monday"],
    "local_time": "08:00",
    "timezone": "America/New_York"
  },
  "execution": {
    "minimum_minutes": 3,
    "maximum_minutes": 15,
    "interaction": "unattended"
  },
  "resources": [
    {
      "id": "source-repository",
      "kind": "directory",
      "access": "read",
      "required": true,
      "description": "Repository to inspect"
    }
  ],
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

- `schema_version`: Use `1`.
- `id`: Use lowercase ASCII letters, digits, and single hyphens. Match the package directory.
- `name`: Use the human-facing task name.
- `status`: Use `draft`, `active`, `paused`, or `archived`. This records intended source status and does not deploy anything.
- `version`: Start at `1`. Increment for behavior or execution-contract changes, not state-only updates.
- `runner_file`, `task_file`, and `state_file`: Use safe relative paths inside the package.

### Schedule

- `enabled`: Record intended scheduling state.
- `frequency`: Use `daily`, `weekly`, `monthly`, or `manual`.
- `interval`: Use a positive integer.
- `start_date`: Use local `YYYY-MM-DD` when explicitly known. It is required when `interval` is greater than `1`; otherwise use `null` when unknown.
- `days`: Use full lowercase weekday names, or an empty list when not applicable.
- `local_time`: Use 24-hour `HH:MM`, or `null` for manual or disabled schedules.
- `timezone`: Use an IANA timezone, or `null` only for manual or disabled schedules.

Preserve schedule values exactly during migration. Do not infer them from names, descriptions, or observed run times. Put native scheduler expressions and source task identifiers in a deployment adapter.

### Execution

- `minimum_minutes` and `maximum_minutes`: Use positive integers with minimum no greater than maximum. Use `null` only in a `draft` migration when the source duration bounds cannot be verified; record the gap as a migration warning and do not impose a new limit.
- `interaction`: Use `unattended`, `interactive`, or `mixed`.

An unattended task must not depend on a user answering during the run. An interactive task may pause with an open interaction. A mixed task may perform unattended work and request input only at an explicit gate.

### Resources

Declare logical resources without environment-specific bindings:

- `id`: Lowercase hyphenated identifier unique within the manifest.
- `kind`: Use `file`, `directory`, `service`, `tool`, `credential`, or `other`.
- `access`: Use `read`, `write`, `read-write`, or `invoke`.
- `required`: State whether execution must stop when the resource is unavailable.
- `description`: Explain the resource's purpose without embedding credentials.

Bind each resource to a path, connector, credential reference, or tool in the selected deployment adapter or launcher. Never store secret values in the package.

### Effects

Use `deny-by-default`. Declare every intended effect:

```json
{
  "kind": "filesystem-write",
  "resource": "report-output",
  "purpose": "Create or update the generated report"
}
```

Allowed kinds are `filesystem-write`, `external-write`, `message-send`, and `command-execution`. `resource` must reference a declared resource with compatible access. The declaration limits intended behavior but does not grant host authority.

Read-only network, filesystem, or service access belongs in `resources`; writes and executable commands also require an effect declaration. Describe human approval gates in `task.md`.

The runner's required write to the canonical `state_file` is internal continuity bookkeeping, not a task-domain effect. `continuity.update_after_run: true` declares intent to make that one write when the host permits it. It never authorizes changes to other package files or resources. Use a state handoff only when the canonical state file is unavailable or read-only.

### Continuity and privacy

- `state_authority`: Use `package`.
- `read_before_run`: Require state to be read before execution.
- `update_after_run`: Require an update after every attempted run, including blocked, no-op, partial, and failed outcomes.
- `handoff_when_read_only`: Require a complete replacement-state handoff when the agent cannot write.
- `privacy`: Use `private`, `internal`, or `public`.

## `runner.md`

Make `runner.md` the provider-neutral entrypoint. It must:

- resolve canonical files from the package root supplied by the launcher or current directory
- read manifest, task instructions, and canonical state before execution
- resolve only the deployment adapter explicitly selected by the launcher
- check resources, host permissions, approval gates, effects, and idempotency before acting
- treat no-op, blocked, partial, failed, and successful outcomes distinctly
- verify the definition of done before claiming success
- update state after every attempted run
- reread state immediately before writing and merge newer evidence
- retain no more than ten recent outcomes
- preserve uncertain or partial external effects precisely
- leave manifest, task, runner, migration record, and adapters unchanged
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

Use logical resource identifiers from the manifest. Keep schedules, paths, provider names, model settings, credentials, notifications, native scheduler syntax, and project identifiers outside this file.

During preservation migration, copy the selected source instructions without behavioral rewriting even when they violate the preferred headings or portability rules. Record warnings and address them only in a separate refinement.

## `state.md`

Use this baseline for new packages:

```markdown
# Task state

## Last attempted run

- None recorded.

## Last successful run

- None recorded.

## Current checkpoint

- No checkpoint required.

## Recent outcomes

- None recorded.

## Pending work

- None.

## Known failures

- None.

## Open interaction

- None.
```

Record only observable facts. Keep at most ten recent outcomes and fold durable information into other sections. Distinguish completed work from incomplete interaction. Record timestamps with explicit timezone offsets when available.

During migration, preserve the complete existing state. If none exists, use the baseline and record that no state source was imported. Normal run updates do not change migration provenance.

## `migration.json`

Create this file only for migrations:

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

Use a timezone-aware ISO 8601 timestamp. Select exactly one task source and at most one state source. Compute `task_sha256` from the selected source bytes and `packaged_task_sha256` from the resulting `task.md`. Record byte-only transformations such as `added-final-newline` in `normalizations`. Leave `behavior_changed` false only when the packaged instructions are semantically identical and every byte difference is fully explained. Set all change flags accurately.

## Deployment adapters

Use optional JSON adapters for settings with no canonical equivalent, including:

- provider and native source identifiers
- absolute paths and logical resource bindings
- model, reasoning, working-directory, and environment settings
- notification and delivery policy
- native schedule expressions, retry, concurrency, and timeout settings
- the minimal launcher prompt

Do not duplicate canonical task instructions, task state, or portable schedule in an adapter. Another agent may ignore an adapter it cannot use.

## Source conflicts

When saved and deployed instructions differ:

1. Preserve both sources and compute both checksums.
2. Do not select one silently.
3. Ask the user which source is canonical.
4. Do not claim a lossless migration until the conflict is resolved.

When schedule, timezone, or enabled status cannot be verified, use a disabled manual schedule and `draft` status, preserve observed evidence in the deployment adapter, and record a migration warning. Never infer an active schedule.
