---
description: List portable workflows beneath the bound workflow root without changing them.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform the read-only `workflow:list` operation.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Do not search for workflow directories. Ignore `$ARGUMENTS` unless it supplies an explicit workflow root.
