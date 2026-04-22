# Style System

This skill uses one fixed house style derived from the attached references:

- warm canvas
- white section panels
- soft gray structure
- dark neutral typography
- orange highlight for emphasis
- light blue for action callouts when a highlighted process needs stronger contrast

## Design tokens

### Color

```yaml
color:
  bg:
    canvas: "#F7F4EE"
    panel: "#FFFFFF"
    section: "#FCFBF8"
    callout: "#EAF4FF"
  border:
    subtle: "#DAD4CA"
    panel: "#E6E0D5"
    callout: "#58A6F4"
  text:
    primary: "#1F1F1C"
    secondary: "#6D685F"
  accent:
    primary: "#F27A2B"
    ok: "#76C68B"
    danger: "#F06A63"
  edge:
    default: "#8E877C"
```

### Typography

```yaml
typography:
  font_family: "Inter, ui-sans-serif, system-ui, sans-serif"
  title:
    size: 32
    weight: 700
  subtitle:
    size: 14
    weight: 500
  section_title:
    size: 14
    weight: 700
  section_subtitle:
    size: 12
    weight: 600
  lane_title:
    size: 12
    weight: 600
  node:
    size: 13
    weight: 500
  annotation:
    size: 11
    weight: 500
```

### Layout

```yaml
spacing:
  canvas_padding_x: 42
  canvas_padding_y: 34
  section_gap: 20
  section_padding_x: 24
  section_padding_top: 54
  section_padding_bottom: 26
  lane_gap: 18
  group_gap: 14
  node_gap: 18
```

```yaml
sizing:
  section_min_width: 320
  section_target_max_width: 420
  node_height: 46
  node_min_width: 118
  node_max_width: 190
  user_node_size: 68
  storage_node_size: 68
  cloud_node_size: 68
  security_node_size: 68
  section_radius: 18
  node_radius: 8
```

## Layout rules

- Sections render left-to-right in source order.
- Section layout controls how lanes are placed inside the panel.
- Lane direction controls how groups advance within the lane.
- Lane offsets may nudge a whole lane to create straighter or wider cross-lane edges.
- Sequential groups preserve source order.
- Parallel groups place their member nodes orthogonally in a compact cluster.
- Connections route around nodes and terminate at node boundaries.
- Keep all nodes, node labels, lane labels, and annotations within their owning section panel.
- In dense sections, prefer two-row or two-column arrangements that preserve alignment before widening the section.
- Sections may exceed the target max width when required to keep owned content inside the panel.
- The renderer must never reorder sections, lanes, groups, or nodes.
- Section panels may be hidden with `show_sections: false`, but sections still define grouping and layout.

## Layout choice guide

- `flow`: use for causal or temporal movement.
- `comparison`: use for side-by-side alternatives.
- `stack`: use for layered architecture or responsibility levels.
- `grid`: use for catalogs, capability maps, or repeated entities.

## Visual rules

- Section titles use title case.
- Section subtitles sit directly below section titles.
- Node labels are centered by default.
- `user`, `storage`, `cloud`, and `security` render as canonical badge-style semantic nodes with the label below by default.
- Badge labels may move above the pictogram when the default below-node label would force an avoidable bend or hide an arrowhead.
- `highlight: true` uses orange emphasis, except process nodes may use a blue callout style when they act as the focal instruction block.
- `status` nodes render as compact pills for outcomes such as `Allow` or `Deny`.
- Arrowheads are always visible and terminate outside target shapes.
- Edge labels are forbidden.

## Diagram PARC Pass

- Proximity: nodes in the same semantic group sit closer together than nodes in different groups.
- Alignment: sections, lanes, node centers, labels, and routes follow visible grid logic.
- Repetition: equivalent node types, charts, panels, annotations, and connection styles use the same treatment.
- Contrast: title, section structure, highlights, and normal nodes establish hierarchy within three seconds.

Common failure pattern: weak diagrams often fail through small amounts of disorder in all four areas at once, rather than one obvious mistake.

## Canonical example target

The canonical generated example should look like an intentional product/system diagram, not a generic graph:

- clear panel hierarchy
- aligned flows
- meaningful whitespace
- restrained edge density
- no brand-specific ornament
