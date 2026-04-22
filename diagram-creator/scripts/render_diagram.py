#!/usr/bin/env python3
"""Render layout-intent diagram specs into deterministic SVG."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


TOKENS = {
    "canvas": "#F7F4EE",
    "panel": "#FFFFFF",
    "section": "#FCFBF8",
    "callout": "#EAF4FF",
    "border": "#DAD4CA",
    "panel_border": "#E6E0D5",
    "callout_border": "#58A6F4",
    "text": "#1F1F1C",
    "muted_text": "#6D685F",
    "accent": "#F27A2B",
    "ok": "#76C68B",
    "danger": "#F06A63",
    "edge": "#8E877C",
}

FONT_STACK = "Inter, ui-sans-serif, system-ui, sans-serif"
CANVAS_PAD_X = 42
CANVAS_PAD_Y = 34
SECTION_GAP = 20
SECTION_PAD_X = 24
SECTION_PAD_TOP = 54
SECTION_PAD_BOTTOM = 26
TITLE_BLOCK_H = 92
LANE_GAP = 18
GROUP_GAP = 14
NODE_GAP = 18
NODE_HEIGHT = 46
NODE_MIN_WIDTH = 118
NODE_MAX_WIDTH = 190
USER_NODE_SIZE = 68
STORAGE_NODE_SIZE = 68
CLOUD_NODE_SIZE = 68
SECURITY_NODE_SIZE = 68
BADGE_LABEL_BASELINE_OFFSET = 18
BADGE_LABEL_TOP_BASELINE_OFFSET = -12
BADGE_LABEL_FONT_SIZE = 12
STATUS_MIN_WIDTH = 92
STATUS_MAX_WIDTH = 180
STATUS_HEIGHT = 42
SECTION_RADIUS = 18
NODE_RADIUS = 8
CHART_WIDTH = 244
CHART_HEIGHT = 220
PIE_CHART_HEIGHT = 280
CHART_RADIUS = 12
CHART_CAPTION_TOP_GAP = 20.0
CHART_CAPTION_BOTTOM_GAP = 14.0
SECTION_MIN_WIDTH = 320
SECTION_MAX_WIDTH = 420
EDGE_CLEARANCE = 12.0
EDGE_STUB = 18.0
GRID_MARGIN = 16.0
TURN_PENALTY = 32.0
PORT_PREFERENCE_PENALTY = 4.0

VALID_SECTION_LAYOUTS = {"flow", "comparison", "stack", "grid"}
VALID_DIRECTIONS = {"horizontal", "vertical"}
VALID_GROUP_TYPES = {"sequential", "parallel"}
VALID_NODE_TYPES = {
    "default",
    "process",
    "model",
    "database",
    "user",
    "storage",
    "cloud",
    "security",
    "status",
    "chart",
}
VALID_ROUTES = {"direct", "elbow", "vertical"}
VALID_CHART_KINDS = {"line", "area", "bar", "pie"}
VALID_REFERENCE_LINE_STYLES = {"solid", "dashed"}
VALID_BADGE_LABEL_POSITIONS = {"top", "bottom"}
CHART_SERIES_COLORS = ["#F27A2B", "#58A6F4", "#76C68B", "#C98BFF"]
CHART_REFERENCE_COLORS = ["#6D685F", "#F06A63", "#58A6F4"]
BADGE_NODE_SIZES = {
    "user": USER_NODE_SIZE,
    "storage": STORAGE_NODE_SIZE,
    "cloud": CLOUD_NODE_SIZE,
    "security": SECURITY_NODE_SIZE,
}
BADGE_NODE_TYPES = set(BADGE_NODE_SIZES)


class DiagramError(ValueError):
    pass


@dataclass(frozen=True)
class Rect:
    left: float
    top: float
    right: float
    bottom: float

    def inflate(self, amount: float) -> "Rect":
        return Rect(
            self.left - amount,
            self.top - amount,
            self.right + amount,
            self.bottom + amount,
        )

    def contains(self, other: "Rect", tolerance: float = 0.01) -> bool:
        return (
            other.left >= self.left - tolerance
            and other.top >= self.top - tolerance
            and other.right <= self.right + tolerance
            and other.bottom <= self.bottom + tolerance
        )


@dataclass
class NodeLayout:
    node_id: str
    label: str
    node_type: str
    highlight: bool
    chart: dict[str, Any] | None
    label_position: str
    x: float
    y: float
    width: float
    height: float
    section_id: str
    lane_id: str

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def rect(self) -> Rect:
        return Rect(self.left, self.top, self.right, self.bottom)


@dataclass
class SectionLayout:
    section_id: str
    title: str
    subtitle: str | None
    x: float
    y: float
    width: float
    height: float
    footer_annotations: list[str]


def estimate_text_width(text: str, font_size: float) -> float:
    return max(0.0, len(text) * font_size * 0.56)


def centered_text_rect(
    center_x: float,
    baseline_y: float,
    text: str,
    font_size: float,
    padding_x: float = 8.0,
    padding_y: float = 4.0,
) -> Rect:
    text_width = estimate_text_width(text, font_size)
    ascent = font_size * 0.82
    descent = font_size * 0.24
    return Rect(
        center_x - text_width / 2 - padding_x,
        baseline_y - ascent - padding_y,
        center_x + text_width / 2 + padding_x,
        baseline_y + descent + padding_y,
    )


def load_spec(path: Path) -> dict[str, Any]:
    raw = path.read_text()
    if path.suffix.lower() != ".json":
        raise DiagramError("JSON is the canonical input format for the rewritten skill.")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise DiagramError("Top-level input must be an object.")
    return data


def require_non_empty_string(obj: dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DiagramError(f"'{key}' must be a non-empty string.")
    return value.strip()


def require_list(obj: dict[str, Any], key: str) -> list[Any]:
    value = obj.get(key)
    if not isinstance(value, list):
        raise DiagramError(f"'{key}' must be an array.")
    return value


def require_number(obj: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = obj.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DiagramError(f"'{key}' must be a number when provided.")
    return float(value)


def normalize_optional_string(value: Any, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DiagramError(f"{context} must be a non-empty string when provided.")
    return value.strip()


def require_numeric_list(value: Any, context: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise DiagramError(f"{context} must be a non-empty array of numbers.")
    numbers: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise DiagramError(f"{context} must contain only numbers.")
        numbers.append(float(item))
    return numbers


def wrap_label(text: str, width: int = 18) -> list[str]:
    wrapped = textwrap.wrap(text, width=width, break_long_words=False)
    return wrapped[:3] if wrapped else [text]


def wrap_text_to_width(text: str, pixel_width: float, max_lines: int = 3) -> list[str]:
    char_width = max(10, int(pixel_width / 7.2))
    wrapped = textwrap.wrap(text, width=char_width, break_long_words=False)
    return wrapped[:max_lines] if wrapped else [text]


def measure_node(node: dict[str, Any]) -> tuple[int, int]:
    node_type = node["type"]
    label = node["label"]
    if node_type in BADGE_NODE_TYPES:
        size = BADGE_NODE_SIZES[node_type]
        return size, size
    if node_type == "status":
        lines = wrap_label(label, 16 if len(label) > 18 else 18)
        max_chars = max(len(line) for line in lines)
        width = max(STATUS_MIN_WIDTH, min(STATUS_MAX_WIDTH, 28 + max_chars * 7))
        height = STATUS_HEIGHT if len(lines) == 1 else STATUS_HEIGHT + (len(lines) - 1) * 14
        return width, height
    if node_type == "chart":
        if isinstance(node.get("chart"), dict) and node["chart"].get("kind") == "pie":
            return CHART_WIDTH, PIE_CHART_HEIGHT
        return CHART_WIDTH, CHART_HEIGHT
    lines = wrap_label(label, 17 if len(label) > 20 else 18)
    max_chars = max(len(line) for line in lines)
    width = max(NODE_MIN_WIDTH, min(NODE_MAX_WIDTH, 30 + max_chars * 7))
    return width, NODE_HEIGHT


def measure_node_footprint(node: dict[str, Any]) -> tuple[float, float]:
    width, height = measure_node(node)
    if node["type"] not in BADGE_NODE_TYPES:
        return float(width), float(height)

    label_position = node.get("label_position", "bottom")
    label_baseline_y = (
        BADGE_LABEL_TOP_BASELINE_OFFSET
        if label_position == "top"
        else height + BADGE_LABEL_BASELINE_OFFSET
    )
    label_rect = centered_text_rect(
        0.0,
        label_baseline_y,
        node["label"],
        BADGE_LABEL_FONT_SIZE,
        padding_x=8.0,
        padding_y=5.0,
    )
    footprint_width = max(float(width), label_rect.right - label_rect.left)
    footprint_height = max(float(height), label_rect.bottom) - min(0.0, label_rect.top)
    return footprint_width, footprint_height


def node_offset_within_footprint(node: dict[str, Any]) -> tuple[float, float]:
    if node["type"] not in BADGE_NODE_TYPES:
        return 0.0, 0.0
    if node.get("label_position", "bottom") != "top":
        return 0.0, 0.0
    label_rect = centered_text_rect(
        0.0,
        BADGE_LABEL_TOP_BASELINE_OFFSET,
        node["label"],
        BADGE_LABEL_FONT_SIZE,
        padding_x=8.0,
        padding_y=5.0,
    )
    return 0.0, max(0.0, -label_rect.top)


def validate_chart(node_id: str, chart_obj: Any) -> dict[str, Any]:
    if not isinstance(chart_obj, dict):
        raise DiagramError(f"Chart node '{node_id}' must define a 'chart' object.")
    kind = require_non_empty_string(chart_obj, "kind")
    if kind not in VALID_CHART_KINDS:
        raise DiagramError(f"Chart node '{node_id}' has invalid chart kind '{kind}'.")

    series_list = require_list(chart_obj, "series")
    normalized_series: list[dict[str, Any]] = []
    expected_length: int | None = None
    seen_series_ids: set[str] = set()
    for index, series in enumerate(series_list):
        if not isinstance(series, dict):
            raise DiagramError(f"Chart node '{node_id}' series entries must be objects.")
        series_id = require_non_empty_string(series, "id")
        if series_id in seen_series_ids:
            raise DiagramError(f"Chart node '{node_id}' has duplicate series id '{series_id}'.")
        seen_series_ids.add(series_id)
        points = require_numeric_list(series.get("points"), f"Chart node '{node_id}' series '{series_id}' points")
        if expected_length is None:
            expected_length = len(points)
        elif len(points) != expected_length:
            raise DiagramError(f"Chart node '{node_id}' series must all have the same number of points.")
        normalized_series.append(
            {
                "id": series_id,
                "label": require_non_empty_string(series, "label"),
                "points": points,
                "color": normalize_optional_string(
                    series.get("color"), f"Chart node '{node_id}' series '{series_id}' color"
                ),
                "index": index,
            }
        )

    reference_lines = chart_obj.get("reference_lines", [])
    if not isinstance(reference_lines, list):
        raise DiagramError(f"Chart node '{node_id}' reference_lines must be an array when provided.")
    normalized_reference_lines: list[dict[str, Any]] = []
    seen_reference_ids: set[str] = set()
    for index, reference_line in enumerate(reference_lines):
        if not isinstance(reference_line, dict):
            raise DiagramError(f"Chart node '{node_id}' reference_lines entries must be objects.")
        ref_id = require_non_empty_string(reference_line, "id")
        if ref_id in seen_reference_ids:
            raise DiagramError(f"Chart node '{node_id}' has duplicate reference line id '{ref_id}'.")
        seen_reference_ids.add(ref_id)
        has_value = "value" in reference_line
        has_points = "points" in reference_line
        if has_value == has_points:
            raise DiagramError(
                f"Chart node '{node_id}' reference line '{ref_id}' must provide exactly one of 'value' or 'points'."
            )
        points: list[float] | None = None
        value: float | None = None
        if has_points:
            points = require_numeric_list(
                reference_line.get("points"),
                f"Chart node '{node_id}' reference line '{ref_id}' points",
            )
            if expected_length is not None and len(points) != expected_length:
                raise DiagramError(
                    f"Chart node '{node_id}' reference line '{ref_id}' points must match the series length."
                )
        else:
            raw_value = reference_line.get("value")
            if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
                raise DiagramError(
                    f"Chart node '{node_id}' reference line '{ref_id}' value must be a number."
                )
            value = float(raw_value)
        style = reference_line.get("style", "dashed")
        if style not in VALID_REFERENCE_LINE_STYLES:
            raise DiagramError(
                f"Chart node '{node_id}' reference line '{ref_id}' has invalid style '{style}'."
            )
        normalized_reference_lines.append(
            {
                "id": ref_id,
                "label": normalize_optional_string(
                    reference_line.get("label"),
                    f"Chart node '{node_id}' reference line '{ref_id}' label",
                ),
                "points": points,
                "value": value,
                "color": normalize_optional_string(
                    reference_line.get("color"), f"Chart node '{node_id}' reference line '{ref_id}' color"
                ),
                "style": style,
                "index": index,
            }
        )

    y_range = chart_obj.get("y_range")
    normalized_y_range: dict[str, float] | None = None
    if y_range is not None:
        if not isinstance(y_range, dict):
            raise DiagramError(f"Chart node '{node_id}' y_range must be an object when provided.")
        y_min = require_number(y_range, "min")
        y_max = require_number(y_range, "max")
        if y_min >= y_max:
            raise DiagramError(f"Chart node '{node_id}' y_range.min must be less than y_range.max.")
        normalized_y_range = {"min": y_min, "max": y_max}

    if kind == "pie":
        if normalized_reference_lines:
            raise DiagramError(f"Chart node '{node_id}' pie charts do not support reference_lines in v1.")
        if normalized_y_range is not None:
            raise DiagramError(f"Chart node '{node_id}' pie charts do not support y_range in v1.")
        for series in normalized_series:
            if len(series["points"]) != 1:
                raise DiagramError(
                    f"Chart node '{node_id}' pie chart series must each contain exactly one value."
                )
            if series["points"][0] < 0:
                raise DiagramError(f"Chart node '{node_id}' pie chart values must be non-negative.")

    return {
        "kind": kind,
        "series": normalized_series,
        "reference_lines": normalized_reference_lines,
        "y_range": normalized_y_range,
        "caption": normalize_optional_string(chart_obj.get("caption"), f"Chart node '{node_id}' caption"),
    }


def validate_spec(data: dict[str, Any]) -> dict[str, Any]:
    diagram = data.get("diagram")
    if not isinstance(diagram, dict):
        raise DiagramError("Missing required top-level 'diagram' object.")

    title = require_non_empty_string(diagram, "title")
    subtitle = diagram.get("subtitle")
    if subtitle is not None and not isinstance(subtitle, str):
        raise DiagramError("'subtitle' must be a string when provided.")
    show_sections = diagram.get("show_sections", True)
    if not isinstance(show_sections, bool):
        raise DiagramError("'show_sections' must be a boolean when provided.")

    sections = require_list(diagram, "sections")
    connections = require_list(diagram, "connections")

    seen_section_ids: set[str] = set()
    seen_node_ids: set[str] = set()
    node_to_section: dict[str, str] = {}
    normalized_sections: list[dict[str, Any]] = []

    for section in sections:
        if not isinstance(section, dict):
            raise DiagramError("Each section must be an object.")
        section_id = require_non_empty_string(section, "id")
        if section_id in seen_section_ids:
            raise DiagramError(f"Duplicate section id: {section_id}")
        seen_section_ids.add(section_id)

        layout = section.get("layout")
        if not isinstance(layout, dict):
            raise DiagramError(f"Section '{section_id}' must define a layout object.")
        layout_type = require_non_empty_string(layout, "type")
        direction = require_non_empty_string(layout, "direction")
        if layout_type not in VALID_SECTION_LAYOUTS:
            raise DiagramError(f"Section '{section_id}' has invalid layout type '{layout_type}'.")
        if direction not in VALID_DIRECTIONS:
            raise DiagramError(f"Section '{section_id}' has invalid layout direction '{direction}'.")

        lanes = require_list(section, "lanes")
        nodes = require_list(section, "nodes")
        annotations = section.get("annotations", [])
        if not isinstance(annotations, list):
            raise DiagramError(f"Section '{section_id}' annotations must be an array.")

        section_node_map: dict[str, dict[str, Any]] = {}
        for node in nodes:
            if not isinstance(node, dict):
                raise DiagramError(f"Section '{section_id}' nodes must be objects.")
            node_id = require_non_empty_string(node, "id")
            if node_id in seen_node_ids:
                raise DiagramError(f"Duplicate node id: {node_id}")
            node_type = require_non_empty_string(node, "type")
            if node_type not in VALID_NODE_TYPES:
                raise DiagramError(f"Node '{node_id}' has invalid type '{node_type}'.")
            label_position = node.get("label_position", "bottom")
            if label_position not in VALID_BADGE_LABEL_POSITIONS:
                raise DiagramError(f"Node '{node_id}' has invalid label_position '{label_position}'.")
            if node_type not in BADGE_NODE_TYPES and "label_position" in node:
                raise DiagramError(
                    f"Node '{node_id}' can only set label_position on badge-style node types."
                )
            seen_node_ids.add(node_id)
            chart = validate_chart(node_id, node.get("chart")) if node_type == "chart" else None
            section_node_map[node_id] = {
                "id": node_id,
                "label": require_non_empty_string(node, "label"),
                "type": node_type,
                "highlight": bool(node.get("highlight", False)),
                "chart": chart,
                "label_position": label_position,
            }
            node_to_section[node_id] = section_id

        seen_lane_ids: set[str] = set()
        lane_memberships: dict[str, str] = {}
        normalized_lanes: list[dict[str, Any]] = []
        for lane in lanes:
            if not isinstance(lane, dict):
                raise DiagramError(f"Section '{section_id}' lanes must be objects.")
            lane_id = require_non_empty_string(lane, "id")
            if lane_id in seen_lane_ids:
                raise DiagramError(f"Duplicate lane id '{lane_id}' in section '{section_id}'.")
            seen_lane_ids.add(lane_id)
            lane_direction = require_non_empty_string(lane, "direction")
            if lane_direction not in VALID_DIRECTIONS:
                raise DiagramError(f"Lane '{lane_id}' has invalid direction '{lane_direction}'.")
            groups = require_list(lane, "groups")
            normalized_groups: list[dict[str, Any]] = []
            for group in groups:
                if not isinstance(group, dict):
                    raise DiagramError(f"Lane '{lane_id}' groups must be objects.")
                group_type = require_non_empty_string(group, "type")
                if group_type not in VALID_GROUP_TYPES:
                    raise DiagramError(f"Lane '{lane_id}' has invalid group type '{group_type}'.")
                group_nodes = require_list(group, "nodes")
                normalized_node_ids: list[str] = []
                for node_id in group_nodes:
                    if not isinstance(node_id, str) or not node_id.strip():
                        raise DiagramError(f"Lane '{lane_id}' group nodes must be non-empty strings.")
                    node_id = node_id.strip()
                    if node_id not in section_node_map:
                        raise DiagramError(
                            f"Lane '{lane_id}' references node '{node_id}' not owned by section '{section_id}'."
                        )
                    if node_id in lane_memberships:
                        raise DiagramError(
                            f"Node '{node_id}' is assigned to more than one lane/group in section '{section_id}'."
                        )
                    lane_memberships[node_id] = lane_id
                    normalized_node_ids.append(node_id)
                normalized_groups.append({"type": group_type, "nodes": normalized_node_ids})
            normalized_lanes.append(
                {
                    "id": lane_id,
                    "title": lane.get("title"),
                    "direction": lane_direction,
                    "x_offset": require_number(lane, "x_offset", 0.0),
                    "y_offset": require_number(lane, "y_offset", 0.0),
                    "groups": normalized_groups,
                }
            )

        if set(section_node_map.keys()) != set(lane_memberships.keys()):
            missing = sorted(set(section_node_map.keys()) - set(lane_memberships.keys()))
            raise DiagramError(
                f"Section '{section_id}' has nodes not assigned to any lane group: {', '.join(missing)}"
            )

        normalized_annotations: list[dict[str, str]] = []
        for annotation in annotations:
            if not isinstance(annotation, dict):
                raise DiagramError(f"Section '{section_id}' annotations must be objects.")
            text = require_non_empty_string(annotation, "text")
            position = annotation.get("position", "footer")
            if position not in {"header", "footer"}:
                raise DiagramError(f"Section '{section_id}' annotation has invalid position '{position}'.")
            normalized_annotations.append({"text": text, "position": position})

        normalized_sections.append(
            {
                "id": section_id,
                "title": require_non_empty_string(section, "title"),
                "subtitle": section.get("subtitle"),
                "layout": {"type": layout_type, "direction": direction},
                "lanes": normalized_lanes,
                "nodes": list(section_node_map.values()),
                "annotations": normalized_annotations,
            }
        )

    normalized_connections: list[dict[str, str]] = []
    for connection in connections:
        if not isinstance(connection, dict):
            raise DiagramError("Each connection must be an object.")
        source = require_non_empty_string(connection, "from")
        target = require_non_empty_string(connection, "to")
        if source not in node_to_section:
            raise DiagramError(f"Connection source '{source}' does not exist.")
        if target not in node_to_section:
            raise DiagramError(f"Connection target '{target}' does not exist.")
        route = connection.get("route", "direct")
        if route not in VALID_ROUTES:
            raise DiagramError(f"Connection '{source}->{target}' has invalid route '{route}'.")
        if "label" in connection and connection.get("label"):
            raise DiagramError("Edge labels are forbidden.")
        normalized_connections.append({"from": source, "to": target, "route": route})

    return {
        "diagram": {
            "title": title,
            "subtitle": subtitle.strip() if isinstance(subtitle, str) and subtitle.strip() else None,
            "show_sections": show_sections,
            "sections": normalized_sections,
            "connections": normalized_connections,
        }
    }


def lane_dimensions(lane: dict[str, Any], node_map: dict[str, dict[str, Any]]) -> tuple[float, float]:
    group_boxes: list[tuple[float, float]] = []
    for group in lane["groups"]:
        node_sizes = [measure_node_footprint(node_map[node_id]) for node_id in group["nodes"]]
        if group["type"] == "sequential":
            if lane["direction"] == "vertical":
                width = max(width for width, _ in node_sizes)
                height = sum(height for _, height in node_sizes) + NODE_GAP * (len(node_sizes) - 1)
            else:
                width = sum(width for width, _ in node_sizes) + NODE_GAP * (len(node_sizes) - 1)
                height = max(height for _, height in node_sizes)
        else:
            if lane["direction"] == "vertical":
                width = sum(width for width, _ in node_sizes) + NODE_GAP * (len(node_sizes) - 1)
                height = max(height for _, height in node_sizes)
            else:
                width = max(width for width, _ in node_sizes)
                height = sum(height for _, height in node_sizes) + NODE_GAP * (len(node_sizes) - 1)
        group_boxes.append((width, height))

    if lane["direction"] == "vertical":
        width = max(width for width, _ in group_boxes)
        height = sum(height for _, height in group_boxes) + GROUP_GAP * (len(group_boxes) - 1)
    else:
        width = sum(width for width, _ in group_boxes) + GROUP_GAP * (len(group_boxes) - 1)
        height = max(height for _, height in group_boxes)

    if lane.get("title"):
        height += 22 if lane["direction"] == "vertical" else 18
        width = max(width, 86)

    return width, height


def lane_positions(
    section: dict[str, Any], lane_sizes: list[tuple[float, float]]
) -> tuple[list[tuple[float, float]], float, float, float, float]:
    positions: list[tuple[float, float]] = []
    min_x = 0.0
    min_y = 0.0
    max_x = 0.0
    max_y = 0.0
    cursor = 0.0

    for index, lane in enumerate(section["lanes"]):
        lane_width, lane_height = lane_sizes[index]
        if section["layout"]["direction"] == "horizontal":
            x = cursor + lane["x_offset"]
            y = lane["y_offset"]
            cursor += lane_width + LANE_GAP
        else:
            x = lane["x_offset"]
            y = cursor + lane["y_offset"]
            cursor += lane_height + LANE_GAP

        positions.append((x, y))
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + lane_width)
        max_y = max(max_y, y + lane_height)

    return positions, min_x, min_y, max_x, max_y


def layout_group(
    lane: dict[str, Any],
    group: dict[str, Any],
    x: float,
    y: float,
    node_specs: dict[str, dict[str, Any]],
    section_id: str,
    lane_id: str,
    positioned: dict[str, NodeLayout],
) -> tuple[float, float]:
    node_sizes = [
        (node_id, *measure_node(node_specs[node_id]), *measure_node_footprint(node_specs[node_id]))
        for node_id in group["nodes"]
    ]
    if group["type"] == "sequential":
        advance = 0.0
        max_width = 0.0
        max_height = 0.0
        track_width = max(footprint_width for _, _, _, footprint_width, _ in node_sizes)
        track_height = max(footprint_height for _, _, _, _, footprint_height in node_sizes)
        for node_id, width, height, footprint_width, footprint_height in node_sizes:
            node_dx, node_dy = node_offset_within_footprint(node_specs[node_id])
            if lane["direction"] == "vertical":
                node_x = x + (track_width - footprint_width) / 2 + (footprint_width - width) / 2 + node_dx
                node_y = y + advance + node_dy
                advance += footprint_height + NODE_GAP
            else:
                node_x = x + advance + node_dx
                node_y = y + (track_height - footprint_height) / 2 + node_dy
                advance += footprint_width + NODE_GAP
            positioned[node_id] = NodeLayout(
                node_id=node_id,
                label=node_specs[node_id]["label"],
                node_type=node_specs[node_id]["type"],
                highlight=node_specs[node_id]["highlight"],
                chart=node_specs[node_id].get("chart"),
                label_position=node_specs[node_id]["label_position"],
                x=node_x,
                y=node_y,
                width=width,
                height=height,
                section_id=section_id,
                lane_id=lane_id,
            )
            max_width = max(max_width, footprint_width)
            max_height = max(max_height, footprint_height)
        if lane["direction"] == "vertical":
            return max_width, advance - NODE_GAP
        return advance - NODE_GAP, max_height

    advance = 0.0
    max_width = 0.0
    max_height = 0.0
    if lane["direction"] == "vertical":
        row_height = max(footprint_height for _, _, _, _, footprint_height in node_sizes)
        for node_id, width, height, footprint_width, footprint_height in node_sizes:
            node_dx, node_dy = node_offset_within_footprint(node_specs[node_id])
            node_x = x + advance + node_dx
            node_y = y + (row_height - footprint_height) / 2 + node_dy
            positioned[node_id] = NodeLayout(
                node_id=node_id,
                label=node_specs[node_id]["label"],
                node_type=node_specs[node_id]["type"],
                highlight=node_specs[node_id]["highlight"],
                chart=node_specs[node_id].get("chart"),
                label_position=node_specs[node_id]["label_position"],
                x=node_x,
                y=node_y,
                width=width,
                height=height,
                section_id=section_id,
                lane_id=lane_id,
            )
            advance += footprint_width + NODE_GAP
            max_width = max(max_width, advance - NODE_GAP)
            max_height = max(max_height, row_height)
        return max_width, row_height

    column_width = max(footprint_width for _, _, _, footprint_width, _ in node_sizes)
    for node_id, width, height, footprint_width, footprint_height in node_sizes:
        node_dx, node_dy = node_offset_within_footprint(node_specs[node_id])
        node_x = x + (column_width - footprint_width) / 2 + (footprint_width - width) / 2 + node_dx
        node_y = y + advance + node_dy
        positioned[node_id] = NodeLayout(
            node_id=node_id,
            label=node_specs[node_id]["label"],
            node_type=node_specs[node_id]["type"],
            highlight=node_specs[node_id]["highlight"],
            chart=node_specs[node_id].get("chart"),
            label_position=node_specs[node_id]["label_position"],
            x=node_x,
            y=node_y,
            width=width,
            height=height,
            section_id=section_id,
            lane_id=lane_id,
        )
        advance += footprint_height + NODE_GAP
        max_width = max(max_width, column_width)
        max_height = max(max_height, advance - NODE_GAP)
    return column_width, max_height


def layout_diagram(diagram: dict[str, Any]) -> tuple[list[SectionLayout], dict[str, NodeLayout], int, int]:
    section_layouts: list[SectionLayout] = []
    node_layouts: dict[str, NodeLayout] = {}
    x_cursor = CANVAS_PAD_X
    max_height = 0.0

    for section in diagram["sections"]:
        node_specs = {node["id"]: node for node in section["nodes"]}
        lane_sizes = [lane_dimensions(lane, node_specs) for lane in section["lanes"]]
        lane_offsets, min_lane_x, min_lane_y, max_lane_x, max_lane_y = lane_positions(section, lane_sizes)

        content_width = max_lane_x - min_lane_x
        content_height = max_lane_y - min_lane_y
        subtitle_lines = (
            wrap_text_to_width(section["subtitle"], SECTION_MAX_WIDTH - SECTION_PAD_X * 2, max_lines=3)
            if section.get("subtitle")
            else []
        )
        footer_annotations = [a["text"] for a in section["annotations"] if a["position"] == "footer"]
        footer_line_count = sum(
            len(wrap_text_to_width(note, SECTION_MAX_WIDTH - SECTION_PAD_X * 2, max_lines=3))
            for note in footer_annotations
        )
        footer_height = footer_line_count * 14
        subtitle_extra = len(subtitle_lines) * 14
        section_width = max(SECTION_MIN_WIDTH, content_width + SECTION_PAD_X * 2)
        section_height = max(
            360.0,
            SECTION_PAD_TOP + subtitle_extra + content_height + SECTION_PAD_BOTTOM + footer_height,
        )

        section_layout = SectionLayout(
            section_id=section["id"],
            title=section["title"],
            subtitle=section.get("subtitle"),
            x=x_cursor,
            y=CANVAS_PAD_Y + TITLE_BLOCK_H,
            width=section_width,
            height=section_height,
            footer_annotations=footer_annotations,
        )
        section_layouts.append(section_layout)

        y_base = section_layout.y + SECTION_PAD_TOP + subtitle_extra
        inner_width = section_layout.width - SECTION_PAD_X * 2
        x_centering_offset = max(0.0, (inner_width - content_width) / 2)
        for index, lane in enumerate(section["lanes"]):
            lane_width, lane_height = lane_sizes[index]
            lane_x = section_layout.x + SECTION_PAD_X + x_centering_offset + (lane_offsets[index][0] - min_lane_x)
            lane_y = y_base + (lane_offsets[index][1] - min_lane_y)
            group_cursor = lane_y + (18 if lane.get("title") else 0)

            for group in lane["groups"]:
                group_width, group_height = layout_group(
                    lane=lane,
                    group=group,
                    x=lane_x,
                    y=group_cursor,
                    node_specs=node_specs,
                    section_id=section["id"],
                    lane_id=lane["id"],
                    positioned=node_layouts,
                )
                if lane["direction"] == "vertical":
                    group_cursor += group_height + GROUP_GAP
                else:
                    group_cursor += group_width + GROUP_GAP

        x_cursor += section_width + SECTION_GAP
        max_height = max(max_height, section_height)

    total_width = int(x_cursor - SECTION_GAP + CANVAS_PAD_X)
    title_rect = centered_text_rect(0.0, 56.0, diagram["title"], 32, padding_x=12.0, padding_y=8.0)
    total_width = max(total_width, int(math.ceil(title_rect.right - title_rect.left + CANVAS_PAD_X * 2)))
    if diagram.get("subtitle"):
        subtitle_rect = centered_text_rect(
            0.0,
            80.0,
            diagram["subtitle"],
            14,
            padding_x=10.0,
            padding_y=6.0,
        )
        total_width = max(total_width, int(math.ceil(subtitle_rect.right - subtitle_rect.left + CANVAS_PAD_X * 2)))
    if section_layouts:
        content_left = min(section.x for section in section_layouts)
        content_right = max(section.x + section.width for section in section_layouts)
        content_width = content_right - content_left
        centered_left = (total_width - content_width) / 2
        x_shift = centered_left - content_left
        if abs(x_shift) > 0.01:
            for section in section_layouts:
                section.x += x_shift
            for node in node_layouts.values():
                node.x += x_shift
    total_height = int(CANVAS_PAD_Y + TITLE_BLOCK_H + max_height + CANVAS_PAD_Y)
    return section_layouts, node_layouts, total_width, total_height


def candidate_port_sides(source: NodeLayout, target: NodeLayout, route: str) -> list[tuple[str, str]]:
    if abs(target.center_x - source.center_x) < 0.01:
        if target.center_y >= source.center_y:
            return [("bottom", "top"), ("right", "left"), ("left", "right")]
        return [("top", "bottom"), ("right", "left"), ("left", "right")]
    if route == "vertical" and (source.node_type in BADGE_NODE_TYPES or target.node_type in BADGE_NODE_TYPES):
        if target.center_y >= source.center_y:
            return [("right", "left"), ("left", "right"), ("bottom", "top")]
        return [("right", "left"), ("left", "right"), ("top", "bottom")]
    if route == "vertical":
        if target.center_y >= source.center_y:
            return [("bottom", "top"), ("right", "left"), ("left", "right")]
        return [("top", "bottom"), ("right", "left"), ("left", "right")]
    if target.center_y < source.center_y - 0.01:
        if target.center_x >= source.center_x:
            return [("top", "bottom"), ("right", "bottom"), ("right", "left"), ("left", "right"), ("bottom", "top")]
        return [("top", "bottom"), ("left", "bottom"), ("left", "right"), ("right", "left"), ("bottom", "top")]
    if target.center_y > source.center_y + 0.01:
        if target.center_x >= source.center_x:
            return [("bottom", "top"), ("right", "top"), ("right", "left"), ("left", "right"), ("top", "bottom")]
        return [("bottom", "top"), ("left", "top"), ("left", "right"), ("right", "left"), ("top", "bottom")]
    if target.center_x >= source.center_x:
        return [("right", "left"), ("bottom", "top"), ("top", "bottom")]
    return [("left", "right"), ("bottom", "top"), ("top", "bottom")]


def port_point(node: NodeLayout, side: str) -> tuple[float, float]:
    if side == "left":
        return node.left, node.center_y
    if side == "right":
        return node.right, node.center_y
    if side == "top":
        return node.center_x, node.top
    return node.center_x, node.bottom


def stub_point(point: tuple[float, float], side: str) -> tuple[float, float]:
    x, y = point
    if side == "left":
        return x - EDGE_STUB, y
    if side == "right":
        return x + EDGE_STUB, y
    if side == "top":
        return x, y - EDGE_STUB
    return x, y + EDGE_STUB


def side_axis(side: str) -> str:
    return "h" if side in {"left", "right"} else "v"


def point_in_rect(point: tuple[float, float], rect: Rect) -> bool:
    x, y = point
    return rect.left < x < rect.right and rect.top < y < rect.bottom


def point_is_clear(point: tuple[float, float], obstacles: list[tuple[str, Rect]], allowed: set[str]) -> bool:
    for obstacle_id, obstacle in obstacles:
        if obstacle_id in allowed:
            continue
        if point_in_rect(point, obstacle):
            return False
    return True


def segment_is_clear(
    start: tuple[float, float],
    end: tuple[float, float],
    obstacles: list[tuple[str, Rect]],
    allowed: set[str],
) -> bool:
    if abs(start[0] - end[0]) > 0.01 and abs(start[1] - end[1]) > 0.01:
        return False
    for obstacle_id, obstacle in obstacles:
        if obstacle_id in allowed:
            continue
        if abs(start[0] - end[0]) < 0.01:
            x = start[0]
            y1, y2 = sorted((start[1], end[1]))
            if obstacle.left < x < obstacle.right and y1 < obstacle.bottom and y2 > obstacle.top:
                return False
        else:
            y = start[1]
            x1, x2 = sorted((start[0], end[0]))
            if obstacle.top < y < obstacle.bottom and x1 < obstacle.right and x2 > obstacle.left:
                return False
    return True


def preferred_elbow_points(
    source_port: tuple[float, float],
    source_stub: tuple[float, float],
    source_side: str,
    target_stub: tuple[float, float],
    target_port: tuple[float, float],
    target_side: str,
    obstacles: list[tuple[str, Rect]],
    allowed: set[str],
) -> list[tuple[float, float]] | None:
    source_axis = side_axis(source_side)
    target_axis = side_axis(target_side)
    if source_axis == "h" and target_axis == "h":
        corner = (source_stub[0], target_stub[1])
    elif source_axis == "v" and target_axis == "v":
        corner = (target_stub[0], source_stub[1])
    elif source_axis == "h" and target_axis == "v":
        corner = (target_stub[0], source_stub[1])
    else:
        corner = (source_stub[0], target_stub[1])

    if not point_is_clear(corner, obstacles, allowed):
        return None
    if not segment_is_clear(source_stub, corner, obstacles, allowed):
        return None
    if not segment_is_clear(corner, target_stub, obstacles, allowed):
        return None
    return [source_port, source_stub, corner, target_stub, target_port]


def unique_sorted_coords(values: list[float]) -> list[float]:
    unique_values: list[float] = []
    for value in sorted(float(value) for value in values):
        if not unique_values or abs(value - unique_values[-1]) > 0.05:
            unique_values.append(value)
    return unique_values


def title_text_obstacles(title: str, subtitle: str | None, width: int) -> list[tuple[str, Rect]]:
    obstacles = [("diagram_title", centered_text_rect(width / 2, 56, title, 32, padding_x=12.0, padding_y=8.0))]
    if subtitle:
        obstacles.append(
            ("diagram_subtitle", centered_text_rect(width / 2, 80, subtitle, 14, padding_x=10.0, padding_y=6.0))
        )
    return obstacles


def section_text_obstacles(section: SectionLayout) -> list[tuple[str, Rect]]:
    obstacles: list[tuple[str, Rect]] = []
    center_x = section.x + section.width / 2
    title_y = section.y + 34
    obstacles.append(
        (
            f"section_title:{section.section_id}",
            centered_text_rect(center_x, title_y, section.title, 14, padding_x=10.0, padding_y=6.0),
        )
    )
    if section.subtitle:
        subtitle_lines = wrap_text_to_width(section.subtitle, section.width - SECTION_PAD_X * 2, max_lines=3)
        for idx, line in enumerate(subtitle_lines):
            baseline_y = title_y + 20 + idx * 14
            obstacles.append(
                (
                    f"section_subtitle:{section.section_id}:{idx}",
                    centered_text_rect(center_x, baseline_y, line, 12, padding_x=8.0, padding_y=5.0),
                )
            )

    consumed_lines = 0
    for note in reversed(section.footer_annotations):
        note_lines = wrap_text_to_width(note, section.width - SECTION_PAD_X * 2, max_lines=3)
        base_y = section.y + section.height - 12 - consumed_lines * 14 - (len(note_lines) - 1) * 14
        for line_index, line in enumerate(note_lines):
            baseline_y = base_y + line_index * 14
            obstacles.append(
                (
                    f"section_footer:{section.section_id}:{consumed_lines + line_index}",
                    centered_text_rect(center_x, baseline_y, line, 11, padding_x=8.0, padding_y=4.0),
                )
            )
        consumed_lines += len(note_lines)
    return obstacles


def node_text_obstacles(nodes: dict[str, NodeLayout]) -> list[tuple[str, Rect]]:
    obstacles: list[tuple[str, Rect]] = []
    for node in nodes.values():
        if node.node_type in BADGE_NODE_TYPES:
            obstacles.append(
                (
                    f"node_label:{node.node_id}",
                    badge_label_rect(node),
                )
            )
        if node.node_type == "chart":
            chart_pad_x = 14.0
            chart_pad_y = 12.0
            title_width = node.width - chart_pad_x * 2
            title_lines = wrap_text_to_width(node.label, title_width, max_lines=2)
            for index, line in enumerate(title_lines):
                baseline_y = node.y + chart_pad_y + 12 + index * 13
                obstacles.append(
                    (
                        f"chart_title:{node.node_id}:{index}",
                        centered_text_rect(
                            node.x + node.width / 2,
                            baseline_y,
                            line,
                            12,
                            padding_x=6.0,
                            padding_y=4.0,
                        ),
                    )
                )
    return obstacles


def badge_label_rect(node: NodeLayout) -> Rect:
    baseline_y = (
        node.top + BADGE_LABEL_TOP_BASELINE_OFFSET
        if node.label_position == "top"
        else node.bottom + BADGE_LABEL_BASELINE_OFFSET
    )
    return centered_text_rect(
        node.center_x,
        baseline_y,
        node.label,
        BADGE_LABEL_FONT_SIZE,
        padding_x=8.0,
        padding_y=5.0,
    )


def build_edge_obstacles(
    title: str,
    subtitle: str | None,
    sections: list[SectionLayout],
    nodes: dict[str, NodeLayout],
    width: int,
) -> list[tuple[str, Rect]]:
    obstacles = [(node_id, node.rect.inflate(EDGE_CLEARANCE)) for node_id, node in nodes.items()]
    obstacles.extend((obstacle_id, rect.inflate(EDGE_CLEARANCE / 2)) for obstacle_id, rect in title_text_obstacles(title, subtitle, width))
    for section in sections:
        obstacles.extend(
            (obstacle_id, rect.inflate(EDGE_CLEARANCE / 2))
            for obstacle_id, rect in section_text_obstacles(section)
        )
    obstacles.extend(
        (obstacle_id, rect.inflate(EDGE_CLEARANCE / 2)) for obstacle_id, rect in node_text_obstacles(nodes)
    )
    return obstacles


def route_connection_points(
    connection: dict[str, str],
    nodes: dict[str, NodeLayout],
    obstacles: list[tuple[str, Rect]],
    width: int,
    height: int,
) -> list[tuple[float, float]]:
    source = nodes[connection["from"]]
    target = nodes[connection["to"]]
    allowed = {source.node_id, target.node_id}
    candidates: list[tuple[float, list[tuple[float, float]]]] = []

    for preference_index, (source_side, target_side) in enumerate(candidate_port_sides(source, target, connection["route"])):
        source_port = port_point(source, source_side)
        target_port = port_point(target, target_side)
        source_stub = stub_point(source_port, source_side)
        target_stub = stub_point(target_port, target_side)

        if not point_is_clear(source_stub, obstacles, allowed):
            continue
        if not point_is_clear(target_stub, obstacles, allowed):
            continue

        preferred = preferred_elbow_points(
            source_port,
            source_stub,
            source_side,
            target_stub,
            target_port,
            target_side,
            obstacles,
            allowed,
        )
        if preferred:
            candidates.append((route_rank(preferred, preference_index), preferred))

        x_values = [
            CANVAS_PAD_X / 2,
            width - CANVAS_PAD_X / 2,
            source_port[0],
            source_stub[0],
            target_port[0],
            target_stub[0],
        ]
        y_values = [
            TITLE_BLOCK_H,
            height - CANVAS_PAD_Y / 2,
            source_port[1],
            source_stub[1],
            target_port[1],
            target_stub[1],
        ]
        for _, obstacle in obstacles:
            x_values.extend([obstacle.left - GRID_MARGIN, obstacle.left, obstacle.right, obstacle.right + GRID_MARGIN])
            y_values.extend([obstacle.top - GRID_MARGIN, obstacle.top, obstacle.bottom, obstacle.bottom + GRID_MARGIN])

        xs = unique_sorted_coords(x_values)
        ys = unique_sorted_coords(y_values)
        points = [(x, y) for x in xs for y in ys if point_is_clear((x, y), obstacles, allowed)]
        point_to_index = {point: index for index, point in enumerate(points)}
        if source_stub not in point_to_index or target_stub not in point_to_index:
            continue

        neighbors: dict[int, list[tuple[int, str]]] = {index: [] for index in range(len(points))}
        for y in ys:
            row = [(point, point_to_index[point]) for point in points if abs(point[1] - y) < 0.01]
            row.sort(key=lambda item: item[0][0])
            for (p1, i1), (p2, i2) in zip(row, row[1:]):
                if segment_is_clear(p1, p2, obstacles, allowed):
                    neighbors[i1].append((i2, "h"))
                    neighbors[i2].append((i1, "h"))
        for x in xs:
            column = [(point, point_to_index[point]) for point in points if abs(point[0] - x) < 0.01]
            column.sort(key=lambda item: item[0][1])
            for (p1, i1), (p2, i2) in zip(column, column[1:]):
                if segment_is_clear(p1, p2, obstacles, allowed):
                    neighbors[i1].append((i2, "v"))
                    neighbors[i2].append((i1, "v"))

        start = point_to_index[source_stub]
        goal = point_to_index[target_stub]
        start_direction = side_axis(source_side)
        target_direction = side_axis(target_side)
        heap: list[tuple[float, float, int, str | None]] = [(0.0, 0.0, start, start_direction)]
        best_cost: dict[tuple[int, str | None], float] = {(start, start_direction): 0.0}
        previous: dict[tuple[int, str | None], tuple[int, str | None]] = {}
        end_state: tuple[int, str | None] | None = None
        end_total_cost = float("inf")

        while heap:
            _, cost, index, direction = heapq.heappop(heap)
            state = (index, direction)
            if cost > best_cost.get(state, float("inf")) + 0.01:
                continue
            if index == goal:
                final_bend_penalty = TURN_PENALTY if direction and direction != target_direction else 0.0
                total_cost = cost + final_bend_penalty
                if total_cost + 0.01 < end_total_cost:
                    end_total_cost = total_cost
                    end_state = state
                continue

            current = points[index]
            for next_index, next_direction in neighbors[index]:
                nxt = points[next_index]
                step = abs(current[0] - nxt[0]) + abs(current[1] - nxt[1])
                bend_penalty = 14.0 if direction and direction != next_direction else 0.0
                next_cost = cost + step + bend_penalty
                next_state = (next_index, next_direction)
                if next_cost + 0.01 < best_cost.get(next_state, float("inf")):
                    best_cost[next_state] = next_cost
                    previous[next_state] = state
                    heuristic = abs(nxt[0] - target_stub[0]) + abs(nxt[1] - target_stub[1])
                    heapq.heappush(heap, (next_cost + heuristic, next_cost, next_index, next_direction))

        if end_state is None:
            continue

        routed = [points[end_state[0]]]
        state = end_state
        while state in previous:
            state = previous[state]
            routed.append(points[state[0]])
        routed.reverse()
        candidate = [source_port, source_stub, *routed[1:-1], target_stub, target_port]
        candidates.append((route_rank(candidate, preference_index), candidate))

    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    raise DiagramError(
        f"Could not route connection '{source.node_id}->{target.node_id}' without crossing nodes or text."
    )


def route_rank(points: list[tuple[float, float]], preference_index: int) -> float:
    simplified = simplify_points(points)
    length = 0.0
    for start, end in zip(simplified, simplified[1:]):
        length += abs(start[0] - end[0]) + abs(start[1] - end[1])
    turns = max(0, len(simplified) - 2)
    return length + turns * TURN_PENALTY + preference_index * PORT_PREFERENCE_PENALTY


def simplify_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(points) < 3:
        return points
    simplified = [points[0]]
    for point in points[1:-1]:
        prev = simplified[-1]
        nxt = points[points.index(point) + 1]
        same_x = abs(prev[0] - point[0]) < 0.01 and abs(point[0] - nxt[0]) < 0.01
        same_y = abs(prev[1] - point[1]) < 0.01 and abs(point[1] - nxt[1]) < 0.01
        if same_x or same_y:
            continue
        simplified.append(point)
    simplified.append(points[-1])
    return simplified


def rounded_orthogonal_path(points: list[tuple[float, float]], radius: float = 10.0) -> str:
    points = simplify_points(points)
    if len(points) < 2:
        return ""
    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for idx in range(1, len(points) - 1):
        prev_x, prev_y = points[idx - 1]
        curr_x, curr_y = points[idx]
        next_x, next_y = points[idx + 1]

        in_len = abs(curr_x - prev_x) + abs(curr_y - prev_y)
        out_len = abs(next_x - curr_x) + abs(next_y - curr_y)
        corner = min(radius, in_len / 2, out_len / 2)

        start_x = curr_x
        start_y = curr_y
        end_x = curr_x
        end_y = curr_y

        if abs(prev_x - curr_x) < 0.01:
            start_y = curr_y - corner if prev_y < curr_y else curr_y + corner
        else:
            start_x = curr_x - corner if prev_x < curr_x else curr_x + corner

        if abs(next_x - curr_x) < 0.01:
            end_y = curr_y + corner if next_y > curr_y else curr_y - corner
        else:
            end_x = curr_x + corner if next_x > curr_x else curr_x - corner

        commands.append(f"L {start_x:.1f} {start_y:.1f}")
        commands.append(f"Q {curr_x:.1f} {curr_y:.1f} {end_x:.1f} {end_y:.1f}")

    commands.append(f"L {points[-1][0]:.1f} {points[-1][1]:.1f}")
    return " ".join(commands)


def marker_adjusted_points(points: list[tuple[float, float]], offset: float = 1.0) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points
    adjusted = list(points)
    prev_x, prev_y = adjusted[-2]
    end_x, end_y = adjusted[-1]
    if abs(prev_x - end_x) < 0.01:
        end_y -= offset if end_y > prev_y else -offset
    elif abs(prev_y - end_y) < 0.01:
        end_x -= offset if end_x > prev_x else -offset
    adjusted[-1] = (end_x, end_y)
    return adjusted


def render_title(title: str, subtitle: str | None, width: int) -> str:
    lines = [
        f'<text x="{width / 2:.1f}" y="56" text-anchor="middle" font-family="{FONT_STACK}" font-size="32" font-weight="700" fill="{TOKENS["text"]}">{escape(title)}</text>'
    ]
    if subtitle:
        lines.append(
            f'<text x="{width / 2:.1f}" y="80" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="500" fill="{TOKENS["muted_text"]}">{escape(subtitle)}</text>'
        )
    return "\n".join(lines)


def render_section(section: SectionLayout) -> str:
    title_y = section.y + 34
    parts = [
        f'<rect x="{section.x:.1f}" y="{section.y:.1f}" width="{section.width:.1f}" height="{section.height:.1f}" rx="{SECTION_RADIUS}" fill="{TOKENS["section"]}" stroke="{TOKENS["panel_border"]}" filter="url(#panelShadow)"/>',
        f'<text x="{section.x + section.width / 2:.1f}" y="{title_y:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="700" letter-spacing="0.06em" fill="{TOKENS["text"]}">{escape(section.title)}</text>',
    ]
    if section.subtitle:
        subtitle_lines = wrap_text_to_width(section.subtitle, section.width - SECTION_PAD_X * 2, max_lines=3)
        for idx, line in enumerate(subtitle_lines):
            parts.append(
                f'<text x="{section.x + section.width / 2:.1f}" y="{title_y + 20 + idx * 14:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="12" font-weight="600" fill="{TOKENS["text"]}">{escape(line)}</text>'
            )

    consumed_lines = 0
    for note in reversed(section.footer_annotations):
        note_lines = wrap_text_to_width(note, section.width - SECTION_PAD_X * 2, max_lines=3)
        base_y = section.y + section.height - 12 - consumed_lines * 14 - (len(note_lines) - 1) * 14
        for line_index, line in enumerate(note_lines):
            parts.append(
                f'<text x="{section.x + section.width / 2:.1f}" y="{base_y + line_index * 14:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="11" font-weight="500" fill="{TOKENS["muted_text"]}">{escape(line)}</text>'
            )
        consumed_lines += len(note_lines)
    return "\n".join(parts)


def render_badge_shell(node: NodeLayout) -> list[str]:
    cx = node.center_x
    cy = node.center_y
    r = node.width / 2
    label_y = (
        node.top + BADGE_LABEL_TOP_BASELINE_OFFSET
        if node.label_position == "top"
        else node.bottom + BADGE_LABEL_BASELINE_OFFSET
    )
    return [
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{TOKENS["panel"]}" stroke="{TOKENS["border"]}" stroke-width="1.4"/>',
        f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{BADGE_LABEL_FONT_SIZE}" font-weight="500" fill="{TOKENS["text"]}">{escape(node.label)}</text>',
    ]


def render_user_node(node: NodeLayout) -> str:
    cx = node.center_x
    cy = node.center_y
    parts = render_badge_shell(node)
    parts.insert(
        1,
        f'<circle cx="{cx:.1f}" cy="{cy - 8:.1f}" r="8" fill="none" stroke="#35C89B" stroke-width="2"/>',
    )
    parts.insert(
        2,
        f'<path d="M {cx - 12:.1f} {cy + 13:.1f} C {cx - 10:.1f} {cy + 2:.1f}, {cx + 10:.1f} {cy + 2:.1f}, {cx + 12:.1f} {cy + 13:.1f}" fill="none" stroke="#35C89B" stroke-width="2"/>',
    )
    return "\n".join(parts)


def render_storage_node(node: NodeLayout) -> str:
    cx = node.center_x
    cy = node.center_y
    left = cx - 14
    right = cx + 14
    top = cy - 12
    bottom = cy + 12
    parts = render_badge_shell(node)
    parts.insert(
        1,
        f'<ellipse cx="{cx:.1f}" cy="{top:.1f}" rx="14" ry="5.5" fill="{TOKENS["panel"]}" stroke="#35C89B" stroke-width="1.8"/>',
    )
    parts.insert(
        2,
        f'<path d="M {left:.1f} {top:.1f} L {left:.1f} {bottom:.1f} M {right:.1f} {top:.1f} L {right:.1f} {bottom:.1f}" fill="none" stroke="#35C89B" stroke-width="1.8" stroke-linecap="round"/>',
    )
    parts.insert(
        3,
        f'<path d="M {left:.1f} {bottom:.1f} A 14 5.5 0 0 0 {right:.1f} {bottom:.1f}" fill="none" stroke="#35C89B" stroke-width="1.8"/>',
    )
    parts.insert(
        4,
        f'<path d="M {left:.1f} {cy - 1:.1f} A 14 5.5 0 0 0 {right:.1f} {cy - 1:.1f}" fill="none" stroke="#35C89B" stroke-width="1.4"/>',
    )
    return "\n".join(parts)


def render_cloud_node(node: NodeLayout) -> str:
    cx = node.center_x
    cy = node.center_y
    scale = 0.42
    translate_x = cx - 21.0
    translate_y = cy - 21.0
    cloud_path = (
        "M77.258,37.494c-1.375,0-2.764,0.164-4.276,0.511c-4.115-9.401-13.534-15.606-23.957-15.606 "
        "c-13.11,0-24.034,9.643-25.863,22.363c-1.114-0.215-2.249-0.323-3.395-0.323c-9.824,0-17.816,7.759-17.816,17.529 "
        "C1.95,71.74,9.942,79.5,19.767,79.5h57.491c11.726,0,21.266-9.308,21.266-20.981C98.523,46.82,88.983,37.494,77.258,37.494z "
        "M77.258,75.5H19.767c-7.618,0-13.816-5.966-13.816-13.532c0-7.565,6.198-13.625,13.816-13.625c1.401,0,2.782,0.255,4.093,0.663 "
        "l0.458,0.169c0.591,0.186,1.234,0.102,1.745-0.25c0.51-0.354,0.826-0.918,0.857-1.537c0.595-11.772,10.304-20.992,22.104-20.992 "
        "c9.319,0,17.689,5.851,20.828,14.557c0.063,0.175,0.15,0.34,0.26,0.491l0.078,0.109c0.497,0.691,1.378,0.992,2.195,0.748 "
        "c1.863-0.558,3.365-0.806,4.872-0.806c9.521,0,17.266,7.532,17.266,17.024C94.523,67.987,86.778,75.5,77.258,75.5z"
    )
    parts = render_badge_shell(node)
    parts.insert(
        1,
        f'<path d="{cloud_path}" fill="#35C89B" transform="translate({translate_x:.1f} {translate_y:.1f}) scale({scale:.3f})"/>',
    )
    return "\n".join(parts)


def render_security_node(node: NodeLayout) -> str:
    cx = node.center_x
    cy = node.center_y
    parts = render_badge_shell(node)
    parts.insert(
        1,
        f'<path d="M {cx - 10:.1f} {cy - 4:.1f} A 10 10 0 0 1 {cx + 10:.1f} {cy - 4:.1f}" fill="none" stroke="#35C89B" stroke-width="2" stroke-linecap="round"/>',
    )
    parts.insert(
        2,
        f'<rect x="{cx - 14:.1f}" y="{cy - 3:.1f}" width="28" height="22" rx="6" fill="{TOKENS["panel"]}" stroke="#35C89B" stroke-width="1.8"/>',
    )
    parts.insert(
        3,
        f'<circle cx="{cx:.1f}" cy="{cy + 7:.1f}" r="2.8" fill="#35C89B"/>',
    )
    parts.insert(
        4,
        f'<path d="M {cx:.1f} {cy + 9.8:.1f} L {cx:.1f} {cy + 14.5:.1f}" fill="none" stroke="#35C89B" stroke-width="1.8" stroke-linecap="round"/>',
    )
    return "\n".join(parts)


def render_status_node(node: NodeLayout) -> str:
    fill = TOKENS["ok"] if node.highlight else "#FDE3E1"
    stroke = "#5CAD73" if node.highlight else TOKENS["danger"]
    text = "#2C6C3C" if node.highlight else "#C94F48"
    lines = wrap_label(node.label, 16 if len(node.label) > 18 else 18)
    line_height = 15
    first_baseline = node.center_y + 4 - ((len(lines) - 1) * line_height) / 2
    parts = [
        f'<rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    ]
    for idx, line in enumerate(lines):
        parts.append(
            f'<text x="{node.center_x:.1f}" y="{first_baseline + idx * line_height:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="600" fill="{text}">{escape(line)}</text>'
        )
    return "\n".join(parts)


def chart_color(explicit_color: str | None, index: int, reference: bool = False) -> str:
    if explicit_color:
        return explicit_color
    palette = CHART_REFERENCE_COLORS if reference else CHART_SERIES_COLORS
    return palette[index % len(palette)]


def chart_value_range(chart: dict[str, Any]) -> tuple[float, float]:
    if chart.get("y_range"):
        return chart["y_range"]["min"], chart["y_range"]["max"]
    values: list[float] = []
    for series in chart["series"]:
        values.extend(series["points"])
    for reference_line in chart["reference_lines"]:
        if reference_line["points"] is not None:
            values.extend(reference_line["points"])
        elif reference_line["value"] is not None:
            values.append(reference_line["value"])
    y_min = min(values)
    y_max = max(values)
    if math.isclose(y_min, y_max):
        pad = 1.0 if math.isclose(y_min, 0.0) else abs(y_min) * 0.15
        return y_min - pad, y_max + pad
    pad = (y_max - y_min) * 0.08
    return y_min - pad, y_max + pad


def chart_point_coordinates(
    values: list[float],
    plot_x: float,
    plot_y: float,
    plot_width: float,
    plot_height: float,
    y_min: float,
    y_max: float,
) -> list[tuple[float, float]]:
    if len(values) == 1:
        return [(plot_x + plot_width / 2, plot_y + plot_height / 2)]
    step_x = plot_width / (len(values) - 1)
    points: list[tuple[float, float]] = []
    span = y_max - y_min
    for index, value in enumerate(values):
        normalized = 0.5 if math.isclose(span, 0.0) else (value - y_min) / span
        x = plot_x + index * step_x
        y = plot_y + plot_height - normalized * plot_height
        points.append((x, y))
    return points


def polyline_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    commands.extend(f"L {x:.1f} {y:.1f}" for x, y in points[1:])
    return " ".join(commands)


def pie_slice_path(cx: float, cy: float, radius: float, start_angle: float, end_angle: float) -> str:
    x1 = cx + radius * math.cos(start_angle)
    y1 = cy + radius * math.sin(start_angle)
    x2 = cx + radius * math.cos(end_angle)
    y2 = cy + radius * math.sin(end_angle)
    large_arc = 1 if end_angle - start_angle > math.pi else 0
    return (
        f"M {cx:.1f} {cy:.1f} "
        f"L {x1:.1f} {y1:.1f} "
        f"A {radius:.1f} {radius:.1f} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z"
    )


def format_percentage(value: float, total: float) -> str:
    if math.isclose(total, 0.0):
        return "0%"
    percent = (value / total) * 100
    rounded = round(percent)
    if math.isclose(percent, rounded, abs_tol=0.05):
        return f"{rounded:.0f}%"
    return f"{percent:.1f}%"


def render_chart_node(node: NodeLayout) -> str:
    assert node.chart is not None
    chart = node.chart
    caption = chart.get("caption")
    chart_pad_x = 14.0
    chart_pad_y = 12.0
    text_left = node.x + chart_pad_x
    text_width = node.width - chart_pad_x * 2
    text_center = node.center_x
    title_lines = wrap_text_to_width(node.label, text_width, max_lines=2)
    title_line_height = 13.0
    title_h = len(title_lines) * title_line_height
    title_legend_gap = 14.0

    pie_total = sum(series["points"][0] for series in chart["series"]) if chart["kind"] == "pie" else 0.0
    legend_entries = []
    for series in chart["series"]:
        label = series["label"]
        if chart["kind"] == "pie":
            label = f"{label} ({format_percentage(series['points'][0], pie_total)})"
        legend_entries.append(
            {
                "label": label,
                "color": chart_color(series["color"], series["index"]),
                "style": "solid",
            }
        )
    legend_entries.extend(
        {
            "label": reference_line["label"] or reference_line["id"],
            "color": chart_color(reference_line["color"], reference_line["index"], reference=True),
            "style": reference_line["style"],
        }
        for reference_line in chart["reference_lines"]
    )
    legend_rows: list[list[dict[str, str]]] = [[]]
    legend_row_width = 0.0
    for entry in legend_entries:
        entry_width = 18.0 + estimate_text_width(entry["label"], 10)
        if legend_rows[-1] and legend_row_width + entry_width > text_width:
            legend_rows.append([])
            legend_row_width = 0.0
        legend_rows[-1].append(entry)
        legend_row_width += entry_width + 16.0
    legend_line_height = 14.0
    legend_h = len(legend_rows) * legend_line_height if legend_entries else 0.0

    caption_lines = wrap_text_to_width(caption, text_width, max_lines=3) if caption else []
    caption_line_height = 12.0
    caption_h = len(caption_lines) * caption_line_height if caption_lines else 0.0

    content_top = node.y + chart_pad_y
    plot_x = node.x + chart_pad_x
    plot_y = content_top + title_h + title_legend_gap + legend_h + (8.0 if legend_h else 0.0)
    plot_width = node.width - chart_pad_x * 2
    plot_bottom_limit = node.y + node.height - chart_pad_y - (
        caption_h + (CHART_CAPTION_TOP_GAP if caption_h else 0.0) + (CHART_CAPTION_BOTTOM_GAP if caption_h else 0.0)
    )
    plot_height = max(58.0, plot_bottom_limit - plot_y)
    plot_bottom = plot_y + plot_height
    y_min, y_max = chart_value_range(chart)

    fill = "#FFF9F3" if node.highlight else TOKENS["panel"]
    stroke = TOKENS["accent"] if node.highlight else TOKENS["border"]
    parts = [
        f'<rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="{CHART_RADIUS}" fill="{fill}" stroke="{stroke}" stroke-width="{1.8 if node.highlight else 1.2}"/>',
    ]

    for index, line in enumerate(title_lines):
        parts.append(
            f'<text x="{text_center:.1f}" y="{content_top + 12 + index * title_line_height:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{TOKENS["text"]}">{escape(line)}</text>'
        )

    legend_y = content_top + title_h + title_legend_gap
    for row_index, row in enumerate(legend_rows):
        legend_x = text_left
        row_y = legend_y + row_index * legend_line_height
        for entry in row:
            dash = ' stroke-dasharray="5 4"' if entry["style"] == "dashed" else ""
            parts.append(
                f'<line x1="{legend_x:.1f}" y1="{row_y:.1f}" x2="{legend_x + 10:.1f}" y2="{row_y:.1f}" stroke="{entry["color"]}" stroke-width="2.2" stroke-linecap="round"{dash}/>'
            )
            parts.append(
                f'<text x="{legend_x + 14:.1f}" y="{row_y + 3:.1f}" font-family="{FONT_STACK}" font-size="10" font-weight="500" fill="{TOKENS["muted_text"]}">{escape(entry["label"])}</text>'
            )
            legend_x += 18.0 + estimate_text_width(entry["label"], 10) + 16.0

    if chart["kind"] == "pie":
        parts.append(
            f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_width:.1f}" height="{plot_height:.1f}" rx="8" fill="#FBFAF7" stroke="{TOKENS["border"]}" stroke-width="1"/>'
        )
        values = [series["points"][0] for series in chart["series"]]
        total = sum(values) or 1.0
        radius = min(plot_width, plot_height) / 2 - 3.0
        cx = plot_x + plot_width / 2
        cy = plot_y + plot_height / 2
        angle = -math.pi / 2
        for series in chart["series"]:
            value = series["points"][0]
            sweep = (value / total) * math.tau
            next_angle = angle + sweep
            color = chart_color(series["color"], series["index"])
            if sweep > 0:
                parts.append(
                    f'<path d="{pie_slice_path(cx, cy, radius, angle, next_angle)}" fill="{color}" stroke="{TOKENS["panel"]}" stroke-width="1.2" opacity="0.96"/>'
                )
            angle = next_angle
    else:
        parts.append(
            f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_width:.1f}" height="{plot_height:.1f}" rx="8" fill="#FBFAF7" stroke="{TOKENS["border"]}" stroke-width="1"/>'
        )
        parts.append(
            f'<line x1="{plot_x:.1f}" y1="{plot_bottom:.1f}" x2="{plot_x + plot_width:.1f}" y2="{plot_bottom:.1f}" stroke="{TOKENS["border"]}" stroke-width="1"/>'
        )
        for reference_line in chart["reference_lines"]:
            ref_color = chart_color(reference_line["color"], reference_line["index"], reference=True)
            points = (
                chart_point_coordinates(reference_line["points"], plot_x, plot_y, plot_width, plot_height, y_min, y_max)
                if reference_line["points"] is not None
                else chart_point_coordinates(
                    [reference_line["value"]] * len(chart["series"][0]["points"]),
                    plot_x,
                    plot_y,
                    plot_width,
                    plot_height,
                    y_min,
                    y_max,
                )
            )
            dash = ' stroke-dasharray="5 4"' if reference_line["style"] == "dashed" else ""
            parts.append(
                f'<path d="{polyline_path(points)}" fill="none" stroke="{ref_color}" stroke-width="1.6"{dash}/>'
            )

    if chart["kind"] == "bar":
        series_count = len(chart["series"])
        point_count = len(chart["series"][0]["points"])
        slot_width = plot_width / max(1, point_count)
        if point_count == 1 and series_count > 1:
            group_width = plot_width * 0.78
            inter_series_gap = max(8.0, min(16.0, group_width * 0.06))
            bar_width = max(
                12.0,
                min(20.0, (group_width - inter_series_gap * (series_count - 1)) / max(1, series_count)),
            )
        else:
            inter_series_gap = 7.0
            bar_width = max(8.0, min(13.0, (slot_width - inter_series_gap * (series_count - 1)) / max(1, series_count)))
        for series in chart["series"]:
            color = chart_color(series["color"], series["index"])
            for point_index, value in enumerate(series["points"]):
                normalized = 0.5 if math.isclose(y_max - y_min, 0.0) else (value - y_min) / (y_max - y_min)
                bar_height = max(2.0, normalized * plot_height)
                group_width = series_count * bar_width + (series_count - 1) * inter_series_gap
                group_x = plot_x + point_index * slot_width + max(0.0, (slot_width - group_width) / 2)
                x = group_x + series["index"] * (bar_width + inter_series_gap)
                y = plot_bottom - bar_height
                parts.append(
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="3" fill="{color}" opacity="0.92"/>'
                )
    elif chart["kind"] != "pie":
        for series in chart["series"]:
            color = chart_color(series["color"], series["index"])
            points = chart_point_coordinates(series["points"], plot_x, plot_y, plot_width, plot_height, y_min, y_max)
            if chart["kind"] == "area":
                area_path = polyline_path(points)
                area_path += f" L {points[-1][0]:.1f} {plot_bottom:.1f} L {points[0][0]:.1f} {plot_bottom:.1f} Z"
                parts.append(f'<path d="{area_path}" fill="{color}" opacity="0.18" stroke="none"/>')
            parts.append(
                f'<path d="{polyline_path(points)}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
            )

    if caption_lines:
        caption_y = node.y + node.height - chart_pad_y - CHART_CAPTION_BOTTOM_GAP - (
            (len(caption_lines) - 1) * caption_line_height
        )
        for index, line in enumerate(caption_lines):
            parts.append(
                f'<text x="{text_center:.1f}" y="{caption_y + index * caption_line_height:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="10" font-weight="500" fill="{TOKENS["muted_text"]}">{escape(line)}</text>'
            )
    return "\n".join(parts)


def render_node(node: NodeLayout) -> str:
    if node.node_type == "user":
        return render_user_node(node)
    if node.node_type == "storage":
        return render_storage_node(node)
    if node.node_type == "cloud":
        return render_cloud_node(node)
    if node.node_type == "security":
        return render_security_node(node)
    if node.node_type == "status":
        return render_status_node(node)
    if node.node_type == "chart":
        return render_chart_node(node)

    if node.highlight and node.node_type == "process":
        fill = TOKENS["callout"]
        stroke = TOKENS["callout_border"]
    elif node.highlight:
        fill = "#FCE7D8"
        stroke = TOKENS["accent"]
    else:
        fill = TOKENS["panel"]
        stroke = TOKENS["border"]

    lines = wrap_label(node.label, 17 if len(node.label) > 22 else 18)
    line_height = 15
    first_baseline = node.center_y + 4 - ((len(lines) - 1) * line_height) / 2
    parts = [
        f'<rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" rx="{NODE_RADIUS}" fill="{fill}" stroke="{stroke}" stroke-width="{2 if node.highlight else 1.2}"/>'
    ]
    for idx, line in enumerate(lines):
        parts.append(
            f'<text x="{node.center_x:.1f}" y="{first_baseline + idx * line_height:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="500" fill="{TOKENS["text"]}">{escape(line)}</text>'
        )
    return "\n".join(parts)


def render_connection(
    connection: dict[str, str],
    nodes: dict[str, NodeLayout],
    obstacles: list[tuple[str, Rect]],
    width: int,
    height: int,
) -> str:
    points = route_connection_points(connection, nodes, obstacles, width, height)
    points = marker_adjusted_points(points)
    path = rounded_orthogonal_path(points, radius=10)
    return f'<path d="{path}" fill="none" stroke="{TOKENS["edge"]}" stroke-width="1.7" marker-end="url(#arrow)"/>'


def render_svg(spec: dict[str, Any]) -> str:
    diagram = spec["diagram"]
    sections, nodes, width, height = layout_diagram(diagram)
    obstacles = build_edge_obstacles(diagram["title"], diagram.get("subtitle"), sections, nodes, width)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(diagram["title"])}">',
        "<defs>",
        '<filter id="panelShadow" x="-10%" y="-10%" width="120%" height="140%">',
        '<feDropShadow dx="0" dy="2" stdDeviation="8" flood-color="rgba(0,0,0,0.05)"/>',
        "</filter>",
        '<marker id="arrow" viewBox="0 0 11 12" markerWidth="11" markerHeight="12" refX="9.5" refY="6" orient="auto" markerUnits="userSpaceOnUse" overflow="visible">',
        f'<path d="M 1.5 1.0 L 9.5 6 L 1.5 11.0" fill="none" stroke="{TOKENS["edge"]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
        "</marker>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="{TOKENS["canvas"]}"/>',
        render_title(diagram["title"], diagram.get("subtitle"), width),
    ]

    if diagram.get("show_sections", True):
        for section in sections:
            parts.append(render_section(section))
    for node_id in sorted(nodes.keys(), key=lambda key: (nodes[key].y, nodes[key].x)):
        parts.append(render_node(nodes[node_id]))
    for connection in diagram["connections"]:
        parts.append(render_connection(connection, nodes, obstacles, width, height))

    parts.append("</svg>")
    return "\n".join(parts)


def validate_geometry(spec: dict[str, Any]) -> None:
    diagram = spec["diagram"]
    sections, nodes, width, height = layout_diagram(diagram)
    section_by_id = {section.section_id: section for section in sections}
    obstacles = build_edge_obstacles(diagram["title"], diagram.get("subtitle"), sections, nodes, width)

    for node in nodes.values():
        section = section_by_id[node.section_id]
        section_rect = Rect(section.x, section.y, section.x + section.width, section.y + section.height)
        if not section_rect.contains(node.rect):
            raise DiagramError(f"Node '{node.node_id}' crosses its section boundary.")
        if node.node_type in BADGE_NODE_TYPES and not section_rect.contains(badge_label_rect(node)):
            raise DiagramError(f"Badge label for node '{node.node_id}' crosses its section boundary.")

    for connection in diagram["connections"]:
        points = route_connection_points(connection, nodes, obstacles, width, height)
        source = nodes[connection["from"]]
        target = nodes[connection["to"]]
        if source.section_id == target.section_id:
            section = section_by_id[source.section_id]
            section_rect = Rect(section.x, section.y, section.x + section.width, section.y + section.height)
            for x, y in points:
                if not section_rect.contains(Rect(x, y, x, y), tolerance=1.0):
                    raise DiagramError(
                        f"Connection '{source.node_id}->{target.node_id}' exits its section boundary."
                    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a layout-intent diagram into SVG.")
    parser.add_argument("input", help="Path to the diagram spec in JSON.")
    parser.add_argument("--output", help="Where to write the SVG.")
    parser.add_argument("--validate-only", action="store_true", help="Validate the spec and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.input).resolve()
    try:
        spec = validate_spec(load_spec(path))
        if args.validate_only:
            validate_geometry(spec)
    except (OSError, json.JSONDecodeError, DiagramError) as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.validate_only:
        print("OK")
        return 0

    svg = render_svg(spec)
    if args.output:
        Path(args.output).write_text(svg)
    else:
        print(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
