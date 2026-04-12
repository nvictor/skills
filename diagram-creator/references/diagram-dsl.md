# Diagram DSL

The source spec has two layers:

- semantic structure: sections, nodes, connections, annotations
- layout intent: section layouts, lanes, groups, and routing hints

The renderer reads both layers and computes only geometry.

## Top-level shape

```json
{
  "diagram": {
    "title": "Ingress vs Gateway API Resources",
    "subtitle": "Comparing two Kubernetes front-door models",
    "sections": [],
    "connections": []
  }
}
```

## Diagram

- `title`: required string
- `subtitle`: optional string
- `sections`: required ordered array
- `connections`: required array
- `show_sections`: optional boolean, defaults to `true`

## Section

```json
{
  "id": "publish_gateway",
  "title": "Publish Gateway",
  "subtitle": "Policy checks before network write",
  "layout": {
    "type": "flow",
    "direction": "vertical"
  },
  "lanes": [],
  "nodes": [],
  "annotations": []
}
```

- `id`: required unique string
- `title`: required string
- `subtitle`: optional string
- `layout.type`: required enum: `flow`, `comparison`, `stack`, `grid`
- `layout.direction`: required enum: `horizontal`, `vertical`
- `lanes`: required ordered array
- `nodes`: required array of node objects owned by this section
- `annotations`: optional array

Sections render left-to-right in the order provided.

## Lane

```json
{
  "id": "checks",
  "title": "Checks",
  "direction": "vertical",
  "x_offset": 18,
  "y_offset": -12,
  "groups": [
    {
      "type": "sequential",
      "nodes": ["verify_identity", "validate_branch", "validate_destination"]
    }
  ]
}
```

- `id`: required unique string within the section
- `title`: optional string
- `direction`: required enum: `horizontal`, `vertical`
- `x_offset`: optional number, nudges the full lane horizontally within its section
- `y_offset`: optional number, nudges the full lane vertically within its section
- `groups`: required ordered array

## Group

```json
{
  "type": "parallel",
  "nodes": ["log_listener", "status_stream"]
}
```

- `type`: required enum: `sequential`, `parallel`
- `nodes`: required ordered array of node ids owned by the section

Sequential groups place nodes along the lane direction. Parallel groups place nodes orthogonally inside the lane as a compact cluster.

## Node

```json
{
  "id": "verify_identity",
  "label": "Verify signing identity",
  "type": "process",
  "highlight": true
}
```

- `id`: required unique string within the diagram
- `label`: required string
- `type`: required enum: `default`, `process`, `model`, `database`, `user`, `storage`, `cloud`, `security`, `status`, `chart`
- `highlight`: optional boolean
- `chart`: required object when `type` is `chart`

Nodes do not declare their lane directly. Lane membership comes from lane groups.

## Chart node

```json
{
  "id": "threshold_chart",
  "label": "Threshold-based alerting",
  "type": "chart",
  "chart": {
    "kind": "line",
    "series": [
      {
        "id": "metric",
        "label": "Metric",
        "points": [20, 65, 40, 78, 52, 83]
      }
    ],
    "reference_lines": [
      {
        "id": "threshold",
        "label": "Threshold",
        "value": 60,
        "style": "dashed"
      }
    ],
    "caption": "Repeated crossings produce alert noise."
  }
}
```

- `chart.kind`: required enum: `line`, `area`, `bar`, `pie`
- `chart.series`: required non-empty ordered array
- `chart.series[].id`: required unique string within the chart
- `chart.series[].label`: required string
- `chart.series[].points`: required non-empty numeric array
- `chart.series[].color`: optional string
- `chart.reference_lines`: optional ordered array
- `chart.reference_lines[].id`: required unique string within the chart
- `chart.reference_lines[].label`: optional string
- `chart.reference_lines[].value`: required number when `points` is omitted
- `chart.reference_lines[].points`: required numeric array when `value` is omitted
- `chart.reference_lines[].color`: optional string
- `chart.reference_lines[].style`: optional enum: `solid`, `dashed`; defaults to `dashed`
- `chart.y_range`: optional object with numeric `min` and `max`
- `chart.caption`: optional string

V1 rules:

- all chart series must have the same point count
- point-based reference lines must match the series point count
- each reference line must provide exactly one of `value` or `points`
- pie charts use one value per series, where each series label becomes a slice label
- pie charts do not support `reference_lines` or `y_range` in v1

## Connection

```json
{
  "from": "signed_commit",
  "to": "verify_identity",
  "route": "direct"
}
```

- `from`: required node id
- `to`: required node id
- `route`: optional enum: `direct`, `elbow`, `vertical`

Edge labels are not supported.

## Annotation

```json
{
  "text": "Push proceeds only after every policy gate passes.",
  "position": "footer"
}
```

- `text`: required string
- `position`: optional enum: `header`, `footer`

## Validation rules

- every section id must be unique
- every lane id must be unique inside its section
- every node id must be unique diagram-wide
- every node must be referenced by exactly one lane group in its owning section
- group node references must exist in the section node set
- lane offsets must be numeric when provided
- connections must reference existing nodes
- routes must be one of the supported enums
- labels and annotation text must be non-empty after trimming
- chart nodes must define a valid `chart` object
- chart series must have equal lengths
- chart `y_range.min` must be less than `chart.y_range.max`

## Reference examples

- [examples/ingress-gateway-resources.json](../examples/ingress-gateway-resources.json)
- [examples/ecommerce-checkout-flow.json](../examples/ecommerce-checkout-flow.json)
- [examples/threshold-vs-slo-chart-alerting.json](../examples/threshold-vs-slo-chart-alerting.json)
