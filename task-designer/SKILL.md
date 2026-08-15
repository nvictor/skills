---
name: task-designer
description: Design, review, refine, migrate, package, run, and deploy portable bounded AI tasks that may run manually, on a schedule, or both. Use for repeatable monitoring, reporting, maintenance, synchronization, content generation, reminders, audits, and task packages whose manifest contains `task_file`. Do not use for multi-stage finite objectives (`workflow_file`) or capability-building coaches (`prompt_file`).
---

# Task Designer

## Purpose

Design provider-neutral tasks whose behavior, effects, resources, and durable state survive changes of agent, machine, or scheduler. A task is one bounded, safely rerunnable operation. It may be invoked manually, scheduled, or both. Do not execute a task or create or change a live schedule unless the user explicitly authorizes that action.

## Package ownership

Own a package when its manifest contains `task_file`. This includes later requests to run, schedule, automate, pause, resume, or otherwise deploy that task package.

When the package type is unknown, inspect its manifest:

- `task_file` identifies a task package; continue with this skill.
- `workflow_file` identifies a finite multi-stage workflow; use the workflow designer.
- `prompt_file` identifies a coach package; use the coach designer.

## Select the operation

- **Create:** Design a task. Create a package when the user provides or implies a destination; otherwise return a standalone definition. Create schema-v2 packages, and omit `schedule` unless scheduling was explicitly requested.
- **Review:** Inspect an existing task and report evidence-backed findings without changing it.
- **Refine:** Improve an existing definition or package while preserving unrelated configuration and state. Migrate a touched schema-v1 package to schema v2.
- **Migrate:** Convert a legacy prompt, skill, scheduled task, or automation into a package without changing behavior or live deployment.
- **Prompt only:** Return one self-contained, provider-neutral task definition ready to paste into an AI agent.
- **Run:** Execute a validated package once when explicitly requested. A manual run never changes its schedule or next scheduled run.
- **Deploy:** Create or change a live schedule only when explicitly requested. A manual package gains a schedule only through explicit scheduling authority.

Treat package creation, execution, and deployment as separate authorities. Authorization for one never implies another.

For create, refine, or review, read `references/quality-rubric.md` completely. For every package operation, also read `references/package-format.md` completely. Copy `assets/task-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_task_package.py` before delivery.

## Examples

Create a manual task without deploying:

```text
Use the task-designer skill to create an on-demand repository health check in design/agents/tasks/repository-health. Do not schedule, run, or deploy it.
```

Create a scheduled task without deploying:

```text
Use the task-designer skill to create a weekly repository health report in design/agents/tasks/repository-health. Schedule it for Mondays at 08:00 America/New_York, but do not run or deploy it.
```

Migrate without changing the live task:

```text
Use the task-designer skill to migrate this scheduled task into design/agents/tasks/<task-id>. Preserve its instructions, state, schedule, timezone, enabled status, and deployment settings. Do not run it or change the live schedule.
```

Run a manual or scheduled package once:

```text
Run the portable task package at design/agents/tasks/weekly-tasklog-recategorize using deployments/codex.json. Follow runner.md and treat state.md as canonical. Do not alter its schedule.
```

Deploy an already validated scheduled package:

```text
Use the task-designer skill to deploy design/agents/tasks/weekly-tasklog-recategorize. Preserve the package schedule, resource bindings, and effect boundaries.
```

Recommend this AI-agnostic launcher when no deployment adapter is required:

```text
Run the portable task package at `<package-root>`. Read and follow `runner.md`. Treat `state.md` as the canonical cross-agent state.
```

When a deployment adapter is required, recommend:

```text
Run the portable task package at `<package-root>` using `<deployment-adapter>`. Read and follow `runner.md`. Treat `state.md` as the canonical cross-agent state.
```

## Workflow

### 1. Inspect the complete source

Use the request, saved definition, deployed prompt, scheduler configuration, execution history, task state, resource bindings, and prior outputs. Identify separately:

- canonical and deployed instructions
- whether scheduling exists, plus timezone and enabled state
- runtime and delivery settings
- required resources and available capabilities
- intended writes and external actions
- durable state, checkpoints, and incomplete work

Do not silently choose between conflicting sources. Preserve each source until the user selects the intended one. Do not infer a schedule from a name, description, or package location.

### 2. Complete the task brief

Determine only what materially affects one run:

- the bounded outcome and when an invocation is useful
- inputs, resources, preconditions, and freshness requirements
- unattended, interactive, or mixed execution
- per-run duration and, only when requested, schedule
- definition of done and verifiable outputs
- no-op conditions and idempotency strategy
- partial-success, retry, and escalation behavior
- state and checkpoint requirements
- intended filesystem, service, messaging, or command effects
- privacy, safety, cost, and domain constraints

