# Opportunity runner

Resolve manifest.json from the supplied package root. Require schema_version 1, an id matching the lowercase hyphenated folder name, and an Opportunity: name matching the definition title. Require opportunity_file, state_file, and runner_file to reference distinct nonempty files inside the root after resolving symlinks. Reject absolute paths, parent traversal, and conflicting workflow_file, task_file, prompt_file, or conversation_file discriminators. Read definition and state before acting. Require exactly one Status line before state sections, using captured, evaluating, deferred, pursued, or declined. Report invalid or conflicting context before writing.

Choose the operation from the user's instruction:

- Status or review: report the current assessment, next step, evidence, uncertainty, and decision without writing or advancing evaluation.
- Evaluate: answer the current question, assess expected value, inspect relevant available evidence, and recommend a bounded test that could change the decision. Distinguish evidence, assumptions, and advice. Do not invent confidence, estimates, history, or agreement. Do not execute the proposed test unless explicitly requested. Any authorized investigation must have a scope or time bound and stopping condition. Persist the current assessment and yield.
- Checkpoint: reconcile supplied evidence or an explicit decision without performing missing work.
- Decide: record the user's explicit choice and rationale to pursue, defer, decline, or reopen. Recommendations and silence are not decisions.

Captured may become evaluating during evaluation. Deferred, pursued, and declined remain unchanged unless the user explicitly reopens or changes the decision. Deferred needs a reason and meaningful revisit trigger. Pursued means an investment decision, not completed delivery. Link to an execution package only if it exists; otherwise record that none has been created. Creation of a workflow or task requires a user request and the corresponding designer. Preserve this opportunity's rationale and identity.

Write only state.md during runtime. Keep its sections Current assessment, Next evaluation step, Evidence and uncertainties, Decision, Revisit trigger, and Execution package. Keep a compact current snapshot rather than an activity log. Preserve sources and uncertainty. Do not rewrite the definition or runner while evaluating. Package refinement is a separate operation.

Reread state immediately before writing and reconcile newer information. Surface material conflicts rather than silently overwriting decisions. Reread and verify saved state and validate the package with the opportunity designer's validator when available, otherwise verify the contract manually. If writes fail or are unavailable, identify what was not saved and provide complete replacement state as a handoff.

This package grants no authority for delivery, external changes, messages, schedules, or experiment execution. Follow the actual user's authorized scope. Do not add overdue behavior or require periodic reviews.
