---
name: recurring-task-designer
description: Design, review, refine, migrate, package, run, and explicitly deploy portable recurring AI tasks for monitoring, reporting, maintenance, synchronization, content generation, reminders, audits, interactive routines, and other repeated workflows. Use when creating or improving a scheduled task, automation, routine, monitor, recurring workflow, agent-neutral task package, or standalone recurring-task prompt.
---

# Recurring Task Designer

## Purpose

Design provider-neutral recurring tasks whose behavior, schedule, effects, resource requirements, and durable state can survive a change of AI agent, machine, or scheduler. Support unattended, interactive, and mixed tasks across domains. Do not execute or deploy a task unless the user explicitly asks.

## Select the operation

- **Create:** Design a new task. Create a package when the user provides or implies a destination; otherwise return a standalone task definition.
- **Review:** Inspect an existing task and report evidence-backed findings without changing it.
- **Refine:** Improve an existing definition or package while preserving unrelated configuration and state.
- **Migrate:** Convert a legacy prompt, skill, scheduled task, or automation into a package without changing behavior or live deployment.
- **Prompt only:** Return one self-contained, provider-neutral task definition ready to paste into an AI agent.
- **Run:** Execute a validated package only when explicitly requested.
- **Deploy:** Create or change a live schedule only when explicitly requested.

Treat package creation, execution, and deployment as separate authorities. Authorization for one never implies another.

For create, refine, or review, read `references/quality-rubric.md` completely. For every package operation, also read `references/package-format.md` completely. Copy `assets/recurring-task-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_recurring_task_package.py` before delivery.

## Examples

Create without deploying:

```text
Use the recurring-task-designer skill to create a weekly repository health report in design/agents/recurring-tasks/repository-health. Schedule it for Mondays at 08:00 America/New_York, but do not run or deploy it.
```

Migrate without changing the live task:

```text
Use the recurring-task-designer skill to migrate this scheduled task into design/agents/recurring-tasks/<task-id>. Preserve its instructions, state, schedule, timezone, enabled status, and deployment settings. Do not run it or change the live schedule.
```

Review without editing:

```text
Review design/agents/recurring-tasks/task-log-maintenance for idempotency, effect safety, portability, failure handling, and useful recurring behavior. Report findings only.
```

Run an existing package:

```text
Run the portable recurring task at design/agents/recurring-tasks/task-log-maintenance once. Follow runner.md, including its resource, effect, verification, and state rules. Do not alter its schedule.
```

Run a portable package across agents:

```text
Run the portable recurring-task package at design/agents/recurring-tasks/weekly-tasklog-recategorize. Read and follow `runner.md`. Treat `state.md` as the canonical cross-agent state.
```

## Workflow

### 1. Inspect the complete source

Use the request, saved task definition, deployed prompt, scheduler configuration, execution history, task state, resource bindings, and prior outputs. Identify separately:

- canonical or saved instructions
- deployed instructions
- schedule, timezone, and enabled state
- runtime and delivery settings
- required resources and available capabilities
- intended writes and external actions
- durable state, checkpoints, and incomplete work

Do not silently choose between conflicting sources. Preserve each source until the user selects the intended one. Do not infer a schedule from a task name or description when live metadata may exist.

### 2. Complete the task brief

Determine only what materially affects execution:

- the recurring outcome and why repetition is useful
- inputs, resources, preconditions, and freshness requirements
- unattended, interactive, or mixed execution
- per-run duration and schedule
- definition of done and verifiable outputs
- no-op conditions and idempotency key or strategy
- partial-success, retry, and escalation behavior
- state and checkpoint requirements
- intended filesystem, service, messaging, or command effects
- privacy, safety, cost, and domain constraints

Ask only when a missing choice would materially change behavior or safety. Keep schedules and environment bindings out of `task.md`; put portable scheduling in the manifest and environment-specific bindings in deployment adapters.

### 3. Design one bounded run

Write operational instructions another capable agent can follow without private platform memory. Define:

