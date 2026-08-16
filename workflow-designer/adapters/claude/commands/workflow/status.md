---
description: Report a portable workflow's verified status without changing it.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform the read-only `workflow:status` operation.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Treat `$ARGUMENTS` as an optional explicit workflow id or package path. Do not search for workflow directories. Resolve the sole nonterminal workflow only when the target is omitted, read its canonical files, and return the status output required by the skill.
