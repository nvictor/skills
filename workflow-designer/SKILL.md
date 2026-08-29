---
name: workflow-designer
description: Design, review, refine, package, discover, inspect, checkpoint, resume, complete, and run portable finite AI workflows whose canonical procedure, execution state, and durable memory survive changes of agent or context. Use when creating or managing a resumable workflow package, choosing or binding a user-owned workflow root, invoking `workflow:list`, `workflow:status`, `workflow:next`, `workflow:checkpoint`, `workflow:run`, `workflow:summary`, or `workflow:complete`, or handling a manifest containing `workflow_file`. Do not use for indefinitely scheduled operations or capability-building coaches.
---

# Workflow Designer

## Purpose

Design provider-neutral workflow packages for finite objectives that require dependent steps, durable continuity, or handoff between agents. Keep the procedure, current position, and learned context in canonical files rather than conversation history. Do not perform workflow work unless the user explicitly requests `workflow:run` or otherwise clearly asks to execute or resume it.

Use a user-chosen workflow root only as a deterministic discovery boundary. Do not maintain an active-workflow pointer. Target a package explicitly whenever more than one nonterminal workflow exists.

## Package ownership

Own a package when its manifest contains `workflow_file`. Use the manifest as the type discriminator:

- `workflow_file` identifies a finite workflow package; continue with this skill.
- `task_file` identifies a bounded, rerunnable task package; use the task designer.
- `prompt_file` identifies a coach package; use the coach designer.

Report conflicting discriminators instead of choosing silently.

Distinguish package types by why continuity exists:

- Use a workflow when one finite objective requires dependent steps and a terminal condition.
- Use a task when one bounded operation should be safely rerunnable manually, on a schedule, or both.
- Use a coach when repetition exists to develop a learner's capability.

Allow loops inside a workflow when they lead toward its terminal condition. Do not treat an internal revise-until-approved loop as a task package.

## Workflow root

Treat the workflow root as an environment binding chosen by the user. It may live inside a project, under a shared agents directory, or in a standalone directory. Do not store its absolute path in workflow packages.

Allow direct children and user-organized subdirectories:

```text
<workflow-root>/
├── workflow-a/
└── group/
    └── workflow-b/
```

Resolve the workflow root in this order:

1. Use a root explicitly supplied by the user.
2. Otherwise use the path in the launcher environment variable `WORKFLOW_ROOT`.
3. Otherwise find the nearest `.workflow-root.json` from the current directory upward and resolve its `workflow_root` value relative to the binding file.
4. Otherwise ask the user to choose a root.

Use `scripts/manage_workflow_root.py locate [start]` for deterministic binding discovery and `bind <workspace> <root>` to create or update a user-authorized workspace binding. Do not search arbitrary directories or assume `.workflows`, `design/agents`, or any other location.

Use this workspace-binding shape:

```json
{
  "workflow_root": "relative/or/absolute/path"
}
```

Prefer a relative value when the root is inside the workspace. Keep this environment binding outside workflow packages. A legacy root-level `state.json` has no canonical meaning under this contract; ignore it and do not delete it without explicit authorization.

## Invocation

Treat `workflow:<operation>` as a provider-neutral operation label, not proof that a host registered a slash command with that spelling. Natural-language requests and host-specific commands must map to the same operation contract.

When installed, prefer the embedded façade skills under `adapters/skills/` for autocomplete:

| Operation | Codex | Claude Code |
| --- | --- | --- |
| `workflow:list` | `$workflow-list` | `/workflow-list` |
| `workflow:status` | `$workflow-status` | `/workflow-status` |
| `workflow:next` | `$workflow-next` | `/workflow-next` |
| `workflow:checkpoint` | `$workflow-checkpoint` | `/workflow-checkpoint` |
| `workflow:run` | `$workflow-run` | `/workflow-run` |
| `workflow:summary` | `$workflow-summary` | `/workflow-summary` |
| `workflow:complete` | `$workflow-complete` | `/workflow-complete` |

Each façade selects exactly one operation and delegates all behavior to this skill. Treat façade invocation as operation selection, not additional authority. Keep façade skills explicit-only in hosts that support that distinction.

For a standalone Claude Code skill, invoke `/workflow-designer <operation> [target]`.

### Install façade skills

Treat façade installation as a host binding, not part of the canonical workflow contract. After installing `workflow-designer` on another computer, install the embedded façades as direct children of the host's personal skills directory so autocomplete can discover them.

For Claude Code, run:

```text
python3 ~/.claude/skills/workflow-designer/scripts/manage_adapter_skills.py install --host claude
```

Then start a new Claude Code session and type `/workflow-` to verify the seven façade names appear. Verify the filesystem binding at any time with:

```text
python3 ~/.claude/skills/workflow-designer/scripts/manage_adapter_skills.py verify --host claude
```

The installer is idempotent and refuses to replace a file, directory, or symlink that does not already point to the matching embedded façade. Use `--skills-dir <path>` only for a nonstandard personal skills directory.

