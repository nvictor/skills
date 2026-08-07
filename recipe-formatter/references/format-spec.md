# Recipe format specification

## Core output

Return plain Markdown-compatible text with no code fence and no introductory or closing prose:

```text
recipe title - optional alias

ingredients

ingredient group:
- ingredient - amount
- alternative | alternative

method

method phase:
- action
- target: desired intermediate result

target result:
- expected final quality
```

Use only the sections the recipe needs. Never emit placeholder groups.

## Lowercase style

- Write the title, headings, group names, ingredients, method text, units, and targets in lowercase.
- Lowercase proper names and acronyms when doing so does not destroy a required symbol or identifier.
- Preserve mathematical symbols, Unicode fractions, and degree symbols.
- Write paired temperatures as `180°C | 350°F`, keeping `C` and `F` uppercase.
- Do not end titles, headings, bullets, or targets with a period.

## Title

- Put the recipe title on the first line.
- Separate genuine names or translations with ` - `.
- Preserve culturally meaningful aliases supplied by the user.
- Do not manufacture translations or alternate names.

Example:

```text
egusi stew - melon seed stew - sauce de graines de courge
```

## Top-level structure

- Put `ingredients` on its own line after the title.
- Put `method` on its own line after all ingredient groups.
- Separate the title, top-level headings, and groups with one blank line.
- Do not use Markdown heading markers, bold text, tables, checkboxes, or numbered steps.
- Use a short lowercase label followed by a colon for every ingredient group and method phase.
- Use `- ` for every ingredient, action, and target bullet.

## Ingredient groups

- Group ingredients by culinary function or reusable component, not alphabetically.
- Prefer specific labels such as `proteins:`, `main seasoning:`, `pepper blend:`, `stew base:`, `assembling:`, or `garnish:`.
- Order groups by dependency and approximate use: advance preparations and components first, assembly components later, garnish or finish last.
- Name a component consistently across ingredients and method. For example, define `pepper blend:` once and refer to `pepper blend` later.
- Represent a previously defined component as a bare ingredient entry when it is incorporated into another group.
- Keep meaningful distinctions such as main seasoning versus extra seasoning.
- Omit an amount when none was supplied. Do not add `to taste` unless the source says it.

### Ingredient line syntax

Use these patterns:

```text
- ingredient
- ingredient - amount
- ingredient - amount, preparation note
- option | option | option
- [classification] ingredient - amount
```

- Use ` - ` between an ingredient and its amount.
- Use ` | ` for interchangeable ingredient choices.
- Use `or` inside prose or when the source describes a broader choice rather than a compact options list.
- Put preparation words with the ingredient when useful: `diced onions`, `ginger paste`, `chopped baby spinach`.
- Put a short remaining note after the amount with a comma: `yam - 4 cups, cubed`.
- Keep alternatives on one bullet when they serve the same role.

## Classifications

Classification tags are Victor's search labels. Put a supplied or high-confidence canonical tag immediately before the ingredient. Preserve existing tags.

Use these established mappings when applicable:

- `[allium]`: onion, garlic, shallot, scallion, leek
- `[capsicum]`: bell pepper, habanero, scotch bonnet, and other chile peppers
- `[zingiberaceae]`: ginger
- `[apiaceae]`: carrot or celery
- `[piperaceae]`: black pepper or white pepper
- `[solanum]`: tomato ingredients
- `[monosodium glutamate]`: msg

Do not invent a new classification scheme or force tags onto every plant ingredient. When uncertain, leave the ingredient untagged.

## Quantities and units

- Preserve quantities unless the user explicitly changes them.
- Prefer Unicode fractions: `½`, `⅓`, `¼`, `⅔`, `¾`, `⅛`.
- Use concise units such as `tsp`, `tbsp`, `cup`, `cups`, `lb`, `g`, `kg`, `ml`, `l`, `min`, and `hr`.
- Use an en dash without surrounding spaces for numeric ranges: `10–15 min`, `4–6 hr`, `¼–½ cup`.
- Use ` | ` for paired temperatures, with Celsius first: `180°C | 350°F`.
- Do not calculate conversions unless asked. Preserve both units when both are supplied.

## Method phases

- Divide the procedure into named culinary phases, not arbitrary step counts.
- Match phase names to ingredient components when possible.
- Order phases by execution and dependency.
- Begin every action bullet with a direct verb: `add`, `blend`, `cook`, `fold`, `heat`, `rest`, `sear`, `simmer`, `stir`, or similar.
- Keep one meaningful action or tightly coupled action sequence per bullet.
- Put conditions before or after the action in natural order: `simmer uncovered over medium-low heat until the sauce thickens`.
- Keep supplied alternatives as separate phases when the cook may choose between them, such as `stovetop:` and `slow cooker:`.
- Include safety-critical details from the source. Do not add generic food-safety advice unless asked.

### Intermediate targets

End a phase with an inline target when texture, appearance, aroma, or reduction determines readiness:

```text
- target: savory browned meat with softened vegetables
```

Do not add a target to every phase mechanically. Add one when supported by the source or when it usefully preserves a doneness cue already implied by the instructions.

## Final target result

- Always end every recipe with `target result:`.
- Add 2–6 bullets describing the expected finished dish.
- Use explicit target language from the source when available.
- When the source omits a target, infer conservative expectations from the dish name, ingredients, preparation, cooking method, timing, and temperature.
- Cover texture, consistency, flavor balance, appearance, and visible components as relevant.
- Prefer observable or sensory qualities over praise such as `delicious` or `perfect`.
- Do not imply an unsupported ingredient, garnish, technique, internal temperature, or culturally specific standard.
- Avoid repeating the method verbatim.

## Updating an existing recipe

1. Treat the pasted recipe as the source of truth except where the user's update overrides it.
2. Apply additions, removals, substitutions, or quantity changes everywhere they matter: ingredient groups, method phases, and targets.
3. Remove stale references to deleted ingredients or methods.
4. Add or rename groups only when the change alters culinary function or dependency.
5. Preserve unaffected details and the recipe's granularity.
6. Update the target result so it reflects every changed ingredient, method, and expected outcome.
7. Add a target result if the existing recipe lacks one.
8. Normalize obvious style drift across the full returned recipe.
9. Return the complete updated recipe by default.

Do not silently reconcile a consequential conflict such as two incompatible cooking temperatures, uncertain raw-versus-cooked protein, or a missing liquid essential to the method. Ask a focused question.

## Final check

Before responding, verify that:

- all output text is lowercase
- the title is first and aliases use ` - `
- `ingredients` precedes grouped ingredient bullets
- `method` precedes phased action bullets
- ingredient amounts use ` - ` and alternatives use ` | `
- component names match between ingredients and method
- every supplied ingredient is used or intentionally presented as an option
- every method ingredient appears in the ingredient list unless it is water, oil, or an explicitly optional adjustment already supported by the source
- removed or replaced items are absent everywhere
- no unsupported amount, timing, temperature, translation, or ingredient was added
- ranges, fractions, units, blank lines, and punctuation are consistent
- the recipe ends with `target result:` followed by 2–6 supported or conservatively inferred sensory bullets
- the response contains only the recipe unless the user asked for commentary
