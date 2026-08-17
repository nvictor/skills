---
name: workflow-summary
description: Derive a compact handoff from a portable finite workflow's canonical files. Use when the user invokes `$workflow-summary` in Codex or `/workflow-summary` in Claude Code; delegate the read-only `workflow:summary` operation to `workflow-designer`.
---

# Workflow Summary

Read and follow the installed `workflow-designer` skill completely, then perform only `workflow:summary`.

Treat the remaining invocation text as an optional explicit workflow id or package path. Follow the canonical skill's target resolution, derived-handoff, read-only, and output contracts; do not store the summary as another source of truth.
