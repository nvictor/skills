# Workflow quality rubric

Read this file completely for create, convert, refine, or review operations. Apply the rubric silently while authoring. Report evidence-backed findings during review.

## Finite objective

- Define one coherent objective with observable value.
- Define a reachable terminal condition for the whole workflow.
- Exclude indefinite schedules and unrelated recurring operations.
- Allow only loops that can terminate, block, or reach a decision gate.

## Step design

- Use the fewest steps that preserve meaningful dependencies and checkpoints.
- Give every step clear eligibility, outcome, and completion evidence.
- Make branches, loops, approval gates, and transitions unambiguous.
- Ensure every nonterminal position has a valid next action or explicit blocker.
- Avoid prescribing domain lifecycle concepts that the workflow does not need.

## Completion integrity

- Require observable evidence before marking a step complete.
- Distinguish current-step completion from whole-workflow completion.
- Never infer completion from effort, elapsed time, or an agent assertion alone.
- Keep unverified historical claims explicitly unverified.

## State quality

- Make state answer where execution is now.
- Record current position, verified completed work, blockers, pending decisions, working artifacts, and interrupted work.
- Keep state compact enough for a new agent to orient quickly.
- Avoid storing rationale, transcripts, or accumulated semantic context in state.

## Memory quality

- Make memory preserve decisions, discoveries, rejected approaches, and durable context.
- Include concise rationale or provenance when future agents need it.
- Avoid event logs, scratch notes, duplicate state, and conversational exhaust.
- Compact obsolete detail without losing current conclusions.

## Resume and handoff

- Let a fresh agent identify the current position without reconstructing chat history.
- Let `workflow:next` identify one valid action without performing it.
- Make safe checkpoints and interrupted operations recoverable.
- Reread continuity files before writing and merge newer evidence.
- Provide complete state and memory handoffs when writing is unavailable.

## Control-plane integrity

- Keep the workflow root user-selected and outside portable package configuration.
- Make root discovery deterministic through an explicit path, launcher binding, or nearest workspace binding; never through a broad directory search.
- Keep root `state.json` limited to workspace selection.
- Make `workflow:list` read only and `workflow:activate` selection only.
- Resolve explicit target, active pointer, then sole nonterminal candidate without silently persisting fallback selection.
- Keep `workflow:status`, `workflow:next`, and `workflow:summary` read-only.
- Require explicit execution intent for `workflow:run`.
- Default an unscoped run to one coherent unit through the next safe checkpoint.
- Require verified terminal evidence for `workflow:complete`.
- Clear the active pointer after completion only when it still selects that package.
- Keep summaries derived rather than authoritative.
- Keep design, execution, and external-effect authority separate.

## Safety and authority

- Treat package constraints as intended limits, not permission grants.
- Stop before missing approvals, unavailable capabilities, unsafe effects, or ambiguous destructive targets.
- Preserve partial and uncertain outcomes precisely enough to prevent duplicate or contradictory work.
- Never claim execution, effects, completion, or persistence without verification.

## Portability

- Keep canonical behavior independent of provider, model, chat, and machine.
- Use the minimal manifest and safe relative file references.
- Keep absolute workflow-root paths out of packages and root `state.json`.
- Keep domain procedure in `workflow.md` and the generic protocol in `runner.md`.
- Make the package understandable and resumable by another capable agent with equivalent authority and resources.

## Final review

Confirm that:

- the objective is finite and the terminal condition is verifiable
- every step can complete, transition, block, or request a decision
- state and memory have distinct, useful roles
- root selection and package lifecycle remain distinct
- read-only operations cannot accidentally execute work
- activation cannot alter package progress
- a run has a safe default boundary
- continuity updates remain truthful under partial work and concurrent changes
- another agent can resume from package files alone
