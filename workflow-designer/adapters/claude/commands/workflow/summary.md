---
description: Derive a compact handoff for the selected portable workflow without changing it.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform the read-only `workflow:summary` operation.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Treat `$ARGUMENTS` as an optional explicit workflow id or package path. Derive the handoff from canonical files and do not save it as new state.
