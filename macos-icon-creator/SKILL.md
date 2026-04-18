---
name: macos-icon-creator
description: Create macOS-style app icon SVGs from a product brief or concept prompt. Use this skill when the user wants a dock-style icon, app-icon SVG, or Big Sur-inspired macOS icon concept rather than a flat logo in a rounded square.
---

# MacOS Icon Creator

Use this skill to design a single polished macOS app icon with paired JSON brief and SVG artifacts. The goal is not brand extraction. The goal is a native-feeling icon concept with a clear metaphor, readable silhouette, and material depth.

## When to use this skill

Use it when the user wants:

- a macOS app icon
- a dock-style icon
- an SVG app icon concept for a Mac application
- a Big Sur-inspired reinterpretation of an app or product idea

Do not use it when the user explicitly wants:

- a logo system or brand mark
- a favicon
- a generic flat badge
- PNG, ICNS, or export automation
- a broad multi-style illustration pass

## Workflow

1. Normalize the brief:
   - app purpose
   - primary noun or action
   - optional symbols to include or avoid
   - tone, palette hints, and native-vs-brand preference
2. Choose the icon metaphor:
   - one primary metaphor
   - at most one or two supporting motifs
   - one composition family with a strong silhouette
3. Compose for macOS:
   - treat the squircle as part of the composition, not a container
   - use depth, layering, lighting, and material cues where they improve recognition
   - add highlights only when they explain curvature, glass, enamel, or a turned plane
   - let forms merge with, sit on, tuck behind, or selectively break past the squircle when that strengthens the icon
   - keep shapes simple enough to survive at small sizes
4. Produce the deliverable:
   - one JSON brief artifact and one SVG artifact by default
   - one concise rationale covering metaphor, material/depth, palette, and silhouette
5. Self-check before finalizing:
   - readable at 16, 32, 64, and 128 px
   - no centered-logo-in-a-box fallback
   - no text, UI screenshots, or fragile micro-detail

## Output contract

- Default output:
  - brief restatement of the icon direction
  - one JSON brief artifact
  - one SVG artifact
  - short rationale
- Optional output:
  - alternates only when the user asks or when the first concept is clearly ambiguous
  - a compact structured concept plan only when it helps refinement

## Constraints

- Prefer simple readable geometry over intricate decoration.
- Use shadows, gradients, highlights, and layering with restraint and purpose.
- Do not add a highlight by default; only use it when it clarifies form or material.
- Design the object and squircle together; do not default to a safely contained centered object.
- Let the metaphor interact with the icon boundary when that improves energy or recognizability.
- Allow controlled breakout beyond the squircle when the protruding element remains legible at small sizes.
- Avoid literal UI panels unless they are abstracted into a bold icon form.
- Avoid pasted logos on plain squircles, random gradient noise, tiny details, and text labels.

## References

- Principles and composition rules: [references/macos-icon-principles.md](references/macos-icon-principles.md)
- Response shape: [references/output-shape.md](references/output-shape.md)
- Final review checklist: [references/style-checklist.md](references/style-checklist.md)
- Optional internal plan schema: [schema/icon-brief.schema.json](schema/icon-brief.schema.json)
- Example JSON briefs and SVGs: [examples/](examples)
