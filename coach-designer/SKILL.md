---
name: coach-designer
metadata:
  version: "3.0.0"
description: Design, review, refine, package, and run portable long-running AI coaches that build durable skills through deliberate practice, feedback, adaptive difficulty, and progress tracking. Coaches run manually, on demand. Use for coach packages, including creating or improving a coach or its curriculum, converting prompts or scheduled coaches into agent-neutral manual packages, or producing a standalone coach prompt.
---

# Coach Designer

## Purpose

Design learning systems that produce durable changes in what a learner can do. Author portable coach packages whose behavior, curriculum, target cadence, and canonical state can survive a change of AI agent. Coaches are run manually by the learner; the package never schedules or deploys itself. Do not teach the requested subject unless the user explicitly asks.

## Canonical naming

Use manifest `name` as the source of truth for human-facing package names, with the format `Coach: <subject>`. See `references/package-format.md` for field rules. Match the main document title and app display labels to that name. Preserve directory names, ids, slash-command identifiers, and historical records.

## Package ownership

Own a package when its manifest contains `prompt_file`. This includes later requests to run, pause, or resume that coach package. If asked to automate or schedule a coach, explain that coaches run manually and offer a target cadence in the manifest instead.

When the target package type is unknown, inspect its manifest before selecting a workflow:

- `conversation_file` identifies an ongoing inquiry; use the conversation designer.
- `prompt_file` identifies a coach package; continue with this skill.
- `task_file` identifies a task package; use the task designer instead.

Report conflicting discriminators instead of choosing silently.

## Select the operation

Choose the operation that matches the request:

- **Create:** Design a new coach. Create a package when the user provides or implies a destination; otherwise return a standalone prompt.
- **Review:** Inspect an existing coach and report evidence-backed findings without changing it.
- **Refine:** Improve an existing prompt or package while preserving unrelated content and recorded state.
- **Migrate:** Convert legacy prompts, scheduled coaches, or combined documents into manual packages, splitting the curriculum from the prompt and dropping deployments.
- **Prompt only:** Return one self-contained, provider-neutral coach prompt ready to paste into an AI agent.
- **Run:** Run a validated coach package only when explicitly requested.

Never create, update, pause, or delete a live scheduled task for a coach.

For create, refine, or review, read `references/quality-rubric.md` completely. For any package operation, also read `references/package-format.md` completely. Copy `assets/coach-package/` when a new package needs a starting structure, replace every template marker, and run `scripts/validate_coach_package.py` before delivery.

## Examples

Create a package with a weekly target cadence:

```text
Use the coach-designer skill to create a five-minute architecture judgment coach in design/agents/coaches/architecture-judgment-coach. Target one session per week.
```

Migrate a scheduled coach to a manual package:

```text
Use the coach-designer skill to migrate this scheduled coach into design/agents/coaches/<coach-id>. Preserve its prompt and state, split out the curriculum, and keep its frequency as the target cadence. Do not change the live task.
```

Review a package without editing it:

```text
Use the coach-designer skill to review design/agents/coaches/communication-coach for deliberate practice, useful progression, portability, and overlap with other coaches. Report findings only.
```

Run an existing package (Dashi copies this prompt with the real package root):

```text
Run the portable coach package at `<package-root>`. Read and follow `runner.md`. Treat `state.md` as the canonical cross-agent state.
```

## Workflow

### 1. Inspect existing context

Use the request, conversation, available learner profile, existing coach files, and progress records. Avoid repeating answered questions.

For an existing coach, identify separately:

- the canonical or saved prompt
- the curriculum, whether separate or embedded in the prompt
- the target cadence
- durable progress or conversation memory

Do not silently choose between conflicting sources. Report the conflict and preserve every source until the user selects the intended one.

### 2. Complete the learner brief

Determine only what materially affects the coach:

- the skill to develop
- relevant background and current ability
- the observable long-term transformation
- session duration and interaction style
- preferred learning style and tolerance for challenge
- target cadence (for example weekly) when creating a package
- continuity requirements
- privacy, safety, or domain constraints

Ask one compact set of questions only when missing information would materially change the result. Infer safe details when possible.

Keep cadence metadata out of the behavioral prompt. Put it in the manifest.

### 3. Design the learning system

Define an observable long-term outcome, such as what the learner should be able to do after approximately 100 sessions, and the fewest competencies needed to reach it. Put the outcome, competencies, learning map, and progression criteria in `curriculum.md`. Keep coaching behavior in `prompt.md`. Design meaningful practice, feedback, assessment, and progression around that outcome. Use deliberate practice, simulations, projects, critique and revision, retrieval, reflection, or teaching back as appropriate. Wait for a meaningful practice attempt before supplying its solution, while teaching missing prerequisites when needed.

#### Teaching approach

Teach progressively, adapting to the learner's goals, prior knowledge, and demonstrated understanding.

- Introduce concepts in a sensible prerequisite order.
- Explain clearly, with examples when useful.
- Check understanding before advancing to material that depends on it. Use questions, applications, teach-backs, or observed work as appropriate.
- Adapt explanations and practice when the learner struggles. Do not mistake a correct guess for durable mastery.
- Favor deliberate practice, evidence-based feedback, and opportunities to improve.
- Increase difficulty when performance supports it.
- Keep the conversation natural. Do not require fixed sentence counts, a checking question after every explanation, or a separate readiness confirmation after every successful assessment.
- Respect requests to pause, slow down, practice more, or revisit a concept.

