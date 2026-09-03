# Portable coach runner

Use the package root supplied by the launcher or the directory containing this file.

## Before coaching

1. Read `manifest.json`.
2. Read the behavioral instructions named by `prompt_file`.
3. Read the canonical progress record named by `state_file`.
4. Continue an open interaction when appropriate; otherwise select the next useful objective from recorded evidence.

Treat the behavioral prompt as authoritative for coaching and the state file as authoritative for cross-agent continuity. Do not substitute private platform memory for newer package state.

## Run the session

Follow the behavioral prompt. Do not discuss package mechanics unless file access fails or conflicting state requires the learner's judgment.

## Preserve continuity

After every coaching turn, including a turn that asks the learner to respond:

1. Reread the state file immediately before writing.
2. Merge evidence from the current turn with any newer recorded evidence.
3. Record only observable work, demonstrated strengths, recurring gaps, feedback given, current difficulty, recent practice, next targets, and any open interaction.
4. Keep incomplete interactions separate from completed sessions.
5. Keep state compact:
   - Treat it as a current snapshot, never an append-only diary.
   - Replace or compact stale and superseded entries instead of appending another event.
   - Retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim.
   - Fold older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples.

Do not modify `manifest.json`, `prompt.md`, `runner.md`, `migration.json`, or deployment adapters.

If the state file is read-only or unavailable, continue the session and end the response with a `State handoff` section containing the complete proposed replacement contents of `state.md`. Never imply that state was saved when it was not.
