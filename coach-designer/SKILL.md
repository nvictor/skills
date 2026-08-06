---
name: coach-designer
description: Design, review, refine, and package portable long-running AI coaches that build durable skills through deliberate practice, feedback, adaptive difficulty, and progress tracking. Use when creating a coach, auditing or improving an existing coach, converting prompts or scheduled coaches into agent-neutral coach packages, or producing a standalone coach prompt.
---

# Coach Designer

## Purpose

Design learning systems that produce durable changes in what a learner can do. Author portable coach packages whose behavior, schedule, and canonical state can survive a change of AI agent or scheduler. Do not teach the requested subject or deploy a scheduled task unless the user explicitly asks.

## Select the operation

Choose the operation that matches the request:

- **Create:** Design a new coach. Create a package when the user provides or implies a destination; otherwise return a standalone prompt.
- **Review:** Inspect an existing coach and report evidence-backed findings without changing it.
- **Refine:** Improve an existing prompt or package while preserving unrelated content and recorded state.
- **Migrate:** Convert legacy prompts, scheduled coaches, or combined documents into packages without changing behavior or live deployments.
- **Prompt only:** Return one self-contained, provider-neutral coach prompt ready to paste into an AI agent.

Treat deployment as a separate operation. Package creation or migration never authorizes creating, updating, pausing, or deleting a live scheduled task.

For create, refine, or review, read `references/quality-rubric.md` completely. For any package operation, also read `references/package-format.md` completely. Copy `assets/coach-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_coach_package.py` before delivery.

## Workflow

### 1. Inspect existing context

Use the request, conversation, available learner profile, existing coach files, deployed configuration, and progress records. Avoid repeating answered questions.

For an existing coach, identify separately:

- the canonical or saved prompt
- the deployed prompt, when available
- schedule, timezone, and enabled state
- runtime-specific settings
- durable progress or conversation memory

Do not silently choose between conflicting sources. Report the conflict and preserve every source until the user selects the intended one.

### 2. Complete the learner brief

Determine only what materially affects the coach:

- the skill to develop
- relevant background and current ability
- the observable long-term transformation
- session duration and interaction style
- preferred learning style and tolerance for challenge
- practice cadence and timezone when creating a package
- continuity requirements
- privacy, safety, or domain constraints

Ask one compact set of questions only when missing information would materially change the result. Infer safe details when possible.

Keep schedule and deployment metadata out of the behavioral prompt. Put them in the manifest.

### 3. Design the learning system

Define an observable long-term outcome, using this horizon when appropriate:

> After approximately 100 sessions, the learner should be able to...

Decompose it into the fewest useful competencies, decisions, habits, and performance standards. Make later design choices support that transformation.

Prefer active methods:

- deliberate practice and focused drills
- simulations, role play, and realistic scenarios
- projects, experiments, debugging, or design work
- critique, revision, and immediate retry
- case analysis and decisions under constraints
- retrieval practice and spaced review
- reflection, explanation, and teaching back

Use instruction sparingly and just in time. Give the learner a meaningful attempt before supplying a full solution whenever the domain permits it.

Use a bounded session loop:

1. Select one objective from observed needs and prior progress.
2. Give a realistic challenge with clear constraints and a definition of done.
3. Let the learner attempt it without premature rescue.
4. Assess the attempt against explicit, domain-relevant criteria.
5. Give specific feedback tied to evidence from the attempt.
6. Require a revision, retry, transfer task, or concise reflection.
7. Record progress and choose the next useful target.

Adapt the loop when another sequence fits the skill better.

### 4. Define progression, feedback, and continuity

Start with a baseline task or existing evidence. Increase difficulty only after demonstrated readiness. Change one relevant dimension at a time, such as ambiguity, complexity, independence, pressure, competing constraints, realism, consequences, transfer, or expected quality.

Define mastery, remediation, and spaced review. Create enough practice modes and scenario variables to remain useful after 50 sessions without relying on random novelty.

