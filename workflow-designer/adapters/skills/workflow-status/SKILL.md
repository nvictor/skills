---
name: workflow-status
description: Report the verified current status of a portable finite workflow. Use when the user invokes `$workflow-status` in Codex or `/workflow-status` in Claude Code; delegate the read-only `workflow:status` operation to `workflow-designer`.
---

# Workflow Status

Read and follow the installed `workflow-designer` skill completely, then perform only `workflow:status`.

Treat the remaining invocation text as an optional explicit workflow id or package path. Follow the canonical skill's target resolution, verification, read-only, and output contracts.
