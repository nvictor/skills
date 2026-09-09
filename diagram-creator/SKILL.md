---
name: diagram-creator
description: Create polished, deterministic SVG diagrams from a semantic model plus explicit layout intent. Use this skill when the user wants architecture, workflow, or systems diagrams that look composed rather than auto-laid-out.
---

# Diagram Creator

Use this skill for diagrams whose layout carries meaning. This skill is not a generic graph renderer. It converts a user request into:

1. a semantic model of the system
2. a layout-intent spec
3. a deterministic SVG

## No-crossing rule

Edges must not cross node interiors, labels, or annotations, including the source and target labels. Edges must not cross, touch, or overlap other edges except at an intentional shared node port. Shared ports do not permit shared line segments. They may touch their endpoint boundaries only at connection ports. Check the entire visible edge, including short terminal segments, bends, stroke width, and arrowheads.

Treat crossings as a failed diagram, not a cosmetic issue. Inspect the rendered SVG visually; renderer validation alone does not prove collision-free output. If a crossing appears, adjust the JSON layout intent and regenerate. Preserve the connections and meaning, and keep unobstructed aligned flows straight. Do not hide crossings behind nodes, manually patch the SVG, or change the renderer to make an individual diagram pass. If a valid layout cannot be produced, report the blocking connection instead of presenting the diagram as finished.

## Decision rule

Ask once: what layout makes the system relationship easiest to understand?

## When to use this skill

Use it when the user wants:

- a polished architecture, workflow, platform, or systems diagram
- grouped flows, lanes, panels, or comparison layouts
- compact embedded charts for comparisons or key metrics inside a diagram
- deterministic SVG that can be regenerated from a source spec

Do not use it when the user explicitly wants:

- Mermaid
- freeform illustration
- arbitrary themes or exploratory graph layout

## Workflow

Use this state sequence: semantic model -> layout intent -> JSON spec -> renderer validation -> PARC review -> SVG/final.

1. Extract the semantic model:
   - title, subtitle
   - sections
   - nodes
   - connections
   - annotations
2. Add layout intent:
   - section order
   - section layout type
   - section direction
   - lane order
   - lane offsets when a cross-lane edge needs more width or cleaner alignment
   - badge label position when the default label placement would block a straight edge
   - color scheme when the default `warm-neutral` palette is not the right fit
   - node order inside each lane
   - connection routing hints only where needed
3. Write the JSON spec to a file.
4. Validate the spec with `python3 scripts/render_diagram.py <spec.json> --validate-only`.
5. Render the SVG with `python3 scripts/render_diagram.py <spec.json> --output <diagram.svg>`.
6. Run a PARC verification:
   - Proximity: related nodes, labels, lanes, and annotations are visibly grouped; unrelated groups are separated.
   - Alignment: sections, lanes, node centers, labels, and routes follow a visible grid.
   - Repetition: repeated node roles, charts, panels, annotations, and connection styles use consistent treatment.
   - Contrast: title, sections, highlighted nodes, and normal nodes form a clear hierarchy within three seconds.
7. Visually inspect the final SVG and run a geometry sanity pass:
   - Trace every edge from source to target. No part crosses a node, label, or annotation. Compare every pair of edges for crossings, touching, or overlapping segments; only intentional shared node ports may meet.
   - Every edge has a visible arrowhead at the target.
   - Straight semantic edges stay straight when node centers align.
   - Single-path diagrams should keep node centers on one visible axis and avoid adding secondary lanes unless the separation carries meaning.
   - Adjacent sections with corresponding roles should align equivalent node rows or columns before adding staggered lanes or extra width.
   - Badge labels sit above or below the pictogram according to whichever side leaves the intended edge path clear.
   - Nodes, labels, annotations, and edge routes stay inside their owning section unless the connection intentionally crosses to another section.
   - Dense sections use the full panel efficiently before increasing section width.

## Output contract

Authoring contract:

- The model decides both semantics and layout intent.
- JSON is the canonical authoring format.

Renderer contract:

- The renderer decides geometry only from the declared layout intent.
- The renderer must not infer graph topology, re-group nodes, or reorder flows.

Final response contract:

- Return or reference the JSON spec and deterministic SVG according to the user's requested delivery format.
- Include a compact validation note covering renderer validation, visual collision inspection, and PARC review. Only claim checks that were performed.
- If a PARC issue shaped the layout, mention it briefly.

## Renderer

Operational notes:

- `scripts/render_diagram.py` requires one positional argument: the input JSON spec path.
- Run commands from this skill directory, or use absolute paths for both the script and the spec.
- The renderer uses only the Python standard library. Do not stop to install `cairosvg`, `lxml`, or other SVG packages for this skill.
- `--validate-only` prints `OK` on success and exits without producing SVG output.
- Specs may set `diagram.color_scheme`; supported schemes are `warm-neutral`, `studio-paper`, `ink-signal`, `console-light`, and `graphite-citrus`.
- Common failure pattern: weak diagrams often fail through accumulated mild disorder across grouping, almost-aligned elements, drifting styles, and weak hierarchy.

Validate:

```bash
python3 scripts/render_diagram.py examples/ingress-gateway-resources.json --validate-only
```

Render:

```bash
python3 scripts/render_diagram.py examples/ecommerce-checkout-flow.json --output /tmp/ecommerce-checkout-flow.svg
```

## Renderer regression tests

When maintaining the renderer, run:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The collision tests in [scripts/test_render_diagram.py](scripts/test_render_diagram.py) exercise the existing renderer and report violations. They do not replace visual inspection of the final SVG or authorize renderer changes during diagram creation.

## References

- DSL and schema: [references/diagram-dsl.md](references/diagram-dsl.md)
- House style and layout rules: [references/style-system.md](references/style-system.md)
- Reference examples: [examples/](examples)
