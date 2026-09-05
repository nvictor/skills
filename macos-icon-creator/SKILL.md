---
name: macos-icon-creator
description: Create or refine macOS-style app icon SVGs from an app brief or existing artwork. Use for dock-style icons and Big Sur-inspired icon concepts, rather than logo systems or general illustration.
---

# macOS Icon Creator

Design a native-feeling icon with a clear metaphor, readable silhouette, and purposeful material depth. This skill targets the dimensional Big Sur-inspired style; it is not a specification for every macOS icon style.

## Workflow

1. Establish the app purpose, primary metaphor, and any requested symbols, palette, or tone. Infer a reasonable direction from the available brief; ask only when missing information would materially change it. For revisions, inspect the existing artwork and preserve approved choices outside the requested change.
2. Read [design principles](references/macos-icon-principles.md) when choosing or revising the composition. Resolve the dominant form before adding supporting detail. Examples in [examples/](examples/) illustrate possible solutions, not templates or mandatory treatments.
3. Build or edit a self-contained SVG with an explicit `viewBox` and enough canvas margin for intended protrusions and shadows. Keep essential geometry editable and avoid external fonts, images, or other dependencies.
4. Render and inspect the actual pixels using the [raster review checklist](references/style-checklist.md). Fix visual defects and repeat the affected checks. If rendering is unavailable, state that limitation instead of claiming visual validation.
5. Deliver using [output guidance](references/output-shape.md). Default to a paired SVG and concise JSON brief for a new concept; respect narrower requests and update an existing brief when the design changes.

The core deliverable is SVG. Requested raster or app-icon exports may extend the task, but export and application installation are separate operations. Validate the rendering path used for those exports and modify an app repository only when the user requests it.
