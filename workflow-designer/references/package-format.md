# Portable workflow package format

Read this file completely for every operation involving a workflow package.

## Contents

- Workflow root
- Workspace binding
- Root `state.json`
- Workflow resolution
- Package contents
- `manifest.json`
- `workflow.md`
- `state.md`
- `memory.md`
- `runner.md`
- Control operations
- Source conflicts

## Workflow root

Let the user choose the workflow root. Treat it as an environment binding, not part of any portable package. Do not prescribe `.workflows`, `design/agents`, a home-directory location, or another fixed convention.

Allow workflow packages as direct children or in user-organized subdirectories:

```text
<workflow-root>/
├── state.json
├── workflow-a/
│   └── ...
└── group/
    └── workflow-b/
        └── ...
```

Resolve the root from an explicit user-supplied path or an existing launcher/workspace binding. Ask the user when neither is available. Do not search arbitrary filesystem locations or infer the root from chat history.

## Workspace binding

Use a workspace binding when the user wants workflow operations to resolve a chosen root without repeating its path. Resolve bindings in this order:

1. An explicit root supplied for the operation.
2. The launcher environment variable `WORKFLOW_ROOT`.
3. The nearest `.workflow-root.json` found from the current directory upward.
4. User clarification.

Use this binding shape:

```json
{
  "workflow_root": "design/agents/workflows"
}
```

Resolve a relative `workflow_root` value from the directory containing `.workflow-root.json`. Allow an absolute value when the selected root is outside the workspace. The binding is environment configuration, so keep it outside workflow packages and do not copy it into package manifests, state, memory, or runners.

Use `scripts/manage_workflow_root.py bind <workspace> <root>` to write a binding and `locate [start]` to resolve one. Preserve unknown binding fields during updates. Never replace binding discovery with a broad filename search or a guessed conventional directory.

## Root `state.json`

Store workspace selection separately from package progress:

```json
{
  "active": "workflow-a"
}
```

Use `null` when no workflow is selected:

```json
{
  "active": null
}
```

Apply these rules:

- Require an `active` field containing `null` or a safe relative path from the workflow root to a package directory.
- Reject absolute paths, parent traversal, paths outside the root, missing packages, and packages without `workflow_file`.
- Preserve unknown fields during updates so the root state can evolve without destroying newer data.
- Write changes atomically after rereading the current file.
- Keep package lifecycle, progress, decisions, and memory out of root state.
- Keep the root's absolute path out of every workflow package.

Use `scripts/manage_workflow_root.py` for deterministic root operations. Initialize a chosen root with `assets/workflow-root/state.json` only when the user asks to establish that root.

## Workflow resolution

Resolve a package for `workflow:status`, `workflow:next`, `workflow:run`, `workflow:summary`, and `workflow:complete` in this order:

1. Use an explicit workflow id or path supplied for the operation.
2. Otherwise use the relative path in root `state.json`.
3. Otherwise use the sole nonterminal workflow beneath the root for that operation only.
4. Otherwise report candidates and require `workflow:activate` or an explicit target.

Do not persist step 3. Only `workflow:activate` changes root selection. Do not let an explicitly targeted operation silently change selection.

Treat package statuses `draft`, `in_progress`, `paused`, and `blocked` as nonterminal. Treat `completed` and `abandoned` as terminal. Reserve “active” for the root selection pointer.

## Package contents

Use this layout:

