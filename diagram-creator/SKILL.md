---
name: diagram-creator
description: Create polished, deterministic SVG diagrams from a semantic model plus explicit layout intent. Use this skill when the user wants architecture, workflow, or systems diagrams that look composed rather than auto-laid-out.
---

# Diagram Creator

Use this skill for diagrams whose layout carries meaning. This skill is not a generic graph renderer. It converts a user request into:

1. a semantic model of the system
2. a layout-intent spec
3. a deterministic SVG

## When to use this skill

Use it when the user wants:

- a polished architecture, workflow, platform, or systems diagram
- grouped flows, lanes, panels, or comparison layouts
- deterministic SVG that can be regenerated from a source spec

Do not use it when the user explicitly wants:

- Mermaid
- freeform illustration
- arbitrary themes or exploratory graph layout

## Workflow

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
   - node order inside each lane
   - connection routing hints only where needed
3. Validate the spec with `scripts/render_diagram.py --validate-only`.
4. Render the SVG with `scripts/render_diagram.py --output ...`.

## Output contract

- The model decides both semantics and layout intent.
- The renderer decides geometry only from the declared layout intent.
- The renderer must not infer graph topology, re-group nodes, or reorder flows.
- JSON is the canonical authoring format.

## Renderer

Validate:

```bash
python3 scripts/render_diagram.py examples/ingress-gateway-resources.json --validate-only
```

Render:

```bash
python3 scripts/render_diagram.py examples/ecommerce-checkout-flow.json --output /tmp/ecommerce-checkout-flow.svg
```

## References

- DSL and schema: [references/diagram-dsl.md](references/diagram-dsl.md)
- House style and layout rules: [references/style-system.md](references/style-system.md)
- Reference examples:
  - [examples/ingress-gateway-resources.json](examples/ingress-gateway-resources.json)
  - [examples/ecommerce-checkout-flow.json](examples/ecommerce-checkout-flow.json)
