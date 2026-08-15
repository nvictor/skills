---
description: Report the next valid action for the selected portable workflow without performing it.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform the read-only `workflow:next` operation.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Treat `$ARGUMENTS` as an optional explicit workflow id or package path. Do not perform domain work.
