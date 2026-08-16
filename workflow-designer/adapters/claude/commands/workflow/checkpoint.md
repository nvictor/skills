---
description: Reconcile externally completed work into a portable workflow without performing domain work.
allowed-tools: Bash(python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate *)
---

Use the `workflow-designer` skill to perform `workflow:checkpoint` with the target and evidence in `$ARGUMENTS`.

The workspace binding resolves to:

!`python3 ~/.claude/skills/workflow-designer/scripts/manage_workflow_root.py locate "${CLAUDE_PROJECT_DIR}"`

Resolve an explicit target or the sole nonterminal workflow. Inspect the supplied evidence and relevant artifacts, update continuity only, and do not perform missing domain work.