```text
<workflow-id>/
├── manifest.json
├── workflow.md
├── state.md
├── memory.md
└── runner.md
```

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`. Keep version 1 deliberately small; add domain artifacts beside or outside the canonical files only when the workflow requires them.

## `manifest.json`

Use this required shape:

```json
{
  "schema_version": 1,
  "id": "build-notation-parser",
  "workflow_file": "workflow.md",
  "state_file": "state.md",
  "memory_file": "memory.md",
  "runner_file": "runner.md"
}
```

Apply these rules:

- Use `schema_version: 1`.
- Use lowercase ASCII letters, digits, and single hyphens for `id`.
- Match `id` to the package directory name.
- Use safe relative paths inside the package for every file field.
- Use `workflow_file` as the package type discriminator.
- Keep lifecycle status in `state.md`.
- Keep workflow logic in `workflow.md`.
- Keep accumulated knowledge in `memory.md`.
- Keep provider, model, machine, scheduler, deployment, and credential configuration out of the manifest.

Treat unknown manifest fields as noncanonical extensions. Preserve them during refinement unless they conflict with this contract, but do not add extensions merely because another package type uses them.

## `workflow.md`

Make `workflow.md` the durable, provider-neutral procedure. For a new workflow, use these headings:

```markdown
# Goal

## Completion criteria

## Constraints

## Steps

## Transitions
```

### Goal

State one finite objective and the value of completing it. Split unrelated objectives into separate workflows.

### Completion criteria

Define observable evidence that proves the whole workflow is finished. Make the terminal condition reachable and distinguish it from merely finishing the current step.

### Constraints

State scope, quality, safety, privacy, resource, time, cost, and authority boundaries that materially affect the work. Describe logical resources rather than machine-specific bindings when portability matters. Treat constraints as limits on intended behavior, not as a permission grant.

### Steps

Use the smallest useful set of numbered steps or phases. For each step, define:

- eligibility or prerequisites
- intended outcome
- observable completion evidence

Add required inputs, approval gates, outputs, or failure behavior when they are not obvious. Keep domain language here rather than expanding the generic runner.

### Transitions

Name the starting step. Define non-obvious ordering, branches, loops, pause points, and decision gates. For a strictly linear workflow, say that execution advances to the next numbered step after verified completion. Ensure every loop can terminate or block and every branch can reach the workflow's terminal condition.

Do not encode a cron schedule or an indefinite cadence. A bounded loop that supports the finite objective is valid.

## `state.md`

Make `state.md` answer “Where is execution now?” Use this structure for new packages:

```markdown
# Workflow state

Status: draft

## Current step

## Completed steps

## Blockers

## Pending decisions

## Working artifacts

## Open operation
```

Use one lifecycle status:

- `draft`: Designed but not started.
- `in_progress`: Ready for or currently undergoing work.
- `paused`: Intentionally stopped without a blocking condition.
- `blocked`: Unable to advance until a stated condition changes.
- `completed`: Every workflow completion criterion is verified.
- `abandoned`: Intentionally terminated without completion.

Record evidence with each completed step when the evidence is not obvious from a linked working artifact. Keep blockers distinct from decisions awaiting user choice. List only artifacts relevant to resuming or verifying work. Use `Open operation` for interrupted work that another agent may need to continue or reconcile.

Update state after every `workflow:run` attempt. Never mark progress from intent, effort, or an unverified claim. Keep historical explanation out of state when it belongs in memory.

## `memory.md`

Make `memory.md` answer “What has this workflow learned that future work needs?” Use this structure for new packages:

```markdown
# Workflow memory

## Decisions

## Discoveries

## Rejected approaches

