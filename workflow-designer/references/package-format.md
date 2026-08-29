# Portable workflow package format

Read this file completely for every operation involving a workflow package.

## Contents

- Workflow root
- Workspace binding
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

Let the user choose the workflow root. Treat it as a discovery boundary and environment binding, not part of any portable package. Do not prescribe `.workflows`, `design/agents`, a home-directory location, or another fixed convention.

Allow workflow packages as direct children or in user-organized subdirectories:

```text
<workflow-root>/
├── workflow-a/
│   └── ...
└── group/
    └── workflow-b/
        └── ...
```

The root has no canonical mutable state and no active-workflow pointer. A legacy root-level `state.json` may remain during migration, but operations must ignore it and must not delete it without explicit authorization.

Resolve the root from an explicit user-supplied path or an existing launcher/workspace binding. Ask the user when neither is available. Do not search arbitrary filesystem locations or infer the root from chat history.

## Workspace binding

Use a workspace binding when the user wants operations to discover a chosen root without repeating its path. Resolve bindings in this order:

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

## Workflow resolution

Resolve a package for `workflow:status`, `workflow:next`, `workflow:checkpoint`, `workflow:run`, `workflow:summary`, and `workflow:complete` in this order:

1. Use an explicit workflow id or package path supplied for the operation.
2. Otherwise use the sole nonterminal workflow beneath the chosen root for that operation only.
3. Otherwise report the nonterminal candidates and require an explicit target.

Never persist an implicit selection. An explicit target may identify a terminal package for inspection. Treat package statuses `draft`, `in_progress`, `paused`, and `blocked` as nonterminal. Treat `completed` and `abandoned` as terminal.

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

Use UTF-8 text and Unix line endings. Use a lowercase hyphenated directory name that exactly matches the manifest `id`. Keep version 1 deliberately small. Add domain artifacts beside or outside the canonical files only when the workflow requires them.

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

Treat state as a compact current snapshot, never as a diary:

- Record only the current step, verified top-level completion, current blockers, decisions affecting the current or next transition, relevant artifacts, and interrupted work.
- Use a compact table when the current step has repeated units whose progress is not cheap to derive from artifacts.
- When a top-level step completes, replace detailed substep history with one completed-step entry and concise evidence.
- Record evidence with a completed step when it is not obvious from a linked authoritative artifact.
- Keep implementation rationale, cleanup history, transcripts, and accumulated discoveries out of state.
- Do not persist a derived summary or next-action explanation when `workflow:next` can derive it.

Update state after every `workflow:run` attempt and every `workflow:checkpoint`. Replace stale or superseded statements rather than appending another event. Never mark progress from intent, effort, or an unverified claim.

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

- **Decisions:** Record current consequential choices and concise rationale.
- **Discoveries:** Record verified facts that affect later steps.
- **Rejected approaches:** Record alternatives worth not repeating and why they were rejected.
- **Durable context:** Record stable background, conventions, or relationships future steps require.

Treat memory as a compact current knowledge base, never an append-only journal:

- Replace a superseded statement with the current truth.
- Preserve the former approach only under `Rejected approaches` and only when its rationale remains useful.
- Do not copy inventories, file lists, or status that are cheaply observable from authoritative artifacts.
- Do not duplicate state, logs, transcripts, scratch notes, or conversational exhaust.
- Preserve provenance or uncertainty when it affects trust.

Keep execution history in project history or a task log rather than canonical workflow continuity.

## `runner.md`

Make `runner.md` the provider-neutral control protocol. It must:

