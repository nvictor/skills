---
name: opportunity-designer
description: Capture, evaluate, refine, and decide on portable opportunity packages for potential improvements before committing to delivery. Use for opportunity_file packages, not execution plans or general ongoing inquiries.
---

# Opportunity Designer

An opportunity preserves a potential improvement, expected value, supporting evidence, uncertainties, and the smallest next step needed to decide whether to pursue it. Its question is “Is this worth doing?” Optionality alone does not make a project an opportunity: a committed finite outcome belongs in a workflow.

## Routing and operations

Inspect a supplied manifest. Own `opportunity_file`; route `workflow_file`, `task_file`, `prompt_file`, and `conversation_file` to their respective designers. Report conflicting discriminators. Distinguish a decision about investing from delivery, repeated operations, capability development, and open inquiry.

- **Create:** Write a package without evaluating or executing it. Default to `/Users/victor/Developer/design/agents/opportunities/<id>` unless another destination is supplied. Keep this machine path out of canonical files.
- **Convert:** Capture supplied notes or discussion alongside the original source. Preserve attribution, uncertainty, and any explicit decision already made. Do not invent missing history.
- **Review / status:** Read only. Report structural issues or the current assessment, evidence, next step, and decision.
- **Refine:** Improve the brief without silently changing the decision or resetting continuity.
- **Evaluate:** Assess value and uncertainty, inspect relevant available evidence, and propose the smallest useful test. Persist the assessment and yield. Do not execute a proposed experiment unless the user requested it; an explicitly authorized bounded investigation may be performed. Do not begin delivery.
- **Checkpoint:** Reconcile supplied evidence or decisions without doing missing evaluation work.
- **Decide:** Record the user's explicit choice to pursue, defer, decline, or reopen. A recommendation is not a decision. On pursue, create a linked workflow or task only when requested, using its designer; preserve the opportunity rather than replacing it.

Read [references/package-format.md](references/package-format.md) for package operations. Use `assets/opportunity-package/` as the starter. Replace template markers and validate created or changed packages with `python3 scripts/validate_opportunity_package.py <package-root>`.

## Evaluation judgment

Capture the observed need, specific beneficiaries, expected change, evidence, key assumptions, rough effort and dependencies, tradeoffs, smallest useful test, decision criteria, and revisit trigger. Keep evidence separate from hypotheses and user agreement separate from agent advice. Personal enjoyment, learning, and creative value are valid benefits. Do not require financial returns, numerical scores, fabricated estimates, or a full project plan.

Prefer tests that could change the investment decision. State what evidence would support pursuing or declining, and when to stop investigating. Use a time or scope bound when performing an authorized investigation. Unknown benefit or effort stays unknown until supported. Deferred work needs a meaningful revisit trigger rather than a default deadline.

Use `captured`, `evaluating`, `deferred`, `pursued`, and `declined`. Evaluation normally moves captured to evaluating. Reassessing deferred or terminal decisions requires a user request to reopen. Never mark pursued because implementation seems useful, or declined because evidence is incomplete.

## Delivery

Summarize the package location, assessment or changes, validation result, and unresolved decision. After creation, provide this launcher with the real path:

```text
Evaluate the portable opportunity package at "<package-root>". Read and follow runner.md. Treat state.md as canonical continuity. Assess value and uncertainty; do not begin delivery or change the decision without my instruction.
```

Keep runtime bookkeeping out of the substantive discussion unless persistence fails. No schedule or automatic overdue behavior belongs to this package type.
