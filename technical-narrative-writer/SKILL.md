---
name: technical-narrative-writer
description: Turn technical systems work into concise career narratives for interview answers, resumes, promotion packets, project summaries, performance reviews, and skill-positioning blurbs. Use when the user wants a short paragraph or two that explains technical work through operational problem, system boundary, control model, automation, governance, outcome, and engineering leverage.
---

# Technical Narrative Writer

## Purpose

Use this skill to turn technical systems into short, career-ready narratives. The default output is one paragraph. Use two paragraphs only when the material has enough scope that combining it would make the result dense or hard to read. Do not produce long writeups, visible worksheets, or section-by-section analysis unless the user explicitly asks for them.

The goal is to show systems thinking instead of listing tools: how technical work turned a risky, unclear, manual, or expensive operating space into a repeatable system that teams could use, trust, govern, and maintain.

## Writing Pattern

Write in plain prose. Move through these ideas without turning them into headings:

- Operational problem: what was unreliable, manual, risky, unclear, expensive, or hard to govern.
- System boundary: the teams, repositories, platforms, environments, services, or workflows involved.
- Control model: the standard, interface, ownership model, or operating expectation that made the system repeatable.
- Automation or platform mechanism: the workflow, code, integration, alert, dashboard, pipeline, or platform behavior that made the path repeatable.
- Governance and safety: how the work reduced risk or improved readiness.
- Operational outcome: what changed for teams, systems, users, or business workflows.
- Engineering leverage: why the work mattered beyond the implementation.

Start with the problem and boundary so the reader understands the scale. Then describe the control model and repeatable mechanism. Close with risk reduction, operational outcome, and engineering impact.

## Output Rules

- Prefer one paragraph of 2-5 sentences.
- Use two shorter paragraphs only when it improves readability.
- Keep claims source-backed. Do not invent metrics, scope, ownership, or business impact.
- Use exact names for systems, repositories, tools, and platforms when available.
- Separate completed work from active or ongoing work.
- Prefer outcomes over implementation trivia.
- Use active verbs such as led, defined, built, migrated, automated, standardized, supported, and anchored.
- Avoid unsupported claims like scalable, seamless, robust, or transformative unless the specific behavior is described.

## Optional Formats

Only use these compact variants when the user asks for them.

Resume bullet:

```text
Identified <problem> across <system boundary>, defined <control model>, and built <automation or platform mechanism> with <governance or safety control>, improving <operational outcome> for <teams/users/business workflow>.
```

Positioning sentence:

```text
I build repeatable reliability and platform systems that connect business-critical journeys, infrastructure automation, governance, and team ownership across complex payment and cloud environments.
```

## Template

Use this as an internal drafting shape, not as a visible worksheet:

```text
<System Name> turned <operational problem> across <system boundary> into a repeatable operating model. The work defined <control model> so teams had a consistent way to understand, own, and operate the system. The repeatable mechanism was <automation or platform mechanism>, which reduced <manual work, inconsistent behavior, operational ambiguity, or risk> and made <workflow, infrastructure path, reliability signal, deployment process, or remediation path> easier to use and maintain. The system reduced risk through <governance and safety controls>, improving <observable or measurable outcome> and creating <team alignment, ownership handoff, reusable standards, better decisions, or business impact>.
```
