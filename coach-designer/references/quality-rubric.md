# Coach quality rubric

Read this file completely when creating, reviewing, or refining a coach. During a preservation migration, use it to produce warnings only; do not rewrite behavior.

## Long-term transformation

- State an observable capability the learner should demonstrate after sustained practice.
- Tie competencies, session activities, feedback, and progression to that capability.
- Prefer demonstrated performance over content coverage, attendance, or confidence alone.

## Active learning

- Give the learner a meaningful attempt before a full explanation whenever the domain permits it.
- Use realistic practice, simulations, projects, debugging, decisions, retrieval, or teaching back.
- Keep instruction short and immediately useful.
- Require feedback application through a retry, revision, transfer task, or concise reflection.

## Session design

- Keep each session bounded by the requested duration.
- Select one useful objective from evidence rather than random novelty.
- State clear constraints and a definition of done when useful.
- Finish with feedback, application, and a clear next target.
- Avoid unnecessary discovery questions and curriculum dumps.

## Feedback

- Cite specific evidence from the learner's attempt.
- Distinguish consequential gaps from optional polish.
- Explain why the important gap matters.
- Give an actionable next move and an immediate chance to use it.
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

- Track only observable work, strengths, gaps, feedback, difficulty, recent practice, and next targets.
- Never invent learner history, preferences, results, or mastery.
- Keep incomplete interactions distinct from completed sessions.
- Treat package state as canonical and update it after every coaching turn.
- Reread state before writing so switching or concurrent agents do not overwrite newer evidence.
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
- practice outweighs explanation
- difficulty follows evidence
- feedback leads to immediate application
- continuity works without invented memory
- every session remains bounded
- instructions are clear, nonredundant, compatible, and executable
- another capable agent could run the coach from the package
