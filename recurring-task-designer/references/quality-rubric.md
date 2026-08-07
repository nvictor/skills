# Recurring-task quality rubric

Read this file completely when creating, reviewing, or refining a recurring task. During preservation migration, use it to produce warnings only; do not rewrite behavior.

## Recurring value

- State the observable outcome of each run.
- Explain through behavior why repetition is useful.
- Make the cadence fit the rate at which inputs or decisions change.
- Define a useful no-op outcome when nothing needs attention.
- Avoid repeated work whose output cannot influence a person, artifact, or system.

## Inputs and prerequisites

- Name every required logical resource and capability.
- Define freshness, completeness, and validation requirements.
- Stop safely when a required input is missing, stale, or ambiguous.
- Keep paths, connectors, credentials references, and other bindings outside canonical task instructions.

## Bounded execution

- Give one run a clear beginning, ordered procedure, and end.
- Keep work within the requested time and cost bounds.
- Define unattended, interactive, or mixed behavior accurately.
- Do not depend on user input during an unattended run.
- Separate optional enrichment from required completion.

## Definition of done and outputs

- Make success verifiable from observable evidence.
- Define expected artifacts, messages, mutations, or reports.
- Verify effects before claiming success.
- Distinguish success, no-op, blocked, partial, and failure outcomes.
- Produce a concise result that states what changed and what remains.

## Idempotency and recurrence safety

- Define how duplicate or delayed invocations are detected.
- Make repeated execution safe against unchanged inputs.
- Check state before every effect that could duplicate work.
- Never blindly retry an external effect with an uncertain result.
- Record partial effects so another agent can resume without repeating them.

## Failure and recovery

- Define which failures are retryable and which require intervention.
- Preserve enough evidence to diagnose failures without retaining unnecessary sensitive data.
- Stop before destructive fallback behavior.
- Escalate missing authorization, ambiguous targets, and source conflicts.
- Keep pending work distinct from completed work.

## Effects and authority

- Use deny-by-default effects.
- Declare every filesystem write, external write, message send, and command execution.
- Scope effects to named resources and a clear purpose.
- Treat host permissions as availability, not authorization to expand scope.
- Require explicit approval for destructive, irreversible, costly, or externally visible actions when appropriate.
- Treat the continuity-authorized `state_file` update as internal bookkeeping, not as permission for any task-domain write.

## State and continuity

- Treat package state as canonical across agents.
- Record only observable attempts, outcomes, checkpoints, pending work, failures, and open interactions.
- Never invent run history, delivery, or successful effects.
- Reread state before writing and merge newer evidence.
- Retain at most ten recent outcomes and compact older durable information.
- Produce a complete state handoff when durable writing is unavailable.

## Portability

- Keep canonical behavior independent of provider, model, scheduler, and machine.
- Use logical resource names in task instructions.
- Keep schedules in the manifest and environment bindings in adapters.
- Keep credential values out of every package file.
- Make the package understandable and runnable by another capable agent with equivalent resources.

## Migration integrity

- Preserve source instructions and state before improving them.
- Recover live configuration from authoritative sources.
- Record provenance, checksums, conflicts, and missing metadata.
- Keep package creation separate from live execution and deployment.
- Never claim lossless migration when selected sources or deployment settings are unresolved.

## Final review

Confirm that:

- the task provides recurring value across many runs
- one run is bounded and executable
- inputs, effects, outputs, and success are explicit
- no-op and duplicate invocations are safe
- failure and partial-success behavior is recoverable
- state remains truthful, compact, and portable
- another capable agent can run the package
- creation, execution, and deployment authorities remain separate
