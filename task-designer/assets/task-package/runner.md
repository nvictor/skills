# Portable task runner

Use the package root supplied by the launcher or the directory containing this file. Use only the deployment adapter explicitly selected by the launcher; do not guess one.

## Before execution

1. Read `manifest.json`.
2. Read the task instructions named by `task_file`.
3. Read the canonical task state named by `state_file`.
4. Resolve declared logical resources from the selected deployment adapter or launcher.
5. Confirm required resources, host permissions, approval gates, allowed effects, and idempotency requirements.

Treat the task instructions as authoritative for behavior and `state.md` as authoritative for cross-agent continuity. Treat declared effects as the maximum intended authority and host permissions as the maximum available authority. Execute only their intersection.

The continuity contract authorizes only the required update to the canonical `state_file` when the host permits it. Treat that write as internal bookkeeping rather than a task-domain effect. It does not authorize changes to any other package file or resource.

If a required resource is unavailable or an intended effect is undeclared, ambiguous, unauthorized, or unsafe to retry, stop before that effect and record a blocked outcome.

## Execute one run

1. Continue an open interaction when the task requires it; otherwise start one bounded run.
2. Check state and current inputs for duplicate, already-completed, or no-op conditions before acting.
3. Follow the ordered procedure in `task.md`.
4. Before each effect, reconfirm its declared kind, bound resource, purpose, host authority, approval, and retry safety.
5. Verify the definition of done from observable evidence.
6. Classify the outcome as `success`, `no-op`, `blocked`, `partial`, or `failed`.
7. Report verified effects, outputs, unresolved work, and the state persistence result. Never claim an unverified effect or delivery.

Do not modify `manifest.json`, `task.md`, `runner.md`, `migration.json`, or deployment adapters. A missing `schedule` means the package is manual-only. A present `schedule` does not prevent manual execution. Do not compute, create, alter, postpone, or advance future schedules.

## Preserve continuity

After every attempted run, including blocked, no-op, partial, and failed runs:

1. Reread the state file immediately before writing.
2. Merge current evidence with any newer recorded evidence.
3. Update the last attempt and, only after verified success, the last successful run.
4. Update checkpoints, pending work, known failures, and open interaction from observable evidence.
5. Add one concise recent outcome and retain at most ten, moving durable facts into the appropriate section.
6. Record uncertain or partial external effects precisely enough to prevent duplicate work.

Write the merged state when the state file is writable. If it is read-only or unavailable, continue only when doing so is safe and end the response with a `State handoff` section containing the complete proposed replacement contents of `state.md`. Never imply that state was saved when it was not.
