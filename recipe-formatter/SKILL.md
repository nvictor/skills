---
name: recipe-formatter
description: Format pasted recipes in Victor's lowercase house style and revise recipes that already use that style. Use when converting loose notes, copied recipes, transcripts, or existing recipe drafts into a consistent title, grouped ingredients, phased method, and expected target result; also use when adding, removing, or changing ingredients, quantities, steps, variants, or wording in an already formatted recipe.
---

# Recipe Formatter

Format recipes as clean, lowercase plain text while preserving the cook's intent.

## Workflow

1. Read [references/format-spec.md](references/format-spec.md) before formatting or revising a recipe.
2. Determine whether the input is a new recipe, an update to an existing formatted recipe, or a merge of recipe fragments.
3. Extract only supported facts: names, aliases, ingredients, amounts, components, actions, timings, temperatures, options, and desired results.
4. Resolve obvious duplicate wording and apply the latest explicit user instruction when an update conflicts with the pasted draft.
5. Organize ingredients into functional groups and organize the method into phases that match how the dish is cooked.
6. Normalize the entire recipe to the house style, not just the changed lines.
7. Always finish the recipe with an expected `target result:` inferred conservatively from the supplied dish, ingredients, and method.
8. Return the complete formatted recipe unless the user explicitly requests an excerpt, diff, or explanation.
9. Run the final check in the format specification before responding.

## Editing Boundaries

- Preserve culinary meaning, cultural names, alternatives, and useful aliases.
- Do not invent quantities, timings, temperatures, equipment settings, or ingredients.
- Infer expected sensory results when necessary, but do not imply an ingredient, technique, garnish, or doneness standard that the recipe does not support.
- Infer sequence only when it follows directly from the supplied procedure or dependencies between named components.
- Correct clear spelling, grammar, duplication, and unit-formatting errors without commentary.
- Ask one focused question only when an unresolved ambiguity would materially change the dish. Otherwise, omit unsupported detail.
- Keep warnings or uncertainty outside the recipe only when the user needs to make a decision.

## Reference Examples

Read [references/canonical-examples.md](references/canonical-examples.md) when the input contains nested components, alternative cooking methods, multilingual title aliases, or an existing recipe whose structure is unclear. Treat the format specification as authoritative when an example contains a minor inconsistency.
