---
name: workflow-run
description: Execute or resume a portable finite workflow through the requested safe scope. Use when the user invokes `$workflow-run` in Codex or `/workflow-run` in Claude Code; delegate `workflow:run` to `workflow-designer`.
---

# Workflow Run

Read and follow the installed `workflow-designer` skill completely, then perform only `workflow:run`.

Treat the remaining invocation text as the target and optional execution scope. Follow the canonical skill's target resolution, eligibility, authority, checkpointing, persistence, and output contracts; this adapter grants no additional authority.
