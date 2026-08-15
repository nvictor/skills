---
description: Clear the selected portable workflow pointer without changing package state.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform the explicit `workflow:deactivate` escape hatch.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Ignore `$ARGUMENTS` unless it identifies the workflow that must still be selected. Change only root selection state.