## Durable context
```

Use the sections as follows:

- **Decisions:** Record consequential choices and concise rationale.
- **Discoveries:** Record verified facts that affect later steps.
- **Rejected approaches:** Record alternatives worth not repeating and why they were rejected.
- **Durable context:** Record stable background, conventions, or relationships that future steps require.

Do not use memory as an event log, transcript, scratchpad, or duplicate state file. Preserve provenance or uncertainty when it affects trust. Compact repeated or obsolete entries while retaining current conclusions and reasons another agent needs.

## `runner.md`

Make `runner.md` the provider-neutral control protocol. It must:

- resolve canonical files from the package root supplied by the launcher or current directory
- read the manifest, workflow, state, and relevant memory before any operation
- inspect working artifacts when needed to verify progress
- implement `workflow:status`, `workflow:next`, and `workflow:summary` as read-only operations
- implement `workflow:run` as the only control operation that performs domain work
- implement `workflow:complete` as a verified lifecycle transition that performs no missing domain work
- default an unscoped run to one coherent unit through the next safe checkpoint
- confirm step eligibility and user and host authority before acting
- verify completion evidence before advancing a step
- apply branches, loops, pauses, and terminal rules from `workflow.md`
- distinguish advanced, no-op, blocked, partial, failed, and completed attempts
- reread and merge state and memory immediately before writing
- keep state positional and memory semantic
- leave the manifest, procedure, and runner unchanged during runtime execution
- emit complete `State handoff` and `Memory handoff` replacements when continuity files cannot be written
- clear root `state.json` after verified completion only when it still selects this package

Keep the runner identical across packages whenever this contract is unchanged. Package design or refinement may modify the runner; ordinary runtime execution may not.

## Control operations

### `workflow:list`

Read root `state.json`, discover manifests containing `workflow_file` beneath the chosen root, and report each workflow's id, relative path, lifecycle status, and selection. Ignore coach and task manifests. Report invalid workflow packages without selecting or modifying them.

### `workflow:activate`

Resolve an explicit workflow id or path. Reject ambiguous, invalid, `completed`, or `abandoned` packages. Reread root `state.json`, preserve unknown fields, and atomically write the normalized relative package path to `active`. Do not change package `state.md` or perform workflow work.

### `workflow:status`

Read canonical files and report:

- lifecycle status and current step
- verified completed steps
- blockers and pending decisions
- working artifacts and open operation
- remaining steps and terminal criteria

Do not modify files, resolve decisions, or perform workflow work.

### `workflow:next`

Return one next valid action with:

- the step it belongs to
- prerequisites and unresolved blockers
- expected outcome
- evidence that would make it complete
- the transition that would follow

Do not perform the action. If no action is valid, explain the exact blocking condition. If the workflow is complete or abandoned, report that it has no next action.

### `workflow:summary`

Derive a compact handoff from canonical sources. Include the goal, current position, verified progress, important decisions and discoveries, blockers, pending decisions, and next valid action. Do not save this derived summary or let it replace canonical state or memory.

### `workflow:run`

Honor the requested scope. Accept scopes such as one action, the next checkpoint, one phase, or completion. When unspecified, stop at the next safe checkpoint after one coherent unit of work.

After an attempt:

1. Verify observed outcomes.
2. Apply the workflow's transition rules.
3. Update state even for no-op, blocked, partial, or failed work.
4. Update memory only for durable new knowledge.
5. Verify the final writes or provide full continuity handoffs.
6. Report workflow outcomes separately from state and memory persistence.

When a run verifies the whole workflow complete, write package state first. Clear root `active` only after that write succeeds and only when the reread pointer still references the completed package.

Do not infer authorization for destructive, irreversible, costly, or externally visible actions from the existence of the package. Follow the user's request, workflow constraints, and host safety rules together.

### `workflow:complete`

Verify every terminal criterion against current evidence without doing missing domain work. If any criterion is unmet or uncertain, leave package and root state unchanged and report the gap. Otherwise mark package `state.md` as `completed`, verify the write, then atomically clear root `active` only when it still selects that package.

### `workflow:deactivate`

Use only when the user explicitly requests the escape hatch. Atomically set root `active` to `null` while preserving unknown fields. Do not alter package lifecycle state.

## Source conflicts

When canonical files disagree:

1. Prefer observable artifact evidence for claims about completed work.
2. Treat `workflow.md` as authoritative for procedure and completion rules.
3. Treat `state.md` as authoritative for the last recorded execution position, subject to verification against newer artifacts.
4. Treat `memory.md` as authoritative for recorded decisions and discoveries, subject to explicit newer evidence.
5. Treat root `state.json` as authoritative only for workspace selection, never package lifecycle.
6. Preserve conflicting evidence and request judgment when resolving it would materially change behavior or history.

Never silently rewrite history to make the files agree.