1. how to resolve and validate inputs
2. how to determine whether work is already complete or unnecessary
3. the ordered procedure and approval gates
4. the exact allowed effects
5. how to verify the definition of done
6. what to report for success, no-op, blocked, partial, or failed outcomes
7. what state to preserve for the next run

Prefer deterministic checks over vague judgment. Require an agent to stop before an undeclared effect, unavailable capability, ambiguous destructive action, or missing authorization. Never treat host access as permission to exceed the package effect boundary.

### 4. Design recurrence and continuity

Make repeated runs safe and useful:

- define a stable idempotency strategy for effectful work
- make no-op a valid, observable outcome
- prevent blind retries after uncertain external effects
- record partial effects precisely so a later agent does not duplicate them
- keep task state compact and evidence-based
- distinguish attempted, successful, blocked, partial, failed, and no-op runs
- preserve incomplete interactions separately from completed runs
- retain at most ten recent outcomes, folding durable information into checkpoints, pending work, or known failures

Treat package `state.md` as canonical across agents. Reread it immediately before writing and merge newer evidence. When writing is unavailable, return the complete replacement state as a handoff.

### 5. Write and validate artifacts

For packages, write the manifest, runner, task, and state according to `references/package-format.md`. Include `migration.json` only for migrations. Keep the generic runner identical whenever the execution contract is unchanged.

Use logical resource identifiers in canonical files. Put absolute paths, connector identifiers, model settings, notification policy, native scheduler syntax, and credentials references in a deployment adapter. Never store credential values in the package.

Run the package validator after every create, refine, or migrate operation. Fix errors before delivery and report warnings that require judgment.

## Preservation-first migration

Perform migration and refinement as separate passes.

During migration:

1. Create the package alongside the source; never replace or move source files.
2. Copy the selected task instructions without rewriting behavior.
3. Preserve the complete state when one exists; never invent or summarize away history.
4. Recover schedule and deployment metadata from authoritative sources. Preserve suspicious values and warn instead of normalizing them.
5. Record provenance, checksums, conflicts, missing metadata, and portability warnings in `migration.json`.
6. Mark undocumented or unverifiable definitions as `draft` rather than activating them.
7. Set `behavior_changed`, `state_changed`, and `deployment_changed` accurately.
8. Validate the package and report what a later refinement or deployment would change.

Do not abstract paths, strengthen safety rules, add idempotency, change schedules, reset state, execute the task, or update a live deployment during the preservation pass. Offer these as a separate refinement after the lossless package exists.

## Effect and execution boundary

Treat manifest effects as the maximum intended authority and host permissions as the maximum available authority. Execute only their intersection.

Treat the continuity-required write to the canonical `state_file` as internal bookkeeping authorized only by the continuity contract. It is not a task-domain effect and never permits changes to other package files or resources.

Before an effect:

- confirm it is declared by kind, resource, and purpose
- confirm the resource binding is unambiguous
- confirm the host permits it
- confirm required approval is present
- confirm the task's idempotency and retry rules make it safe

If any check fails, stop before the effect, record a blocked outcome, and state the missing requirement. Do not claim success or saved state when either is unverified.

## Execution and deployment

For a run, follow `runner.md` from the package root. Do not compute or alter future schedules. Report task effects and state changes separately.

For deployment, use the current platform's native scheduling capability, preserve unrelated live settings, and use a minimal launcher that supplies the package root, names any deployment adapter, and delegates to `runner.md`. Verify the resulting schedule, timezone, enabled state, resource bindings, effect permissions, and launcher. Retain a recoverable snapshot.

## Output contract

- **Create, refine, or migrate with an authorized destination:** Write and validate the package, then summarize artifacts, validation, behavior changes, state handling, and unresolved warnings.
- **Review:** Return prioritized, evidence-backed findings without editing.
- **Prompt only:** Return only the completed task definition, without a preface, fence, placeholders, or TODOs.
- **Run:** Report outcome, verified effects, outputs, and whether state was written or handed off.
- **Deploy:** Report package changes and live deployment changes separately.

Never claim behavior preservation, successful effects, state persistence, or deployment changes unless each was verified.
