---
name: workflow-next
description: Identify the next valid action for a portable finite workflow without performing it. Use when the user invokes `$workflow-next` in Codex or `/workflow-next` in Claude Code; delegate the read-only `workflow:next` operation to `workflow-designer`.
---

# Workflow Next

Read and follow the installed `workflow-designer` skill completely, then perform only `workflow:next`.

Treat the remaining invocation text as an optional explicit workflow id or package path. Follow the canonical skill's target resolution, advisory-only, verification, and output contracts; do not perform domain work.
