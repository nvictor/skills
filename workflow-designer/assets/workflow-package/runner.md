# Portable workflow runner

Use the package root supplied by the launcher or the directory containing this file. The launcher may also supply a user-selected workflow root whose `state.json` contains workspace selection. Do not infer or hardcode that root.

## Load canonical context

1. Read `manifest.json`.
2. Read the durable procedure named by `workflow_file`.
3. Read the execution position named by `state_file`.
4. Read the durable knowledge named by `memory_file`, selecting only what the operation needs.
5. Inspect working artifacts when required to verify state or completion.

Treat the workflow file as authoritative for procedure, the state file as authoritative for execution position, and the memory file as authoritative for accumulated semantic context. Do not replace newer package evidence with chat history or private platform memory.

## Select the operation

- `workflow:status`: Report where execution is, what is verified complete, what is blocked or undecided, and what remains. Do not modify files or perform workflow work.
- `workflow:next`: Identify one next valid action, its prerequisites, completion evidence, and blockers. Do not execute it or modify files.
- `workflow:summary`: Derive a compact handoff from canonical files. Do not save the summary as another source of truth or modify files.
- `workflow:run`: Perform the explicitly requested scope. When scope is unspecified, perform one coherent unit through the next safe checkpoint.
- `workflow:complete`: Verify every terminal criterion without performing missing domain work. Complete only when current evidence satisfies all criteria.

Reject an unknown operation or ask for a choice when the launcher does not make the intended operation clear.

## Run workflow work

For `workflow:run` only:

1. Confirm the workflow is not already completed or abandoned.
2. Confirm the current step is eligible and reconcile it with verified artifacts.
3. Resolve blockers or pending decisions only when the available evidence and authority permit it.
4. Perform the requested scope while following workflow constraints, approval gates, and host safety rules.
5. Verify step outcomes against observable completion evidence before advancing.
6. Apply transition rules, stopping at the requested boundary or next safe checkpoint.
7. Classify the attempt as `advanced`, `no-op`, `blocked`, `partial`, `failed`, or `completed`.

Treat package instructions as intended limits, not as authority to exceed the user's request or host permissions. Stop before an unauthorized, destructive, irreversible, costly, or externally visible effect. Do not modify `manifest.json`, the file named by `workflow_file`, or `runner.md` during runtime execution.

## Preserve continuity

After every `workflow:run` attempt, including blocked, partial, failed, and no-op attempts, and after a successful `workflow:complete`:

1. Reread the files named by `state_file` and `memory_file` immediately before writing.
2. Merge current evidence with any newer recorded evidence; do not overwrite concurrent progress.
3. Update state with the lifecycle status, current step, verified completed steps, blockers, pending decisions, working artifacts, and open operation.
4. Update memory only with durable decisions, discoveries, rejected approaches, and stable context future steps need.
5. Keep state positional and memory semantic. Remove conversational exhaust and compact obsolete detail without losing durable conclusions.
6. Mark the workflow `completed` only when every terminal completion criterion is verified.

The runtime write to state and memory preserves continuity only; it does not authorize other package or domain changes.

After the package state has been written and verified as `completed`, reread root `state.json` when the launcher supplied a workflow root. Atomically set `active` to `null` only when it still contains this package's relative path. Preserve unknown root-state fields. Do not clear a concurrently changed selection. If root state cannot be written, leave it unchanged and report the stale pointer; do not undo verified package completion.

If either continuity file is read-only or unavailable, continue only when doing so is safe. End the response with a `State handoff` and a `Memory handoff`, each containing the complete proposed replacement contents for its canonical file. Never imply that continuity was saved when it was not.
