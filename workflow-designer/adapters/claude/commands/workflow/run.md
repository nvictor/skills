---
description: Execute or resume a portable workflow through a requested safe checkpoint.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform `workflow:run` with the scope in `$ARGUMENTS`.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Resolve an explicit target or the sole nonterminal workflow. Follow the package runner, honor authority boundaries, and persist truthful state after the attempt. When scope is absent, stop after one coherent unit at the next safe checkpoint.
