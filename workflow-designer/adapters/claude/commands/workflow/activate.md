---
description: Select a nonterminal portable workflow beneath the bound workflow root.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform `workflow:activate` for `$ARGUMENTS`.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Require an explicit workflow id or package path. Change only root selection state; do not execute workflow work or change package lifecycle state.
