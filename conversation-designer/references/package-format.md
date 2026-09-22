# Portable conversation package format

## Files and identity

Use UTF-8 text and these five files: `manifest.json`, `conversation.md`, `state.md`, `memory.md`, and `runner.md`. The manifest uses:

```json
{
  "schema_version": 1,
  "id": "example",
  "name": "Conversation: Example",
  "conversation_file": "conversation.md",
  "state_file": "state.md",
  "memory_file": "memory.md",
  "runner_file": "runner.md"
}
```

Use lowercase ASCII letters, digits, and single hyphens in the id, matching the package directory. The name has the exact prefix `Conversation: ` and a nonempty trimmed subject on one line. Use that exact name as the first heading in the conversation document.

File references must be distinct relative paths to nonempty files inside the package, including after resolving symlinks. Reject absolute paths, parent traversal, and conflicting package discriminators. Create only the seven manifest fields above. Preserve unknown extensions on refinement and report them as warnings rather than silently deleting them. No status, schedule, provider, model, credentials, or machine configuration belongs in this contract.

## Conversation definition

Use sections `## Subject and intent`, `## Conversational style`, `## Boundaries`, and `## Starting behavior`. Describe what makes the inquiry worthwhile and how to enter it. Do not encode a mandatory path through observation, hypothesis, counterexample, and conclusion. Do not add mastery measures or terminal criteria.

## State

Use sections `## Current question`, `## Unresolved threads`, `## Pending exchange`, and `## Resume point` under `# Conversation state`.

Record the current focus, parked branches, relevant unanswered user objection, and enough of the last exchange to avoid repeating it. Identify who, if anyone, is being asked to respond. A response that asks no question can legitimately leave no pending answer. The resume point is a useful entry into the inquiry, not a compulsory next step. A new package may say that no exchange has occurred. Do not introduce lifecycle tokens or interpret silence as completion.

## Memory

Use sections `## Hypotheses and explanations`, `## Distinctions and examples`, `## Objections and revisions`, and `## Qualified conclusions` under `# Conversation memory`.

Attribute claims to the user, agent, or a source as appropriate. Distinguish proposals, evidence, and agreement. Preserve uncertainty and the scope of conclusions. For example, record that an agent discussed descending choruses; do not infer that the user understands chorus function. Keep useful references with the claims they support. Never invent an omitted song, exact objection, or source exchange.

Replace stale statements with current knowledge. Retain the reason for an important revision without keeping an exhaustive history. State may point to a durable objection in memory rather than duplicating its full explanation.

## Runtime contract

The generic runner resolves all four referenced documents from the supplied package root and reads them before responding. It implements resume, summarize, review, and checkpoint. Design operations belong to the designer.

Resume answers the user directly, or uses the recorded resume point if no new question is supplied. It produces one focused turn and yields; it does not simulate the user's reply. A fresh package follows starting behavior. It writes only state and memory. Ordinary conversational replies continue the established package without requiring the user to invoke it again.

Review and summarize are read-only. Checkpoint records supplied context without advancing the inquiry. Refinement never silently resets continuity. Instructions and the runner remain unchanged during runtime operations.

Before continuity writes, reread both files and reconcile newer information. Preserve material conflicts rather than silently choosing a history. Verify both written files before claiming persistence. If writes are unavailable or fail, provide complete `State handoff` and `Memory handoff` replacement contents and identify what was not saved. Partial persistence must be reported accurately.

Packages authorize conversational continuity, not unrelated filesystem or external actions. Keep responses natural; routine bookkeeping need not be narrated.
