# Portable opportunity package format

## Identity and files

Use four UTF-8 files: manifest.json, opportunity.md, state.md, and runner.md.

```json
{
  "schema_version": 1,
  "id": "example",
  "name": "Opportunity: Example",
  "opportunity_file": "opportunity.md",
  "state_file": "state.md",
  "runner_file": "runner.md"
}
```

The id uses lowercase ASCII letters, digits, and single hyphens and matches its directory. The name is `Opportunity: <subject>` with a trimmed nonempty single-line subject. The definition's first heading matches the name. References are distinct relative paths to nonempty files inside the package after resolving symlinks. Reject traversal, absolute paths, and other package discriminators. Create only these six manifest fields. Preserve unknown extensions during refinement and report them as warnings. Do not place status, schedules, providers, models, credentials, or machine bindings in the manifest.

## Definition

Use these sections in opportunity.md:

- `## Observation`: the need or possibility, with source context.
- `## Beneficiaries`: who benefits.
- `## Expected value`: the desired improvement and why it matters.
- `## Evidence`: known observations and references, separated from assumptions.
- `## Uncertainties`: assumptions that could change the investment decision.
- `## Effort and tradeoffs`: rough investment, dependencies, and competing uses of time.
- `## Smallest useful test`: bounded learning action and stopping condition.
- `## Decision criteria`: evidence that would justify pursuing, deferring, or declining.
- `## Revisit trigger`: a meaningful change that merits reassessment, or explicitly unknown.

Do not require certainty to capture a possibility. Mark missing information explicitly.

## State

Begin with `# Opportunity state` and exactly one preamble `Status: captured` line. Valid tokens:

- `captured`: preserved, not yet assessed.
- `evaluating`: actively reducing uncertainty.
- `deferred`: set aside by the user, with rationale and a revisit trigger.
- `pursued`: the user chose to invest. Delivery status belongs to a linked execution package.
- `declined`: the user chose not to invest, with rationale preserved.

Use sections `## Current assessment`, `## Next evaluation step`, `## Evidence and uncertainties`, `## Decision`, `## Revisit trigger`, and `## Execution package`.

The assessment briefly states expected benefit and confidence. Next evaluation step identifies the smallest useful learning action, or says no further evaluation is planned. Evidence and uncertainties contain current findings and their sources. Decision records the explicit user choice and rationale, or says no decision has been made. Deferred requires a meaningful trigger; pursued records a relative link or stable identifier to an execution package when one exists, otherwise explicitly says none has been created. Do not fabricate a link or imply delivery has begun. Definition holds the brief; state holds the current assessment and decision. Keep state a compact snapshot, not a journal.

## Runtime

The runner is self-contained and identical across packages. Resolve files from the supplied root, validate identity, paths, and lifecycle, and read definition and state before acting. Review/status are read-only. Evaluation writes only state; checkpoint reconciles supplied evidence; decide records explicit user choices. Refinement belongs to the designer.

Evaluation does not authorize delivery, experiment execution, contacting people, scheduling, or creating another package. Bounded investigation requires user authority. Evaluation of a deferred, pursued, or declined package may discuss the assessment but must not reopen its lifecycle without user instruction. Captured may advance to evaluating when evaluated. Pursue, defer, decline, and reopen are explicit decisions.

Before writing, reread state and reconcile newer evidence. Preserve unresolved conflicts rather than replacing another decision. Verify the write and validate the package. If persistence fails or is unavailable, report it and provide complete replacement state as a handoff. Do not claim that an unpersisted decision was saved.