Tailor the feedback rubric to the skill. Require feedback to:

- cite specific evidence from the learner's work
- separate important gaps from optional refinements
- explain the consequence of each important gap
- give one actionable next move
- acknowledge strong work precisely
- create an immediate opportunity to apply the feedback

Track only completed work, demonstrated strengths, recurring errors, feedback already given, current difficulty, recent practice, and next targets. Never invent history. Treat package `state.md` as canonical when a runner is available, update it after every coaching turn, and preserve incomplete interactions. When file writing is unavailable, produce the complete replacement state as a handoff.

### 5. Write the artifacts

Write operational instructions that another capable agent can follow. Make the prompt self-contained enough to work when copied alone while keeping scheduler and vendor configuration outside it.

Include relevant concerns when they improve execution:

- purpose and role
- necessary learner context
- long-term transformation
- competencies and success criteria
- coaching philosophy
- session structure and practice modes
- feedback framework
- progression and adaptation
- continuity behavior
- constraints and anti-patterns
- explicit starting behavior

Use “session,” not platform terms such as “automation run.” Do not include model names, scheduler syntax, notification settings, project identifiers, or machine-specific paths in `prompt.md`.

For packages, write the manifest, runner, prompt, and state according to `references/package-format.md`. Include `migration.json` only for migrations. Keep the runner generic: it must locate files from the package root supplied by the launcher rather than embed a provider or machine path.

## Preservation-first migration

Perform migration and improvement as separate passes.

During migration:

1. Create packages alongside the sources; never replace or move source files.
2. Copy the selected prompt without rewriting its behavior.
3. Preserve the complete progress record. Do not summarize away source history.
4. Translate schedule metadata without changing its meaning. Preserve the original timezone and flag missing or suspicious timezone data.
5. Record provenance, checksums, conflicts, and warnings in `migration.json`.
6. Mark undocumented or non-deployed definitions as draft or archived rather than activating them.
7. Set `behavior_changed` and `deployment_changed` accurately.
8. Validate the package and report what would change if it were later deployed.

Do not merge coaches, improve prompts, normalize timezones, reset state, or update live tasks during a preservation migration. Offer those as a separate refinement after the lossless package exists.

## Constraints

Prevent a generated coach from:

- defaulting to lectures or information dumps
- solving tasks before a fair attempt
- praising weak or incomplete work
- inventing learner history, preferences, or results
- repeating scenarios mechanically
- asking unnecessary setup questions every session
- increasing difficulty before demonstrated readiness
- changing several difficulty dimensions without a reason
- treating entertainment, volume, or speed as evidence of growth
- ending without feedback, application, or a clear next target

Keep sessions within the requested duration. Preserve psychological safety without weakening accurate critique. Add appropriate verification and safety boundaries for regulated, hazardous, medical, legal, financial, or other high-stakes domains.

## Validation and deployment boundary

Run the package validator after every create, refine, or migrate operation. Fix errors before delivery and report warnings that require judgment.

For prompt-only work, apply the coach quality rubric silently. For reviews, report the rubric findings instead of rewriting unless the user asks for changes.

Do not deploy merely because a package is valid. If deployment is explicitly requested, use the current platform's native scheduling capability, preserve unrelated live settings, and make its prompt a minimal launcher that names the package root and delegates to `runner.md`. Verify the resulting schedule, runner path, and enabled state, and retain a recoverable snapshot.

## Output contract

Match the result to the operation:

- **Create, refine, or migrate with an authorized destination:** Write and validate the package, then summarize the files, validation, preserved behavior, and unresolved warnings.
- **Review:** Return prioritized, evidence-backed findings. Do not modify files.
- **Prompt only:** Return only the completed coach prompt, without a preface, design notes, a Markdown fence, placeholders, or TODOs.
- **Deployment:** Report package changes and live deployment changes separately.

Never claim behavior preservation unless the prompt and state provenance have been verified.
