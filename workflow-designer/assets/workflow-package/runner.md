# Portable workflow runner

Use the package root supplied by the launcher or the directory containing this file. Do not infer or hardcode a workflow root.

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
- `workflow:checkpoint`: Reconcile externally or manually completed work into continuity without performing domain work.
- `workflow:run`: Perform the explicitly requested scope. When scope is unspecified, perform one coherent unit through the next safe checkpoint.
- `workflow:complete`: Verify every terminal criterion without performing missing domain work. Complete only when current evidence satisfies all criteria.

Reject an unknown operation or ask for a choice when the launcher does not make the intended operation clear.

## Reconcile a checkpoint

For `workflow:checkpoint` only:

1. Require explicit intent to record or reconcile work performed outside this run.
2. Inspect user-supplied evidence and relevant working artifacts without doing missing domain work.
3. Prefer observable artifact evidence; preserve unverified claims as uncertain.
4. Reconcile state as a current snapshot and memory as current durable knowledge.
5. Classify the result as `reconciled`, `no-op`, `blocked`, or `conflicted`.

Checkpoint authority permits writes only to the files named by `state_file` and `memory_file`. It never permits domain effects.

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

After every `workflow:checkpoint`, every `workflow:run` attempt including blocked, partial, failed, and no-op attempts, and after a successful `workflow:complete`:

1. Reread the files named by `state_file` and `memory_file` immediately before writing.
2. Merge current evidence with any newer recorded evidence; do not overwrite concurrent progress.
3. Update state as a compact current snapshot: lifecycle status, current step, verified top-level completion, current blockers and decisions, working artifacts, and open operation.
4. Replace stale or superseded positional statements instead of appending an event. Compact completed substep detail into one evidence-backed top-level entry.
5. Update memory only with current durable decisions, discoveries, rejected approaches, and stable context future steps need. Replace superseded statements rather than retaining contradictory versions.
6. Keep state positional and memory semantic. Keep execution history in project history or a task log, not in continuity files.
7. Mark the workflow `completed` only when every terminal completion criterion is verified.

The runtime write to state and memory preserves continuity only; it does not authorize other package or domain changes.

If either continuity file is read-only or unavailable, continue only when doing so is safe. End the response with a `State handoff` and a `Memory handoff`, each containing the complete proposed replacement contents for its canonical file. Never imply that continuity was saved when it was not.
