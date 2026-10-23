# Portable coach runner

Use the package root supplied by the learner or the directory containing this file.

## Before coaching

1. Read `manifest.json`.
2. Read the behavioral instructions named by `prompt_file`.
3. Read the topic map and sequencing guide named by `curriculum_file`.
4. Read the canonical progress record named by `state_file`.
5. Resume an open interaction from its recorded phase: pending check, remediation, or practice attempt. For legacy `awaiting_readiness`, honor pause or revisit requests; otherwise acknowledge demonstrated understanding and continue naturally within the session budget. Do not automatically reteach or restart. Reteach only on request or evidence of need. Preserve unknowns in legacy state and ask one focused clarification only when needed. Otherwise select the next useful objective from the learner's request and recorded evidence.

Treat the behavioral prompt as authoritative for coaching and the state file as authoritative for cross-agent continuity. Do not substitute private platform memory for newer package state.

## Run the session

Follow the behavioral prompt. Do not discuss package mechanics unless file access fails or conflicting state requires the learner's judgment.

## Preserve continuity

After every coaching turn, including a turn that asks the learner to respond:

1. Reread the state file immediately before writing.
2. Merge evidence from the current turn with any newer recorded evidence.
3. Record only observable work, demonstrated strengths, recurring gaps, feedback given, current difficulty, recent practice, next targets, and any open interaction. For incomplete learning, retain mode, current concept/objective, phase, outstanding question, understanding evidence, unresolved misconception, next concept, readiness status, and any exhausted session budget.
4. Keep incomplete interactions separate from completed sessions. Session limits pause the current phase; they do not establish understanding, readiness, or mastery.
5. Keep state compact:
   - Treat it as a current snapshot, never an append-only diary.
   - Replace or compact stale and superseded entries instead of appending another event.
   - Retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim.
   - Fold older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples.

Do not modify `manifest.json`, `prompt.md`, `curriculum.md`, `runner.md`, or `migration.json`.

If the state file is read-only or unavailable, continue the session and end the response with a `State handoff` section containing the complete proposed replacement contents of `state.md`. Never imply that state was saved when it was not.