When migrating from the former Claude command adapters, inspect `~/.claude/commands/workflow` first. Remove it only when it is a symlink to this package's removed `adapters/claude/commands/workflow` directory. Do not remove an unrelated command directory. The former `/workflow:<operation>` aliases are obsolete after the `/workflow-<operation>` façade skills are installed.

The same manager supports Codex with `--host codex`. Do not tell a user that a façade command exists until its host binding verifies successfully.

## Select the operation

- **Create:** Design and write a new workflow package without executing it.
- **Convert:** Turn an existing plan, checklist, procedure, or project brief into a package while preserving its intent and source artifacts.
- **Review:** Inspect a package and report evidence-backed findings without editing or running it.
- **Refine:** Improve a package while preserving unrelated procedure, state, memory, and artifacts.
- **`workflow:list`:** Read only. List workflow packages beneath the chosen root and their lifecycle statuses.
- **`workflow:status`:** Read only. Report the current position, verified progress, blockers, pending decisions, and remaining work.
- **`workflow:next`:** Read only. Identify the next valid action, its prerequisites, and why it follows. Do not execute it.
- **`workflow:summary`:** Read only. Derive a compact human or agent handoff from canonical files. Do not store it as another source of truth.
- **`workflow:checkpoint`:** Reconcile externally or manually completed work into state and memory without performing domain work.
- **`workflow:run`:** Execute or resume the permitted amount of domain work, then persist truthful state and durable memory.
- **`workflow:complete`:** Verify the terminal criteria and mark the package completed without performing missing domain work.

Treat package design, bookkeeping, workflow execution, and external effects as separate authorities. Authorization for one never implies another.

For create, convert, refine, or review, read `references/quality-rubric.md` completely. For every root or package operation, read `references/package-format.md` completely. Copy `assets/workflow-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_workflow_package.py` before delivery. Use `scripts/manage_workflow_root.py` to bind, locate, list, resolve, or validate a workflow root.

## Examples

Create without running:

```text
Use workflow-designer to create a resumable workflow for publishing my conference talk in design/agents/workflows/publish-conference-talk. Do not run it.
```

Bind a workspace so future operations can discover its workflow root:

```text
Bind this workspace to design/agents/workflows as its workflow root.
```

List workflows:

```text
workflow:list in design/agents/workflows
```

Inspect an explicit workflow:

```text
workflow:status for design/agents/workflows/build-notation-parser
workflow:next for design/agents/workflows/build-notation-parser
```

Record progress performed outside the agent:

```text
workflow:checkpoint design/agents/workflows/iss-sprites: I curated the down direction. Verify the artifact and update bookkeeping only.
```

Resume execution:

```text
workflow:run design/agents/workflows/build-notation-parser through the next safe checkpoint.
```

Produce a handoff:

```text
workflow:summary for design/agents/workflows/build-notation-parser
```

Use this provider-neutral launcher form:

```text
Perform `workflow:<operation>` on the portable workflow package at `<package-root>`. Read and follow `runner.md`. Treat `state.md` and `memory.md` as canonical cross-agent continuity.
```

When a root contains exactly one nonterminal workflow, the target may be omitted:

```text
Perform `workflow:<operation>` using the user-selected workflow root at `<workflow-root>`. Resolve its sole nonterminal workflow, then follow that package's `runner.md`.
```

## Resolve a workflow

Resolve the target for `workflow:status`, `workflow:next`, `workflow:checkpoint`, `workflow:run`, `workflow:summary`, or `workflow:complete` in this order:

1. Use an explicit workflow id or package path from the user.
2. Otherwise use the sole nonterminal workflow beneath the chosen root for this operation only.
3. Otherwise report the nonterminal candidates and require an explicit target.

Never persist an implicit selection. An explicit target may identify a terminal workflow for inspection. Treat `draft`, `in_progress`, `paused`, and `blocked` as nonterminal; treat `completed` and `abandoned` as terminal.

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

### 4. Separate state, memory, artifacts, and history

Treat `state.md` as a compact current snapshot, never an activity log. Put only:

- lifecycle status and current step
- current-step progress when it cannot be derived cheaply from artifacts
- completed top-level steps with concise evidence
- blockers and pending decisions that affect the current or next transition
- working artifacts needed to resume or verify work
- interrupted work that must be reconciled

Use a compact table for repeated current-step units such as directions, files, or environments. When a step completes, replace detailed substep history with one completed-step entry and its evidence.

Treat `memory.md` as current durable knowledge, never an append-only journal. Put only:

- consequential decisions and their rationale
- verified discoveries future steps need
- rejected approaches worth not repeating
- stable context that would otherwise be lost

When new evidence supersedes an entry, replace the old statement. Retain the former approach under `Rejected approaches` only when its rationale remains useful. Do not duplicate facts that are cheaply observable from authoritative artifacts. Keep execution history in project history or a task log, not in state or memory.

### 5. Write and validate the package

