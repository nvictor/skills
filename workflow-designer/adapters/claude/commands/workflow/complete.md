---
description: Verify and mark a portable workflow complete without doing missing work.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform `workflow:complete`.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Treat `$ARGUMENTS` as an optional explicit workflow id or package path. Resolve the sole nonterminal workflow only when the target is omitted. Verify every terminal criterion without performing missing domain work.
