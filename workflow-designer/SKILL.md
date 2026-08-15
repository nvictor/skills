---
name: workflow-designer
description: Design, review, refine, package, discover, select, inspect, resume, complete, and run portable finite AI workflows whose canonical procedure, execution state, durable memory, and workspace selection survive changes of agent or context. Use when creating or managing a resumable workflow package, choosing a user-owned workflow root, handling root `state.json`, invoking `workflow:list`, `workflow:activate`, `workflow:status`, `workflow:next`, `workflow:run`, `workflow:summary`, or `workflow:complete`, or handling a manifest containing `workflow_file`. Do not use for indefinitely scheduled operations or capability-building coaches.
---

# Workflow Designer

## Purpose

Design provider-neutral workflow packages for finite objectives that require multiple dependent steps, durable continuity, or handoff between agents. Keep the procedure, current position, and learned context in canonical files rather than conversation history. Do not perform workflow work unless the user explicitly requests `workflow:run` or otherwise clearly asks to execute or resume it.

Keep workflow discovery equally durable. Store the selected workflow in a root-level `state.json` beneath a workflow root chosen by the user. Never hardcode a root location or infer canonical selection from chat history, Git branches, modification times, or machine-specific conventions.

## Package ownership

Own a package when its manifest contains `workflow_file`. Use the manifest as the type discriminator:

- `workflow_file` identifies a finite workflow package; continue with this skill.
- `task_file` identifies a bounded, rerunnable task package; use the task designer.
- `prompt_file` identifies a coach package; use the coach designer.

Report conflicting discriminators instead of choosing silently.

Distinguish the package types by why continuity exists:

- Use a workflow when one finite objective requires dependent steps and a terminal condition.
- Use a task when one bounded operation should be safely rerunnable manually, on a schedule, or both.
- Use a coach when repetition exists to develop a learner's capability.

Allow loops inside a workflow when they lead toward its terminal condition. Do not treat an internal revise-until-approved loop as a task package.

## Workflow root

Treat the workflow root as an environment binding chosen by the user. It may live inside a project, under a shared agents directory, or in a standalone directory. Do not store its absolute path in workflow packages.

Use this root layout, allowing the user to organize packages in direct children or nested directories:

```text
<workflow-root>/
├── state.json
├── workflow-a/
└── group/
    └── workflow-b/
```

Store only selection state in root `state.json`:

```json
{
  "active": "workflow-a"
}
```

Use `null` when no workflow is selected. Store a safe relative package path from the chosen root, never an absolute path. Keep this workspace selection separate from each package's lifecycle in `state.md`.

Resolve the workflow root in this order:

1. Use a root explicitly supplied by the user.
2. Otherwise use a root already bound by the current launcher or workspace configuration.
3. Otherwise ask the user to choose a root.

Do not search arbitrary directories or assume `.workflows`, `design/agents`, or any other location.

## Select the operation

- **Create:** Design and write a new workflow package without executing it.
- **Convert:** Turn an existing plan, checklist, procedure, or project brief into a package while preserving its intent and source artifacts.
- **Review:** Inspect a package and report evidence-backed findings without editing or running it.
- **Refine:** Improve a package while preserving unrelated procedure, state, memory, and artifacts.
- **`workflow:list`:** Read only. List workflow packages beneath the chosen root, their lifecycle status, and which one is selected.
- **`workflow:activate`:** Select one nonterminal workflow by writing its safe relative path to root `state.json`. Do not change package state or execute work.
- **`workflow:status`:** Read only. Report the current position, verified progress, blockers, pending decisions, and remaining work.
- **`workflow:next`:** Read only. Identify the next valid action, its prerequisites, and why it follows. Do not execute it.
- **`workflow:summary`:** Read only. Derive a compact human or agent handoff from canonical files. Do not store the summary as another source of truth.
- **`workflow:run`:** Execute or resume the permitted amount of work, then persist truthful state and durable memory.
- **`workflow:complete`:** Verify the terminal criteria, mark the package completed, and clear the root pointer only when it selects that package. Do not use completion to bypass unfinished work.
- **`workflow:deactivate`:** Use only as an escape hatch. Clear the root pointer without changing package lifecycle state.

Treat package design, workflow execution, and external effects as separate authorities. Authorization for one never implies another.

For create, convert, refine, or review, read `references/quality-rubric.md` completely. For every root or package operation, read `references/package-format.md` completely. Copy `assets/workflow-root/state.json` when initializing a user-selected root. Copy `assets/workflow-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_workflow_package.py` before delivery. Use `scripts/manage_workflow_root.py` to initialize, list, resolve, activate, clear, and validate root selection state.

## Examples

Create without running:

