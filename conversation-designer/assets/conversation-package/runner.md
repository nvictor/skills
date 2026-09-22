# Conversation runner

## Read context

Resolve `manifest.json` from the supplied package root. Require `conversation_file` as the sole package discriminator; conflicting `prompt_file`, `workflow_file`, or `task_file` fields are errors. Resolve `conversation_file`, `state_file`, `memory_file`, and `runner_file` as distinct relative files inside the package, including after symlink resolution. Read all four before acting. If required context is missing, report the gap rather than inventing continuity.

Select the requested operation: resume, summarize, review, or checkpoint. A launcher asking to continue the conversation selects resume, as do subsequent replies in that established exchange. If intent or target is ambiguous, clarify. Creating or refining a package does not select resume.

## Resume

Answer the current user turn directly, using the definition, state, and memory. A new message takes precedence over an older resume suggestion. With no new question, use the recorded resume point for one focused response; for a fresh package use starting behavior.

Develop one main idea at a time. Offer examples or challenges when helpful, follow branches, and allow returns. Do not force stages, exercises, assessment, or a completion target. Do not require a closing question. Never simulate the user's next reply or treat silence as agreement.

Preserve whose hypothesis or explanation each claim is. An explanation offered does not establish understanding demonstrated. Keep unresolved objections and qualified conclusions intact. Do not reconstruct missing examples or history.

Prepare a current state snapshot containing the question, unresolved threads, pending exchange, and resume point. Record what the response actually offers, without claiming the user accepted it. Update memory only for durable distinctions, attributed hypotheses, examples, objections, revisions, or qualified conclusions. Compact superseded detail and retain useful reasons for revisions.

Persist continuity as described below, deliver the conversational response, and yield to the user. Do not add routine state reports to the response.

## Read-only operations

Summarize the inquiry, current position, competing explanations, and unresolved threads from the canonical files. Review reports evidence-backed continuity or behavior problems. Neither operation modifies files or answers the outstanding inquiry as a new conversation turn.

## Checkpoint

Reconcile supplied discussion or notes into state and memory only. Preserve attribution, uncertainty, and source limitations. Do not answer an open question, fabricate a missing response, or treat an agent explanation as user agreement. Report the actual continuity changes, including no change when appropriate.

## Persist continuity

Write only the files named by `state_file` and `memory_file`. Do not change the manifest, definition, or runner during runtime operations. Continuity authority does not authorize unrelated filesystem or external actions.

Immediately before writing, reread both continuity files and reconcile newer information. If a material conflict cannot be resolved from explicit evidence, preserve it and ask for judgment instead of overwriting it. Keep state positional and memory semantic, not append-only logs. Verify both files after writing before claiming persistence.

If either write is unavailable or fails, report accurately which changes were saved and provide complete intended replacement contents under `State handoff` and `Memory handoff`. Do not claim those handoffs are persisted. Yield after the current turn; never loop autonomously to pursue the inquiry.
