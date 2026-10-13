# Coach quality rubric

Read this file completely when creating, reviewing, or refining a coach. During a preservation migration, use it to produce warnings only; do not rewrite behavior.

## Long-term transformation

- State an observable capability the learner should demonstrate after sustained practice.
- Tie competencies, session activities, feedback, and progression to that capability.
- Prefer demonstrated performance over content coverage, attendance, or confidence alone.

## Active learning

- Choose guided learning for unfamiliar material, unknown familiarity, missing prerequisites, conceptual gaps, or an explicit explanation request.
- Use practice-first for evidence-supported previously learned material or an explicit practice request. Teach missing prerequisites without treating basic instruction as an exercise solution.
- Keep factual input gathering separate from understanding checks.
- Use realistic practice, simulations, projects, debugging, decisions, retrieval, or teaching back.
- Keep instruction short and immediately useful.
- Apply teaching feedback through a focused check; apply practice feedback through a retry, revision, transfer task, or concise reflection within the remaining budget.

## Session design

- Keep sessions within their requested duration and choose one useful objective from evidence.
- Explain and assess progressively, checking understanding before advancing to dependent material.
- Use questions, applications, teach-backs, or observed work to assess understanding naturally.
- Adapt to confusion, learner requests, and demonstrated performance without a fixed conversational script.
- Do not require a separate readiness confirmation after a successful assessment.
- Give focused feedback and opportunities to apply it within the remaining session budget.
- Pause incomplete work at session limits and preserve its position for resumption.

## Feedback

- Cite specific evidence from the learner's attempt.
- Distinguish consequential gaps from optional polish.
- Explain why the important gap matters.
- Give an actionable next move and a chance to use it within the remaining budget; otherwise preserve it for resumption.
- Recognize strong work precisely without generic or undeserved praise.
- Evaluate submitted work and stated rationale without demanding hidden chain-of-thought.

## Progression

- Establish a baseline or use existing evidence.
- Increase difficulty only after demonstrated readiness.
- Change one meaningful difficulty dimension at a time unless several changes serve a clear purpose.
- Define mastery, remediation, and spaced review.
- Revisit weak skills with new surface details rather than repeating scripts.
- Include enough purposeful variation to remain useful after at least 50 sessions.

## Continuity

- Treat state as a compact current snapshot, never an append-only diary.
- Track observable work, strengths, gaps, feedback, difficulty, recent practice, and next targets.
- Preserve the current objective, interaction position, outstanding work, observed evidence, and remaining session budget in an open interaction.
- Resume the recorded phase without automatically reteaching. Preserve unknowns in legacy state; do not invent understanding or consent.
- Never invent learner history, preferences, results, or mastery.
- Keep incomplete interactions distinct from completed sessions.
- Treat package state as canonical and update it after every coaching turn.
- Reread state before writing so switching or concurrent agents do not overwrite newer evidence.
- Retain at most ten completed-session entries, newest first, and preserve those recent entries verbatim.
- Compact older durable evidence into one line per strength or gap with an observation count and at most three recent dated examples.
- Replace stale or superseded statements instead of appending another event.
- Produce a complete replacement-state handoff when durable storage is unavailable.

## Safety and respect

- Preserve psychological safety without softening accurate critique.
- Add verification and boundaries for regulated or hazardous domains.
- Respect relationship, privacy, consent, and autonomy constraints relevant to the domain.
- Avoid collecting or retaining personal details that do not improve coaching.

## Portability

- Keep the behavioral prompt independent of AI provider and scheduler.
- Keep schedules, timezones, and source status in the manifest.
- Keep model names, project IDs, notifications, machine paths, and scheduler expressions outside the canonical package.
- Make the prompt usable alone while allowing state to improve continuity.
- Provide a provider-neutral runner that makes state behavior explicit.
- Make the package understandable without proprietary tooling.

## Portfolio fit

- Check whether the coach duplicates or conflicts with another coach when an inventory is available.
- Give overlapping coaches distinct transformations and assessment criteria, or recommend consolidation.
- Separate a coach's subject area from its actual learning objective.

## Final review

Confirm that:

- the coach would still be valuable after 50 sessions
- the long-term transformation is observable
- the sequence fits learner familiarity and requests, with active understanding checks and deliberate practice
- difficulty follows evidence
- feedback leads to a focused check or practice application within the remaining budget
- continuity works without invented memory
- every session remains bounded, with incomplete work paused at its exact phase
- assessment precedes dependent material without unnecessary readiness gates
- instructions are clear, nonredundant, compatible, and executable
- another capable agent could run the coach from the package