```text
Use workflow-designer to create a resumable workflow for publishing my conference talk in design/agents/workflows/publish-conference-talk. Do not run it.
```

Choose and initialize a root:

```text
Use design/agents/workflows as my workflow root and initialize its state.json.
```

List and activate workflows:

```text
workflow:list in design/agents/workflows
workflow:activate publish-conference-talk in design/agents/workflows
```

Convert a plan without changing its source:

```text
Convert this migration checklist into a portable workflow package. Preserve the original file and do not perform the migration.
```

Inspect the current position:

```text
workflow:status for design/agents/workflows/build-notation-parser
```

Determine the next action without performing it:

```text
workflow:next for design/agents/workflows/build-notation-parser
```

Resume execution:

```text
workflow:run design/agents/workflows/build-notation-parser through the next safe checkpoint.
```

Produce a handoff:

```text
workflow:summary for design/agents/workflows/build-notation-parser
```

Use this provider-neutral launcher form, substituting the actual package root and operation:

```text
Perform `workflow:<operation>` on the portable workflow package at `<package-root>`. Read and follow `runner.md`. Treat `state.md` and `memory.md` as canonical cross-agent continuity.
```

When selecting by workflow root, use this form:

```text
Perform `workflow:<operation>` using the user-selected workflow root at `<workflow-root>`. Resolve the package from root `state.json`, then follow its `runner.md`.
```

## Resolve a workflow

Resolve the target for `workflow:status`, `workflow:next`, `workflow:run`, `workflow:summary`, or `workflow:complete` in this order:

1. Use an explicit workflow id or package path from the user.
2. Otherwise use the relative package path in root `state.json`.
3. Otherwise use the sole nonterminal workflow beneath the root for this operation only.
4. Otherwise report the nonterminal candidates and require selection.

Do not persist the sole-candidate fallback. Only `workflow:activate` changes selection. An explicitly targeted operation does not activate that workflow unless the user also requests activation.

Treat `draft`, `in_progress`, `paused`, and `blocked` as nonterminal. Treat `completed` and `abandoned` as terminal. Use “active” only for workspace selection; use `in_progress` for package execution lifecycle.

## Design workflow

### 1. Inspect the complete context

Use the request, source plans, existing package files, working artifacts, current state, durable memory, and relevant external evidence. Identify separately:

- the finite objective and terminal condition
- ordered steps, dependencies, branches, loops, and approval gates
- verified completed work and current position
- blockers and pending decisions
- durable decisions, discoveries, and rejected approaches
- working artifacts and required capabilities
- intended external, destructive, costly, or irreversible effects

Do not reconstruct claimed history from chat when canonical files exist. Do not silently resolve conflicts among the procedure, state, memory, and artifacts.

### 2. Complete the workflow brief

Determine only what materially affects execution:

- the goal and observable completion criteria
- the smallest useful steps or phases
- entry requirements and completion evidence for each step
- transition rules, including branches and loops
- safe checkpoints and useful resume points
- decisions that require user input
- state that answers where execution is now
- memory that future steps need to know
- constraints, resources, verification, and authority boundaries

Ask only when a missing choice would materially change the workflow or its safety. Prefer explicit completion evidence over vague outcomes.

### 3. Design finite control flow

Give every workflow one reachable terminal condition. Use the fewest steps that preserve meaningful dependencies and resumability. Keep domain-specific concepts inside `workflow.md`; do not teach the generic runtime about specs, audits, branches, findings, chapters, or other lifecycle-specific nouns.

For each step, define enough information to determine:

1. when the step is eligible
2. what outcome it should produce
3. what evidence proves it complete
4. where execution may transition next
5. when it must block, pause, loop, or request a decision

Prefer Markdown instructions over formal workflow-engine syntax. Add explicit transition rules only where order, branching, or looping would otherwise be ambiguous.

### 4. Separate state from memory

Put execution position in `state.md`:

- lifecycle status and current step
- completed steps and their evidence
- blockers and pending decisions
- working artifacts and open operation

Put durable semantic context in `memory.md`:

- decisions and their rationale
- discoveries future steps need
- rejected approaches worth not repeating
- stable context that would otherwise be lost

Do not duplicate logs or conversational exhaust. Move durable conclusions out of transient state, compact obsolete detail, and preserve uncertainty honestly. Never invent completed work, decisions, evidence, or history.

### 5. Write and validate the package

Write `manifest.json`, `workflow.md`, `state.md`, `memory.md`, and `runner.md` according to `references/package-format.md`. Keep the manifest deliberately small. Put lifecycle status in state, not the manifest. Keep provider names, model settings, machine paths, credentials, scheduler syntax, and chat history out of canonical files unless a workflow's explicit domain constraint genuinely requires a named environment.

