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
7. Check the output before finalizing it.

## Source handling

Supported sources:

- Confluence pages
- GitHub issues, pull requests, discussions, wikis, READMEs, and docs
- HTML pages or exported HTML files
- Markdown files

Rules:

- Preserve technical accuracy.
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

## Plain language rules

Apply the `clear-language` principles:

- Know the reader and write for their task.
- Put the most important information first.
- Use active voice and direct sentences.
- Use short paragraphs and one idea per sentence.
- Use numbered lists for steps and bullets for facts or options.
- Define technical terms when the reader may not know them.
- Cut filler, buzzwords, marketing language, and unsupported claims.

Prefer these words:

| Instead of | Use |
| --- | --- |
| utilize / leverage | use |
| implement / facilitate | build, add, set up, help |
| initiate / terminate | start / stop |
| subsequently | then, next |
| in order to | to |
| due to the fact that | because |
| functionality | feature, behavior |
| robust / performant | say what it handles or how fast it is |
| scalable / seamless / intuitive | explain the specific behavior |

## Output structure

Use this structure by default. Omit sections that have no useful source-backed
content.

```markdown
# <Clear title>

One-sentence summary of what this is.

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
- Include verification steps.
- Include expected outputs when available.
- Put troubleshooting at the end.

### reference

- Preserve precision.
- Organize by API, config, flags, options, paths, or schemas.
- Minimize narrative text.
- Do not force 30-70% compression if precision would suffer.

### troubleshooting

- Use symptom -> cause -> fix structure.
- Prioritize actionable fixes.
- Include only known issues from the source.

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

- Remove at least 30-70% of source text unless `mode=reference`.
- Collapse low-value detail into bullets.
- Remove repeated points.
- Keep exact names, commands, paths, APIs, defaults, and constraints when they
  matter.

## Final checklist

Run this checklist before finalizing:

- [ ] Reader can understand the topic in under 2 minutes.
- [ ] First paragraph says what the thing is.
- [ ] Every section helps the reader act or decide.
- [ ] No buzzwords, filler, or duplicated points.
- [ ] No unsupported claims.
- [ ] Source links are omitted unless the user asked for sources.
