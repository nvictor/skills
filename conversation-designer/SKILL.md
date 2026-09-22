---
name: conversation-designer
description: Create, convert, review, refine, resume, summarize, and checkpoint portable conversation packages that preserve an ongoing inquiry across agents. Use for conversation packages or manifests containing `conversation_file`, not ordinary chat, capability-building coaches, finite workflows, or repeatable tasks.
---

# Conversation Designer

Design conversations whose continuity exists to preserve and deepen an inquiry. Borrow the workflow's separation of state and memory and the coach's focused pacing, without prescribing practice, assessment, progression, or a completion target.

## Ownership and destination

Inspect a supplied manifest before selecting the designer. `conversation_file` identifies this package type; `prompt_file`, `workflow_file`, and `task_file` belong to the coach, workflow, and task designers respectively. Report conflicting discriminators rather than choosing silently.

Default new packages to `/Users/victor/Developer/design/agents/conversations/<id>`. Honor an explicit destination. This local default belongs only in the designer, never in generated canonical files. Use an explicit package path or the package already established in the current exchange for existing-package operations. Ask for a target when ambiguous; do not guess from recency or maintain an active-package pointer.

## Operations

- **Create:** Design and write a package. Do not begin the inquiry.
- **Convert:** Extract a package from supplied discussion or notes, preserving attribution, objections, uncertainty, and missing context. Preserve the source; do not reconstruct unavailable history.
- **Review:** Report evidence-backed findings without editing or advancing the conversation.
- **Refine:** Improve instructions while preserving unrelated continuity. Do not treat instruction changes as conversational progress.
- **Resume:** Respond to the current turn using the package, then persist continuity and yield. Subsequent user replies in that established conversation continue this operation unless the user changes intent.
- **Summarize:** Produce a compact read-only handoff of the inquiry, current position, competing explanations, and unresolved threads.
- **Checkpoint:** Reconcile supplied discussion into continuity without answering its open question or advancing the inquiry.

Read [package-format.md](references/package-format.md) for any package operation. For create, convert, review, or refine, also read [quality-rubric.md](references/quality-rubric.md). Copy `assets/conversation-package/` as the starting structure for new packages; replace all template markers. Keep the generic runner identical across packages unless its runtime contract must change.

## Design

Use available context to establish the subject, intent, preferred depth and style, boundaries, and starting or resume point. Ask only about missing choices that materially affect the conversation. A broad topic can start with a focused opening; it does not need a curriculum or a planned sequence of questions.

Write instructions that answer directly and develop one main idea at a time. Follow curiosity through examples, objections, and revised explanations when useful, without forcing these into stages. Allow pauses, branches, and returns. Do not require a question at the end of each response.

Separate the user's hypothesis, the agent's explanation, and evidence-supported conclusions. An explanation offered is not understanding demonstrated or agreement established. Record what was discussed and what remains unsettled, not invented learning outcomes. Preserve consequential objections even when a new thread becomes the focus.

Keep state positional and memory semantic. Both are compact current documents, not transcripts or append-only journals. Retain a superseded hypothesis only when its revision remains useful. Do not fill missing source context with plausible details.

## Validation and delivery

Run `python3 scripts/validate_conversation_package.py <package-root>` relative to this skill after creating, converting, or refining a package. Fix structural errors, then apply the quality rubric to behavior. The validator cannot establish that an inquiry was faithfully understood.

For creation or refinement, report the package location, validation, and material unresolved context. Provide this launcher with the actual path:

```text
Resume the portable conversation package at <package-root>. Read and follow runner.md. Treat state.md and memory.md as canonical cross-agent continuity.
```

For resume, keep the visible response conversational. Report persistence problems when they occur, without adding routine bookkeeping reports to every turn. Review and summary never modify files. Checkpoint reports continuity changes only. Do not create schedules, wrapper skills, or external effects as part of these operations.