When the user asks to initialize a chosen workflow root, create its `state.json` with `active: null`. Do not create or select a root merely because a package was created. Keep `runner.md` generic and identical across packages whenever the runtime contract is unchanged. Validate every created or refined package and every changed root state. Fix errors before delivery and report warnings that require judgment.

## Control-plane behavior

### Read-only operations

For `workflow:list`, read root `state.json`, discover manifests containing `workflow_file` beneath the chosen root, and report their relative paths, ids, lifecycle statuses, and selection. Ignore coach and task packages.

For `workflow:status`, `workflow:next`, and `workflow:summary`:

1. Resolve an explicit, selected, or sole nonterminal workflow.
2. Read the manifest and resolve the canonical files.
3. Read the procedure, state, and only the memory needed to interpret them.
4. Inspect relevant working artifacts when the operation requires verification.
5. Return the requested view without changing root or package files or performing domain work.

Treat `workflow:next` as advisory even when the next action appears harmless. Use `workflow:run` for execution.

### Selection

For `workflow:activate`, validate the target package, reject terminal or ambiguous targets, reread root `state.json`, and atomically replace `active` with the package's normalized relative path. Preserve unknown root-state fields. Do not change package `state.md`.

For `workflow:deactivate`, reread root `state.json` and atomically set `active` to `null`. Do not change the previously selected package. Treat this as an explicit escape hatch, not a routine completion step.

### Run

For `workflow:run`, follow `runner.md` from the package root. Honor an explicit scope such as one action, the next checkpoint, one phase, or completion. When scope is unspecified, perform one coherent unit of work through the next safe checkpoint; do not assume authorization to finish the whole workflow.

Before acting, confirm the current step is eligible, required inputs exist, blockers are resolved, and the requested action is within user and host authority. Treat workflow constraints as intended limits, never as a grant of permissions. Stop before unauthorized, destructive, externally visible, or unsafe effects.

Update state after every attempted execution, including blocked or partial work. Add to memory only when the run produces durable information. Reread both files immediately before writing and merge newer evidence. When writing is unavailable, return complete replacement contents as handoffs and never imply persistence succeeded.

Mark a step complete only from observable evidence. Mark the workflow complete only when its terminal criteria are satisfied. Do not equate effort, elapsed time, a plausible artifact, or an agent assertion with verified completion. After the completed package state is successfully written, clear root `state.json` only when it still points to that package. Do not clear a concurrently changed selection.

### Complete

For `workflow:complete`, resolve the target and verify every terminal criterion from current evidence without performing missing domain work. If any criterion is unmet or uncertain, report it and leave package and root state unchanged. Otherwise:

1. Reread package `state.md` and root `state.json`.
2. Mark the package lifecycle `completed` and persist any final positional state.
3. Verify the package write.
4. Set root `active` to `null` only if it still selects that package.
5. Report package completion and pointer clearing separately.

## Conversion and preservation

Convert source material before improving it:

1. Create the package alongside the source; never replace or move the source.
2. Preserve the objective, steps, constraints, known progress, and durable decisions.
3. Record ambiguity as a blocker or pending decision rather than inventing an answer.
4. Mark unverifiable progress as unverified; do not promote it to completed state.
5. Validate the package and identify refinements separately.

Do not execute domain work during conversion. Offer structural or behavioral improvements only after the preserved package exists.

## Output contract

- **Create or convert with an authorized destination:** Write and validate the package. Summarize its objective, files, initial state, validation result, and unresolved warnings. Do not run it.
- **Initialize root:** Create and validate `<workflow-root>/state.json` at the user-selected location with no active workflow.
- **Refine:** Write and validate the package. Report behavior changes separately from state or memory changes.
- **Review:** Return prioritized, evidence-backed findings without editing or running.
- **`workflow:list`:** Report discovered workflow ids, relative paths, lifecycle statuses, and the selected workflow without editing.
- **`workflow:activate`:** Report the selected workflow and verified root-state write without changing package lifecycle state.
- **`workflow:status`:** Report lifecycle status, current step, verified completed work, blockers, pending decisions, working artifacts, and remaining steps.
- **`workflow:next`:** Report one next valid action, prerequisites, completion evidence, and blockers. Do not act.
- **`workflow:summary`:** Return a compact derived handoff covering goal, position, progress, durable decisions, blockers, and next action.
- **`workflow:run`:** Report attempted work, verified outcome, current position, new durable memory, unresolved work, and whether canonical files were written or handed off.
- **`workflow:complete`:** Report verified terminal evidence, package-state persistence, and whether the matching root pointer was cleared.
- **`workflow:deactivate`:** Report pointer clearing separately and leave package state unchanged.

Never claim execution, completion, state persistence, or preserved behavior without verifying it.