Write `manifest.json`, `workflow.md`, `state.md`, `memory.md`, and `runner.md` according to `references/package-format.md`. Keep the manifest deliberately small. Put lifecycle status in state, not the manifest. Keep provider names, model settings, machine paths, credentials, scheduler syntax, and chat history out of canonical files unless a workflow's explicit domain constraint genuinely requires a named environment.

Keep `runner.md` generic and identical across packages whenever the runtime contract is unchanged. Validate every created or refined package. Fix errors before delivery and report warnings that require judgment.

## Control-plane behavior

### Read-only operations

For `workflow:list`, discover manifests containing `workflow_file` beneath the chosen root and report their relative paths, ids, and lifecycle statuses. Ignore coach and task packages.

For `workflow:status`, `workflow:next`, and `workflow:summary`:

1. Resolve an explicit or sole nonterminal workflow.
2. Read the manifest and resolve the canonical files.
3. Read the procedure, state, and only the memory needed to interpret them.
4. Inspect relevant working artifacts when the operation requires verification.
5. Return the requested view without changing files or performing domain work.

Treat `workflow:next` as advisory even when the next action appears harmless. Use `workflow:run` for execution.

### Checkpoint

For `workflow:checkpoint`, require explicit intent to record or reconcile work performed outside the current agent run. Do not perform missing domain work.

1. Resolve the workflow and read all canonical context needed for reconciliation.
2. Inspect user-supplied evidence and relevant artifacts.
3. Prefer observable artifact evidence over prose claims; preserve uncertainty when verification is unavailable.
4. Update state as a current snapshot, replacing stale or superseded statements rather than appending an event.
5. Update memory only when the checkpoint establishes a durable decision, discovery, rejected approach, or stable context.
6. Reread state and memory immediately before writing and merge newer evidence.
7. Preserve lifecycle status as exactly one of `draft`, `in_progress`, `paused`, `blocked`, `completed`, or `abandoned`; never humanize the token.
8. Verify the writes with `scripts/validate_workflow_package.py` when filesystem execution is available, or at minimum reread and verify the exact status token. Otherwise return complete state and memory handoffs.

Classify the checkpoint as `reconciled`, `no-op`, `blocked`, or `conflicted`. Checkpoint authority permits continuity writes only; it never permits domain effects.

### Run

For `workflow:run`, follow `runner.md` from the package root. Honor an explicit scope such as one action, the next checkpoint, one phase, or completion. When scope is unspecified, perform one coherent unit of work through the next safe checkpoint; do not assume authorization to finish the whole workflow.

Before acting, confirm the current step is eligible, required inputs exist, blockers are resolved, and the requested action is within user and host authority. Treat workflow constraints as intended limits, never as a grant of permissions. Stop before unauthorized, destructive, externally visible, or unsafe effects.

After every attempt, reconcile continuity as a snapshot: verify current artifacts, replace stale positional statements, compact finished substep detail, and update memory only for durable new knowledge. Reread both files immediately before writing and merge newer evidence. Preserve lifecycle status as exactly one of `draft`, `in_progress`, `paused`, `blocked`, `completed`, or `abandoned`; never humanize the token. After writing, run `scripts/validate_workflow_package.py` when filesystem execution is available, or at minimum reread and verify the exact status token. When writing is unavailable, return complete replacement contents as handoffs and never imply persistence succeeded.

Mark a step complete only from observable evidence. Mark the workflow complete only when its terminal criteria are satisfied. Do not equate effort, elapsed time, a plausible artifact, or an agent assertion with verified completion.

### Complete

For `workflow:complete`, resolve the target and verify every terminal criterion from current evidence without performing missing domain work. If any criterion is unmet or uncertain, report it and leave package state unchanged. Otherwise reread `state.md`, mark the lifecycle `completed`, persist the final positional snapshot, validate the package when filesystem execution is available or at minimum reread and verify the exact status token, and report completion.

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
- **Bind root:** Write and verify the workspace binding without changing any package.
- **Refine:** Write and validate the package. Report behavior changes separately from state or memory changes.
- **Review:** Return prioritized, evidence-backed findings without editing or running.
- **`workflow:list`:** Report discovered workflow ids, relative paths, and lifecycle statuses without editing.
- **`workflow:status`:** Report lifecycle status, current step, verified completed work, blockers, pending decisions, working artifacts, and remaining steps.
- **`workflow:next`:** Report one next valid action, prerequisites, completion evidence, and blockers. Do not act.
- **`workflow:summary`:** Return a compact derived handoff covering goal, position, progress, durable decisions, blockers, and next action.
- **`workflow:checkpoint`:** Report evidence reconciled, conflicts or uncertainty preserved, state changes, memory changes, and whether continuity was written or handed off.
- **`workflow:run`:** Report attempted work, verified outcome, current position, new durable memory, unresolved work, and whether canonical files were written or handed off.
- **`workflow:complete`:** Report verified terminal evidence and package-state persistence.

Never claim execution, completion, state persistence, or preserved behavior without verifying it.