- resolve canonical files from the package root supplied by the launcher or current directory
- read the manifest, workflow, state, and relevant memory before any operation
- inspect working artifacts when needed to verify progress
- implement `workflow:status`, `workflow:next`, and `workflow:summary` as read-only operations
- implement `workflow:checkpoint` as continuity reconciliation without domain work
- implement `workflow:run` as the only control operation that performs domain work
- implement `workflow:complete` as a verified lifecycle transition that performs no missing domain work
- default an unscoped run to one coherent unit through the next safe checkpoint
- confirm step eligibility and user and host authority before acting
- verify completion evidence before advancing a step
- apply branches, loops, pauses, and terminal rules from `workflow.md`
- distinguish run outcomes and checkpoint outcomes accurately
- store lifecycle status only as the exact tokens `draft`, `in_progress`, `paused`, `blocked`, `completed`, or `abandoned`, without humanizing them
- reread and merge state and memory immediately before writing
- reread written continuity and verify the exact lifecycle status token before reporting persistence
- replace stale continuity statements and compact superseded detail
- keep state positional and memory semantic
- leave the manifest, procedure, and runner unchanged during runtime operations
- emit complete `State handoff` and `Memory handoff` replacements when continuity files cannot be written

Keep the runner identical across packages whenever this contract is unchanged. Package design or refinement may modify the runner; ordinary runtime operations may not.

## Control operations

### `workflow:list`

Discover manifests containing `workflow_file` beneath the chosen root and report each workflow's id, relative path, and lifecycle status. Ignore coach and task manifests. Report invalid workflow packages without modifying them.

### `workflow:status`

Read canonical files and report:

- lifecycle status and current step
- verified completed steps
- blockers and pending decisions
- working artifacts and open operation
- remaining steps and terminal criteria

Do not modify files, resolve decisions, or perform workflow work.

### `workflow:next`

Return one next valid action with its step, prerequisites, unresolved blockers, expected outcome, completion evidence, and following transition. Do not perform the action. If no action is valid, explain the exact blocking condition. If the workflow is terminal, report that it has no next action.

### `workflow:summary`

Derive a compact handoff from canonical sources. Include the goal, current position, verified progress, important decisions and discoveries, blockers, pending decisions, and next valid action. Do not save this derived summary or let it replace canonical state or memory.

### `workflow:checkpoint`

Use this operation only when the user explicitly asks to record or reconcile work performed outside the current agent run. Perform no missing domain work.

1. Inspect the supplied evidence and relevant artifacts.
2. Prefer observable artifact evidence; preserve unverified claims as uncertain.
3. Reconcile the current snapshot by replacing stale or superseded state.
4. Add or revise memory only for durable knowledge.
5. Reread continuity files before writing and merge newer evidence.
6. Verify the writes, including the exact lifecycle status token, or provide complete continuity handoffs.

Classify the result as `reconciled`, `no-op`, `blocked`, or `conflicted`. A checkpoint authorizes writes only to the files named by `state_file` and `memory_file`.

### `workflow:run`

Honor the requested scope. Accept scopes such as one action, the next checkpoint, one phase, or completion. When unspecified, stop at the next safe checkpoint after one coherent unit of work.

After an attempt:

1. Verify observed outcomes.
2. Apply the workflow's transition rules.
3. Reconcile state as a current snapshot even for no-op, blocked, partial, or failed work.
4. Update memory only for durable new knowledge, replacing superseded statements.
5. Reread and merge continuity files before writing.
6. Verify the final writes, including the exact lifecycle status token, or provide full continuity handoffs.
7. Report workflow outcomes separately from continuity persistence.

Do not infer authorization for destructive, irreversible, costly, or externally visible actions from the package. Follow the user's request, workflow constraints, and host safety rules together.

### `workflow:complete`

Verify every terminal criterion against current evidence without doing missing domain work. If any criterion is unmet or uncertain, leave package state unchanged and report the gap. Otherwise mark `state.md` as `completed`, persist a compact final snapshot, verify the write, and report completion.

## Source conflicts

When canonical files disagree:

1. Prefer observable artifact evidence for claims about completed work.
2. Treat `workflow.md` as authoritative for procedure and completion rules.
3. Treat `state.md` as authoritative for the last recorded execution position, subject to verification against newer artifacts.
4. Treat `memory.md` as authoritative for recorded decisions and discoveries, subject to explicit newer evidence.
5. Preserve conflicting evidence and request judgment when resolving it would materially change behavior or history.

Never silently rewrite uncertain history merely to make the files agree. When evidence establishes that one statement supersedes another, keep only the current truth in state or memory.