Ask only when a missing choice materially changes behavior or safety. Keep schedules and environment bindings out of `task.md`; put portable scheduling intent in the optional manifest `schedule` and environment-specific bindings in deployment adapters.

### 3. Design one bounded run

Write operational instructions another capable agent can follow without private platform memory. Define:

1. how to resolve and validate inputs
2. how to detect already-complete or unnecessary work
3. the ordered procedure and approval gates
4. the exact allowed effects
5. how to verify the definition of done
6. what to report for success, no-op, blocked, partial, or failed outcomes
7. what state to preserve for the next invocation

Prefer deterministic checks. Stop before an undeclared effect, unavailable capability, ambiguous destructive action, or missing authorization. Never treat host access as permission to exceed package effects.

### 4. Design rerun safety and continuity

- define a stable idempotency strategy for effectful work
- make no-op a valid, observable outcome
- prevent blind retries after uncertain external effects
- record partial effects precisely so a later agent does not duplicate them
- distinguish attempted, successful, blocked, partial, failed, and no-op runs
- preserve incomplete interactions separately from completed runs
- retain at most ten recent outcomes and fold durable facts into other state sections

Treat `state.md` as canonical across agents. Reread it immediately before writing and merge newer evidence. When writing is unavailable, return the complete replacement state as a handoff.

### 5. Write and validate artifacts

Write the manifest, runner, task, and state according to `references/package-format.md`. Include `migration.json` only for migrations. Keep the generic runner identical whenever its execution contract is unchanged.

Use logical resource identifiers in canonical files. Put absolute paths, connector identifiers, model settings, notification policy, native scheduler syntax, and credential references in a deployment adapter. Never store credential values in the package.

Run the package validator after every create, refine, or migrate operation. Fix errors before delivery and report warnings that require judgment.

## Preservation-first migration

Perform migration and refinement as separate passes.

During migration:

1. Create the package alongside the source; never replace or move source files.
2. Copy selected instructions without rewriting behavior.
3. Preserve complete existing state; never invent or summarize away history.
4. Recover scheduling and deployment metadata from authoritative sources. Preserve suspicious values and warn instead of normalizing them.
5. Record provenance, checksums, conflicts, missing metadata, and portability warnings in `migration.json`.
6. Mark undocumented or unverifiable definitions as `draft` rather than activating them.
7. Set `behavior_changed`, `state_changed`, and `deployment_changed` accurately.
8. Validate the package and report what later refinement or deployment would change.

Do not abstract paths, strengthen safety rules, add idempotency, change schedules, reset state, execute the task, or update a live deployment during the preservation pass. Offer these as a separate refinement.

## Effect and execution boundary

Treat manifest effects as maximum intended authority and host permissions as maximum available authority. Execute only their intersection.

The continuity-required write to `state_file` is internal bookkeeping authorized only by the continuity contract. It never permits changes to other package files or resources.

Before an effect, confirm its declaration, resource binding, host permission, required approval, and retry safety. If any check fails, stop before the effect, record a blocked outcome, and state the missing requirement.

## Execution and deployment

For a run, follow `runner.md` from the package root. A package without `schedule` is manual-only. A package with `schedule` may still be run manually. Never compute, create, alter, postpone, or advance future schedules during a manual run. Report task effects and state changes separately.

After creating and validating a package, recommend the exact launcher with the real package root and required adapter. Mention automation only when the user requested scheduling or the package already has scheduling intent. This does not authorize deployment.

When the user explicitly authorizes deployment:

1. Confirm `task_file` identifies a task package, resolve the selected adapter, and require a valid schema-v2 schedule. If absent, add one only from the user's explicit scheduling request.
2. Inspect the current agent's scheduler tools and authoritative documentation. Use the native mechanism directly.
3. Check for an existing automation for the same package. Update it instead of duplicating it.
4. Map schedule, timezone, enabled state, and adapter bindings without changing meaning.
5. Use a standalone scheduled job with declared resources and package-authorized effects.
6. Use the minimal launcher above. Keep runtime and native schedule settings outside canonical package files.
7. Verify the saved schedule, enabled state, package root, runner, state access, resource bindings, effects, and launcher.

## Output contract

- **Create:** Write and validate the package, summarize behavior, state handling, and warnings, then provide the exact launcher. Mention deployment only when scheduling is in scope.
- **Refine or migrate:** Write and validate, then summarize artifacts, behavior changes, state handling, and warnings.
- **Review:** Return prioritized, evidence-backed findings without editing.
- **Prompt only:** Return only the completed definition, without a preface, fence, placeholders, or TODOs.
- **Run:** Report outcome, verified effects, outputs, and whether state was written or handed off.
- **Deploy:** Report package changes and live deployment changes separately.

Never claim behavior preservation, successful effects, state persistence, or deployment changes unless each was verified.