Use judgment to decide when to explain, assess, practice, or continue. Avoid unnecessary confirmation questions and artificial transitions. Keep each session within its limits; preserve unfinished work for resumption.

Choose guided explanation for unfamiliar material and practice for previously learned material or explicit practice requests. Collect necessary setup facts without treating them as tests. Let the agent adapt the teaching sequence instead of imposing a fixed conversational protocol.

Legacy interaction phases remain valid. Resume pending checks, remediation, or practice from recorded evidence without restarting. For `awaiting_readiness`, honor a pause or revisit request; otherwise acknowledge demonstrated understanding and continue naturally within the session budget. Unknown understanding remains unknown and must be assessed before dependent material. Preserve existing state fields and useful history; no state conversion is required.

### 4. Define progression, feedback, and continuity

Start with existing evidence, a guided explanation and check for unfamiliar material, or a bounded baseline task for suitable learned material. Increase difficulty only after demonstrated readiness. Change one relevant dimension at a time, such as ambiguity, complexity, independence, pressure, competing constraints, realism, consequences, transfer, or expected quality.

Define mastery, remediation, and spaced review in the curriculum. Create enough practice modes and scenario variables to remain useful after 50 sessions without relying on random novelty.

Tailor the feedback rubric to the skill. Require feedback to:

- cite specific evidence from the learner's work
- separate important gaps from optional refinements
- explain the consequence of each important gap
- give one actionable next move
- acknowledge strong work precisely
- create a focused check or practice application within the remaining budget

Track only observable work, demonstrated strengths, recurring errors, feedback already given, current difficulty, recent practice, and next targets. Never invent history. Treat package `state.md` as canonical when a runner is available, update it after every coaching turn, and preserve incomplete interactions. Record the current objective, interaction position, outstanding work, observed evidence, and any exhausted session budget. Resume unfinished work naturally without automatically reteaching or restarting. Reteach only on request or evidence of need. For legacy state missing these details, preserve useful history, mark unknowns, and ask one focused clarification only when necessary. Keep runtime bookkeeping outside the teaching flow unless access fails or a conflict requires judgment. When file writing is unavailable, produce the complete replacement state as a handoff.

### 5. Write the artifacts

Write operational instructions that another capable agent can follow. Make the prompt self-contained enough to work when copied alone while keeping vendor configuration outside it. Point it to `curriculum.md` for topics and sequencing.

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

For packages, write the manifest, runner, prompt, curriculum, and state according to `references/package-format.md`. Include `migration.json` only for migrations. Keep the runner generic: it must locate files from the package root supplied by the learner rather than embed a provider or machine path.

## Preservation-first migration

For the one-time update from the legacy teaching protocol to the four teaching
guarantees, read [scripts/migrations/README.md](scripts/migrations/README.md).
This is a behavioral refinement of existing packages, separate from the
preservation migration below. Do not run it during ordinary coach operations.

Perform migration and improvement as separate passes.

During migration:

1. Create packages alongside the sources; never replace or move source files.
2. Copy the selected prompt without rewriting its behavior.
3. Preserve the complete progress record. Do not summarize away source history.
4. Translate the source schedule into a target cadence: keep `frequency` and `interval`, set `enabled` to `false`.
5. Move curriculum content (topic maps, competencies, sequencing, review rules) from the prompt into `curriculum.md` and point the prompt to it. Report any behavior change.
6. Record provenance, checksums, conflicts, and warnings in `migration.json`.
7. Mark undocumented definitions as draft or archived rather than activating them.
8. Set `behavior_changed` accurately.
9. Validate the package.

Do not merge coaches, reset state, or update live tasks during a migration. Offer prompt improvements as a separate refinement. Tell the user that any old scheduled task is theirs to remove.

## Constraints

Prevent a generated coach from:

- defaulting to lectures or information dumps
- supplying a practice solution before a fair attempt, while still teaching missing prerequisites
- praising weak or incomplete work
- inventing learner history, preferences, or results
- repeating scenarios mechanically
- asking unnecessary setup questions every session
- increasing difficulty before demonstrated readiness
- changing several difficulty dimensions without a reason
- treating entertainment, volume, or speed as evidence of growth
- forcing feedback application or advancement to claim a completed session when its budget has expired

Keep sessions within the requested duration. Preserve psychological safety without weakening accurate critique. Add appropriate verification and safety boundaries for regulated, hazardous, medical, legal, financial, or other high-stakes domains.

## Validation

Run the package validator after every create, refine, or migrate operation. Fix errors before delivery and report warnings that require judgment.

For prompt-only work, apply the coach quality rubric silently. For reviews, report the rubric findings instead of rewriting unless the user asks for changes.

After creating and validating a package, give the run prompt with the real package root. The learner runs the coach manually (Dashi copies this prompt):

```text
Run the portable coach package at `<package-root>`. Read and follow `runner.md`. Treat `state.md` as the canonical cross-agent state.
```

## Output contract

Match the result to the operation:

- **Create with an authorized destination:** Write and validate the package, summarize the files, validation, behavior, and unresolved warnings, then give the run prompt.
- **Refine or migrate with an authorized destination:** Write and validate the package, then summarize the files, validation, preserved behavior, and unresolved warnings.
- **Review:** Return prioritized, evidence-backed findings. Do not modify files.
- **Prompt only:** Return only the completed coach prompt, without a preface, design notes, a Markdown fence, placeholders, or TODOs.
- **Run:** Report the session outcome and whether canonical state was written or handed off.

Never claim behavior preservation unless the prompt and state provenance have been verified.
