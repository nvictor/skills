---
name: succinct-writer
description: Create clear, brief Markdown documents from one or more Confluence, GitHub, HTML, or Markdown sources. Use this skill when source material must be read, compressed, reorganized, and rewritten into a new task-oriented document without inventing facts.
---

# Succinct Writer

Use this skill to write a new Markdown file that explains a topic clearly and
briefly from source documents. The goal is not to clean up the source. The goal
is to help the intended reader understand, act, or decide quickly.

## Workflow

1. Read all source material before writing.
2. Identify the intended reader and their likely goal.
3. Choose the output mode. If the user does not provide one, infer it from the
   source and reader goal.
4. Extract only durable, useful information.
5. Remove history, duplication, status chatter, meeting notes, stale context,
   and internal noise unless the reader needs it.
6. Write a new Markdown file with short sections, plain headings, bullets, and
   examples.
7. Run the final editing pass and checklist before finalizing it.

## Source handling

Supported sources:

- Confluence pages
- GitHub issues, pull requests, discussions, wikis, READMEs, and docs
- HTML pages or exported HTML files
- Markdown files

Rules:

- Preserve technical accuracy.
- For every retained claim, preserve its certainty, conditions, exceptions,
  scope, causality, and time.
- Never invent missing facts.
- Mark important missing facts as `Unknown`.
- Omit unimportant unknowns.
- Do not copy large sections verbatim.
- Do not preserve the source structure unless it helps the reader.
- Include source links or file paths only when the user asks for sources.
- When sources are requested, put them in a `Source notes` section.

Ignore unless explicitly requested:

- meeting notes
- brainstorming
- unresolved debates
- outdated migrations
- abandoned approaches
- conversational text
- reaction comments
- status updates

## Writing rules

- Know the reader and write for their task.
- Lead with the answer, result, or decision the reader needs.
- Use active voice and direct sentences.
- Use short paragraphs and one idea per sentence.
- Use numbered lists for steps and bullets for facts or options.
- Use one term for one concept. Change terms only when the source distinguishes
  between them.
- Make the actor explicit when the reader must know who performs an action.
- Put one primary action in each instruction.
- After important steps, explain how to verify success using source-backed
  expected outputs or observable behavior. Do not invent output, status text,
  or success criteria; mark missing verification details as `Unknown` when
  they matter.
- Prefer direct verbs over noun phrases that hide the action.
- Replace an ambiguous phrasal verb with a precise verb when one exists.
- Rewrite long noun clusters when the relationship between the nouns is
  unclear.
- Use a list when prose hides a sequence, condition, or complex enumeration.
- Define technical terms when the reader may not know them.
- Cut filler, buzzwords, marketing language, and unsupported claims.

Treat sentence length, passive voice, phrasal verbs, and noun clusters as
signals to inspect, not automatic violations. Do not force a shorter or simpler
rewrite when it would reduce precision.

### Before and after

These examples illustrate wording and structure, not facts to reuse.

**Lead with the answer**

- Before: "This section explains the available configuration options. To
  disable retries, you can use the retry setting."
- After: "Set `retries` to `0` to disable retries."

**Remove filler**

- Before: "It is important to note that you will need to have administrator
  access in order to change this setting."
- After: "You need administrator access to change this setting."

**Write one action per instruction**

Before: "Open Settings, select Notifications, and turn off email alerts."

After:

1. Open Settings.
2. Select Notifications.
3. Turn off email alerts.

## Output structure

Use this structure by default. Omit sections that have no useful source-backed
content.

```markdown
# <Clear title>

The answer, result, or decision the reader needs, with enough context to
understand it.

## Why it matters

- 1-3 bullets explaining the reader value.

## How it works

Short explanation in plain language.

## How to use it

Steps, commands, or examples if present in the source.

## Key details

Only the important constraints, defaults, APIs, paths, owners, or decisions.

## Common problems

Known issues and fixes, only if present in the source.

## Source notes

- Source link or file path. Include this section only when the user asks for
  sources.
```

Formatting rules:

- Prefer one page unless the source requires more.
- Prefer one-screen sections.
- Avoid repeating information already stated.
- Use fenced code blocks with language tags.
- Use tables only when they make comparison easier.
- End with no summary unless it adds new value.

## Modes

### summary

- Explain what something is and why it matters.
- Use concise sections.
- Optimize for fast understanding.

### guide

- Put prerequisites first.
- Use numbered actions.
- Put troubleshooting at the end.
- When work remains, end with exactly one concrete next action. Omit the
  closing action when the reader's task is complete.

### reference

- Preserve precision.
- Organize by API, config, flags, options, paths, or schemas.
- Minimize narrative text.

### troubleshooting

- Use symptom -> cause -> fix structure.
- Prioritize actionable fixes.
- Include only known issues from the source.
- When work remains, end with exactly one concrete next action. Omit the
  closing action when the reader's task is complete.

### onboarding

- Explain concepts before actions.
- Assume minimal context.
- Include setup steps when present.
- Give the reader a first success milestone.

### architecture

- Focus on systems, dependencies, data flow, boundaries, and decisions.
- Include diagrams if the source supports them.
- Separate current behavior from proposed or historical behavior.

## Compression goals

- Compress as much as possible without losing information the reader needs to understand, act, or decide correctly.
- Collapse low-value detail into bullets.
- Remove repeated points.
- Keep exact names, commands, paths, APIs, defaults, and constraints when they
  matter.

## Final editing pass

Remove opening announcements, redundant recaps, closing pleasantries, and
tangents. Start with useful content and stop when the reader has what they
need. Preserve meaningful uncertainty, including source qualifiers, unresolved
facts, and conditions that affect understanding, action, or decisions.

## Final checklist

Run this checklist before finalizing:

- [ ] Reader can understand the topic in under 2 minutes.
- [ ] First paragraph leads with the answer, result, or decision the reader needs.
- [ ] Every section helps the reader act or decide.
- [ ] Every retained claim is traceable to a source.
- [ ] Numbers, conditions, exceptions, and scope qualifiers are unchanged.
- [ ] The output preserves the source's level of certainty and causal claims.
- [ ] Each concept has one consistent name.
- [ ] Each instruction has one primary action, with clear order and conditions.
- [ ] Important steps explain how to verify success with source-backed outputs
      or observable behavior, or identify important missing verification details.
- [ ] Guide and troubleshooting modes end with one concrete next action only
      when work remains.
- [ ] Actors and pronoun references are unambiguous.
- [ ] Long sentences and noun clusters do not permit multiple interpretations.
- [ ] Compression keeps the information the reader needs to act correctly.
- [ ] No buzzwords, filler, opening announcements, redundant recaps, closing
      pleasantries, or tangents.
- [ ] No unsupported claims.
- [ ] Source links are omitted unless the user asked for sources.
