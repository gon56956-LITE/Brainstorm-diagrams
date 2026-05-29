"""Business-simple fault tree SVG renderer."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from renderers.text_utils import chars_for_width, estimate_text_width as measure_text_width, truncate_text, wrap_text


WIDTH = 1920
HEIGHT = 1080
FONT_STACK = "Arial, Helvetica, Microsoft YaHei, Noto Sans CJK SC, sans-serif"

SIDE_MARGIN = 70
CANVAS_WIDTH_STEP = 80
CANVAS_HEIGHT_STEP = 60
CANVAS_BOTTOM_MARGIN = 70
MAX_DEPTH = 3
MAX_FIRST_LEVEL_EVENTS = 8
MAX_CHILDREN_PER_EVENT = 4

TOP_EVENT_W = 460
TOP_EVENT_H = 110
INTERMEDIATE_W = 280
INTERMEDIATE_H = 78
BASIC_W = 210
BASIC_H = 62
BASIC_MAX_W = 320
BASIC_TEXT_PADDING_X = 22
BASIC_TEXT_PADDING_Y = 18
TOP_EVENT_TEXT_PADDING_X = 76
TOP_EVENT_TEXT_PADDING_Y = 22
INTERMEDIATE_TEXT_PADDING_X = 20
INTERMEDIATE_TEXT_PADDING_Y = 18
SUBTREE_GAP = 46
COMPACT_COLUMN_GAP = 34
COMPACT_CHILD_GAP = 14
COMPACT_BRANCH_GAP = 24
PARENT_CHILD_GAP = 128
EVENT_DETAIL_MAX_H = 230
EVENT_DETAIL_MAX_LINES = 5

LEVEL_Y = [118, 360, 595, 820]

PALETTE = {
    "background": "#FFFFFF",
    "background_soft": "#F7FAFD",
    "navy": "#0B2E63",
    "navy_2": "#0B3A75",
    "blue": "#2F6FB6",
    "light_blue": "#DCEBFF",
    "pale_blue": "#F3F8FF",
    "line_blue": "#6E93BD",
    "gray_text": "#5B6B80",
    "light_gray": "#E6EDF5",
    "border_gray": "#9AA9BD",
    "decor": "#BCD2EA",
}

DEFAULT_TREE = [
    {
        "id": "1",
        "type": "intermediate_event",
        "label": "Power Issue",
        "gate": "OR",
        "children": [
            {"id": "1.1", "type": "basic_event", "label": "No Power Supply"},
            {"id": "1.2", "type": "basic_event", "label": "Power Module Fault"},
            {"id": "1.3", "type": "basic_event", "label": "Fuse Blown"},
        ],
    },
    {
        "id": "2",
        "type": "intermediate_event",
        "label": "Control Unit Issue",
        "gate": "AND",
        "children": [
            {"id": "2.1", "type": "basic_event", "label": "Firmware Crash"},
            {"id": "2.2", "type": "basic_event", "label": "Controller Fault"},
        ],
    },
    {
        "id": "3",
        "type": "intermediate_event",
        "label": "Start Signal Issue",
        "gate": "OR",
        "children": [
            {"id": "3.1", "type": "basic_event", "label": "Start Button Failure"},
            {"id": "3.2", "type": "basic_event", "label": "Signal Line Disconnected"},
            {"id": "3.3", "type": "basic_event", "label": "Sensor Fault"},
        ],
    },
]


@dataclass
class FaultNode:
    id: str
    kind: str
    label: str
    label_zh: str = ""
    gate: str = "OR"
    children: list["FaultNode"] = field(default_factory=list)


@dataclass
class LayoutNode:
    node: FaultNode
    depth: int
    width: int
    height: int
    subtree_width: float
    x: float = 0
    y: float = 0
    children: list["LayoutNode"] = field(default_factory=list)


def render_fault_tree_to_file(data: dict[str, Any], output_path: Path) -> dict[str, Any]:
    normalized = normalize_input(data)
    svg = render_fault_tree(normalized)
    validate_svg(svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "path": str(output_path),
        "format": "svg",
        "diagram_type": "fault_tree",
        "theme": normalized["theme"],
        "diagnostics": normalized["diagnostics"],
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    diagram_type = canonical_diagram_type(data.get("diagram_type", "fault_tree"))
    if diagram_type != "fault_tree":
        raise ValueError('Fault tree renderer requires diagram_type="fault_tree".')

    output = clean_text(data.get("output", "svg")).lower() or "svg"
    if output != "svg":
        raise ValueError("The fault_tree renderer outputs SVG only.")

    diagnostics = list(data.get("_diagnostics", [])) if isinstance(data.get("_diagnostics"), list) else []
    title = clean_text(data.get("title", "Fault Tree Analysis")) or "Fault Tree Analysis"
    title_zh = clean_text(data.get("title_zh", ""))
    subtitle = clean_text(data.get("subtitle", ""))
    subtitle_zh = clean_text(data.get("subtitle_zh", ""))
    show_legend = as_bool(data.get("show_legend", True))
    layout_mode = clean_text(data.get("layout_mode", "review_compact")).lower().replace("-", "_") or "review_compact"
    if layout_mode not in {"review_compact", "wide_tree"}:
        diagnostics.append(f"Unsupported layout_mode '{layout_mode}'; review_compact was used.")
        layout_mode = "review_compact"

    top_event_raw = data.get("top_event", {})
    if not isinstance(top_event_raw, dict):
        top_event_raw = {"label": top_event_raw}
    top_label = clean_text(
        top_event_raw.get("label")
        or top_event_raw.get("name")
        or top_event_raw.get("title")
        or data.get("topic")
        or "Top Event"
    )
    top_label_zh = clean_text(top_event_raw.get("label_zh", ""))
    top_id = clean_text(top_event_raw.get("id", "T0")) or "T0"
    event_detail = normalize_event_detail(data.get("event_detail"), top_event_raw)

    tree_raw = data.get("tree", {})
    if not isinstance(tree_raw, dict):
        tree_raw = {}
    root_gate = normalize_gate(
        tree_raw.get("gate", data.get("gate", top_event_raw.get("gate", "OR"))),
        diagnostics,
        "top event",
    )
    first_level_raw = tree_raw.get("children", data.get("children", []))
    if not isinstance(first_level_raw, list) or not first_level_raw:
        diagnostics.append("No fault-tree children were provided; default example events were used.")
        first_level_raw = DEFAULT_TREE

    children = normalize_children(
        first_level_raw,
        diagnostics,
        parent_label=top_label,
        depth=1,
        limit=MAX_FIRST_LEVEL_EVENTS,
    )
    root = FaultNode(
        id=top_id,
        kind="top_event",
        label=top_label,
        label_zh=top_label_zh,
        gate=root_gate,
        children=children,
    )

    return {
        "diagram_type": "fault_tree",
        "title": title,
        "title_zh": title_zh,
        "subtitle": subtitle,
        "subtitle_zh": subtitle_zh,
        "output": "svg",
        "theme": clean_text(data.get("theme", data.get("style", "business_simple"))) or "business_simple",
        "show_legend": show_legend,
        "layout_mode": layout_mode,
        "event_detail": event_detail,
        "root": root,
        "diagnostics": diagnostics,
    }


def normalize_event_detail(raw_detail: Any, top_event_raw: dict[str, Any]) -> dict[str, Any]:
    fallback_description = clean_text(
        top_event_raw.get("description")
        or top_event_raw.get("detail")
        or top_event_raw.get("event_detail")
        or ""
    )
    if raw_detail is None:
        raw_detail = {}

    if isinstance(raw_detail, str):
        text = clean_text(raw_detail)
        return {"title": "Event Detail", "text": text, "bullets": []} if text else (
            {"title": "Event Detail", "text": fallback_description, "bullets": []} if fallback_description else {}
        )

    if not isinstance(raw_detail, dict):
        return {"title": "Event Detail", "text": fallback_description, "bullets": []} if fallback_description else {}

    title = clean_text(raw_detail.get("title", "Event Detail")) or "Event Detail"
    text = clean_text(raw_detail.get("text") or raw_detail.get("description") or fallback_description)
    raw_bullets = raw_detail.get("bullets", [])
    bullets: list[str] = []
    if isinstance(raw_bullets, list):
        bullets = [clean_text(item) for item in raw_bullets if clean_text(item)]
    elif clean_text(raw_bullets):
        bullets = [clean_text(raw_bullets)]

    if not text and not bullets:
        return {}
    return {"title": title, "text": text, "bullets": bullets}


def normalize_children(
    raw_children: list[Any],
    diagnostics: list[str],
    *,
    parent_label: str,
    depth: int,
    limit: int,
) -> list[FaultNode]:
    children: list[FaultNode] = []
    if len(raw_children) > limit:
        diagnostics.append(
            f"Event '{parent_label}' has {len(raw_children)} children; only the first {limit} are rendered."
        )

    for index, raw_child in enumerate(raw_children[:limit], start=1):
        child = normalize_node(raw_child, diagnostics, depth=depth, index=index)
        if child is not None:
            children.append(child)
    return children


def normalize_node(raw: Any, diagnostics: list[str], *, depth: int, index: int) -> FaultNode | None:
    if isinstance(raw, str):
        label = clean_text(raw)
        if not label:
            return None
        return FaultNode(id=str(index), kind="basic_event", label=label)

    if not isinstance(raw, dict):
        diagnostics.append(f"Ignored fault-tree event #{index}: expected text or object.")
        return None

    label = clean_text(raw.get("label") or raw.get("name") or raw.get("title") or raw.get("text") or "")
    label_zh = clean_text(raw.get("label_zh", ""))
    if not label and label_zh:
        label = label_zh
    if not label:
        diagnostics.append(f"Ignored fault-tree event #{index}: missing label.")
        return None

    raw_children = raw.get("children", [])
    if not isinstance(raw_children, list):
        diagnostics.append(f"Event '{label}' has non-list children; using no child events.")
        raw_children = []

    raw_kind = clean_text(raw.get("type", "")).lower().replace("-", "_").replace(" ", "_")
    if raw_kind not in {"intermediate_event", "basic_event"}:
        raw_kind = "intermediate_event" if raw_children and depth < MAX_DEPTH else "basic_event"
    if depth == 1:
        raw_kind = "intermediate_event"
    if depth >= MAX_DEPTH:
        raw_kind = "basic_event"

    gate = normalize_gate(raw.get("gate", "OR"), diagnostics, label)
    node = FaultNode(
        id=clean_text(raw.get("id", str(index))) or str(index),
        kind=raw_kind,
        label=label,
        label_zh=label_zh,
        gate=gate,
    )

    if raw_children and raw_kind == "basic_event":
        diagnostics.append(f"Nested children under basic event '{label}' are not rendered in the MVP.")
    elif raw_children:
        node.children = normalize_children(
            raw_children,
            diagnostics,
            parent_label=label,
            depth=depth + 1,
            limit=MAX_CHILDREN_PER_EVENT,
        )

    return node


def parse_fault_tree_markdown(text: str) -> dict[str, Any]:
    metadata, body = split_front_matter(text)
    title = metadata.get("title", "Fault Tree Analysis")
    subtitle = metadata.get("subtitle", "")
    show_legend = metadata.get("show_legend", "true")
    diagnostics: list[str] = []

    top_label = metadata.get("top_event", "")
    root_gate = metadata.get("gate", "OR")
    children: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    nested: dict[str, Any] | None = None
    context: str = "metadata"
    event_detail: dict[str, Any] = {"title": "Event Detail", "text": "", "bullets": []}
    event_detail_lines: list[str] = []

    for raw_line in body.splitlines():
        raw_line = raw_line.rstrip()
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue

        key_value = parse_key_value(line)
        if key_value is not None:
            key, value = key_value
            if key == "diagram_type":
                continue
            if key == "gate":
                if nested is not None and context == "nested":
                    nested["gate"] = value
                elif current is not None and context == "intermediate":
                    current["gate"] = value
                else:
                    root_gate = value
                continue
            if key in {"event_detail", "event_description", "description"}:
                event_detail["text"] = value
                context = "event_detail"
                current = None
                nested = None
                continue
            if key in {"title", "subtitle", "show_legend"}:
                metadata[key] = value
                continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            if not heading:
                continue
            if level == 1:
                top_label = normalize_top_heading(heading)
                current = None
                nested = None
                context = "root"
            elif level == 2:
                current = {
                    "id": str(len(children) + 1),
                    "type": "intermediate_event",
                    "label": heading,
                    "children": [],
                }
                children.append(current)
                nested = None
                context = "intermediate"
            elif level == 3 and current is not None:
                nested = {
                    "id": f"{len(children)}.{len(current['children']) + 1}",
                    "type": "intermediate_event",
                    "label": heading,
                    "children": [],
                }
                current["children"].append(nested)
                context = "nested"
            continue

        if re.match(r"^event\s+detail\s*[:：]\s*$", line, flags=re.I):
            context = "event_detail"
            current = None
            nested = None
            continue

        bullet = parse_bullet(raw_line)
        if bullet is not None:
            indent_level, bullet_text = bullet
            if context == "event_detail":
                event_detail["bullets"].append(bullet_text)
                continue
            if current is None:
                diagnostics.append(f"Ignored bullet '{bullet_text}': no intermediate event appears before it.")
                continue
            target = nested if nested is not None and (context == "nested" or indent_level > 0) else current
            target["children"].append(
                {
                    "id": f"{target.get('id', 'E')}.{len(target['children']) + 1}",
                    "type": "basic_event",
                    "label": bullet_text,
                }
            )
            continue

        if context == "event_detail":
            event_detail_lines.append(line)
            continue

        diagnostics.append(f"Ignored unrecognized fault-tree line: '{line}'.")

    if not top_label:
        top_label = "Top Event"
        diagnostics.append("No top event heading was provided; 'Top Event' was used.")

    if event_detail_lines and not event_detail["text"]:
        event_detail["text"] = " ".join(event_detail_lines)
    if not event_detail["text"] and not event_detail["bullets"]:
        event_detail = {}

    return {
        "diagram_type": "fault_tree",
        "title": metadata.get("title", title),
        "subtitle": metadata.get("subtitle", subtitle),
        "show_legend": as_bool(metadata.get("show_legend", show_legend)),
        "output": "svg",
        "theme": metadata.get("theme", "business_simple"),
        "top_event": {"id": "T0", "label": top_label},
        "event_detail": event_detail,
        "tree": {"gate": root_gate, "children": children},
        "_diagnostics": diagnostics,
    }


def render_fault_tree(data: dict[str, Any]) -> str:
    root_layout = build_layout_tree(data["root"], 0)
    if data["layout_mode"] == "wide_tree":
        canvas_width = round_up(max(WIDTH, math.ceil(root_layout.subtree_width + SIDE_MARGIN * 2)), CANVAS_WIDTH_STEP)
        assign_positions(root_layout, (canvas_width - root_layout.subtree_width) / 2, 0)
    else:
        canvas_width = compact_canvas_width(root_layout)
        assign_compact_positions(root_layout, canvas_width)
    _min_x, _max_x, _min_y, max_y = layout_bounds(root_layout)
    canvas_height = round_up(max(HEIGHT, math.ceil(max_y + CANVAS_BOTTOM_MARGIN)), CANVAS_HEIGHT_STEP)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" role="img" aria-label="{xml(data["root"].label)}">',
        render_defs(),
        f'<rect x="0" y="0" width="{canvas_width}" height="{canvas_height}" fill="{PALETTE["background"]}"/>',
        render_background_decorations(canvas_width, canvas_height),
    ]
    if data.get("event_detail"):
        parts.append(render_event_detail_panel(data))
    else:
        parts.append(render_title(data))
    if data["show_legend"]:
        parts.append(render_legend(canvas_width))
    if data["layout_mode"] == "review_compact":
        parts.append(render_compact_connectors(root_layout))
    else:
        parts.append(render_connectors(root_layout))
    parts.append(render_nodes(root_layout))
    parts.append("</svg>")

    if canvas_width != WIDTH or canvas_height != HEIGHT:
        data["diagnostics"].append(f"Canvas expanded to {canvas_width}x{canvas_height} to fit the fault tree.")

    return "\n".join(part for part in parts if part)


def build_layout_tree(node: FaultNode, depth: int) -> LayoutNode:
    width, height = node_size(node, depth)
    layout = LayoutNode(node=node, depth=depth, width=width, height=height, subtree_width=width)
    if depth >= MAX_DEPTH or not node.children:
        return layout

    layout.children = [build_layout_tree(child, depth + 1) for child in node.children]
    child_total = sum(child.subtree_width for child in layout.children)
    child_total += SUBTREE_GAP * max(0, len(layout.children) - 1)
    layout.subtree_width = max(width, child_total)
    return layout


def assign_positions(layout: LayoutNode, left: float, depth: int, y: float | None = None) -> None:
    layout.x = left + layout.subtree_width / 2
    layout.y = LEVEL_Y[min(depth, len(LEVEL_Y) - 1)] if y is None else y
    if not layout.children:
        return

    child_total = sum(child.subtree_width for child in layout.children)
    child_total += SUBTREE_GAP * max(0, len(layout.children) - 1)
    child_left = left + (layout.subtree_width - child_total) / 2
    child_y = layout.y + layout.height + PARENT_CHILD_GAP
    for child in layout.children:
        assign_positions(child, child_left, depth + 1, child_y)
        child_left += child.subtree_width + SUBTREE_GAP


def layout_bounds(layout: LayoutNode) -> tuple[float, float, float, float]:
    min_x = layout.x - layout.width / 2
    max_x = layout.x + layout.width / 2
    min_y = layout.y
    max_y = layout.y + layout.height
    for child in layout.children:
        child_min_x, child_max_x, child_min_y, child_max_y = layout_bounds(child)
        min_x = min(min_x, child_min_x)
        max_x = max(max_x, child_max_x)
        min_y = min(min_y, child_min_y)
        max_y = max(max_y, child_max_y)
    return min_x, max_x, min_y, max_y


def assign_compact_positions(layout: LayoutNode, canvas_width: int) -> None:
    layout.x = canvas_width / 2
    layout.y = LEVEL_Y[0]
    if not layout.children:
        return

    columns = layout.children
    column_extents = [compact_extents(child) for child in columns]
    column_widths = [left + right for left, right in column_extents]
    total_width = sum(column_widths) + COMPACT_COLUMN_GAP * max(0, len(columns) - 1)
    left = max(SIDE_MARGIN, (canvas_width - total_width) / 2)
    first_branch_y = layout.y + layout.height + PARENT_CHILD_GAP
    for child, (left_extent, _right_extent), column_width in zip(columns, column_extents, column_widths):
        center_x = left + left_extent
        assign_compact_branch(child, center_x, first_branch_y)
        left += column_width + COMPACT_COLUMN_GAP


def compact_canvas_width(layout: LayoutNode) -> int:
    if not layout.children:
        return WIDTH
    column_widths = [compact_column_width(child) for child in layout.children]
    total_width = sum(column_widths) + COMPACT_COLUMN_GAP * max(0, len(column_widths) - 1)
    return round_up(max(WIDTH, math.ceil(total_width + SIDE_MARGIN * 2)), CANVAS_WIDTH_STEP)


def compact_column_width(layout: LayoutNode) -> float:
    left, right = compact_extents(layout)
    return left + right


def compact_extents(layout: LayoutNode) -> tuple[float, float]:
    left = layout.width / 2
    right = layout.width / 2
    for child in layout.children:
        child_left, child_right = compact_extents(child)
        child_center_offset = -(COMPACT_BRANCH_GAP + child.width / 2)
        left = max(left, -child_center_offset + child_left)
        right = max(right, child_center_offset + child_right)
    return left, right


def assign_compact_branch(layout: LayoutNode, center_x: float, y: float) -> float:
    layout.x = center_x
    layout.y = y
    if not layout.children:
        return y + layout.height

    child_y = y + layout.height + PARENT_CHILD_GAP
    for child in layout.children:
        child_x = center_x - COMPACT_BRANCH_GAP - child.width / 2
        child_bottom = assign_compact_branch(child, child_x, child_y)
        child_y = child_bottom + COMPACT_CHILD_GAP
    return max(y + layout.height, child_y - COMPACT_CHILD_GAP)


def node_size(node: FaultNode, depth: int) -> tuple[int, int]:
    if depth == 0 or node.kind == "top_event":
        return top_event_size(node)
    if node.kind == "basic_event" or not node.children:
        return basic_event_size(node)
    return intermediate_event_size(node)


def top_event_size(node: FaultNode) -> tuple[int, int]:
    text = join_bilingual(node.label, node.label_zh)
    text_width = TOP_EVENT_W - TOP_EVENT_TEXT_PADDING_X - 20
    char_limit = chars_for_width(text_width, 24, latin_factor=0.55, minimum=8)
    line_count = len(wrap_label(text, char_limit, None))
    height = max(TOP_EVENT_H, TOP_EVENT_TEXT_PADDING_Y * 2 + line_count * (24 + 4))
    return TOP_EVENT_W, height


def intermediate_event_size(node: FaultNode) -> tuple[int, int]:
    text = join_bilingual(node.label, node.label_zh)
    text_width = INTERMEDIATE_W - INTERMEDIATE_TEXT_PADDING_X * 2
    char_limit = chars_for_width(text_width, 18, latin_factor=0.55, minimum=8)
    line_count = len(wrap_label(text, char_limit, None))
    height = max(INTERMEDIATE_H, INTERMEDIATE_TEXT_PADDING_Y * 2 + line_count * (18 + 4))
    return INTERMEDIATE_W, height


def basic_event_size(node: FaultNode) -> tuple[int, int]:
    text = join_bilingual(node.label, node.label_zh)
    estimated = estimate_text_width(text, 15) + BASIC_TEXT_PADDING_X * 2
    width = round_up(max(BASIC_W, min(BASIC_MAX_W, math.ceil(estimated))), 10)
    text_width = width - BASIC_TEXT_PADDING_X * 2
    char_limit = chars_for_width(text_width, 15, latin_factor=0.55, minimum=8)
    line_count = len(wrap_label(text, char_limit, None))
    height = max(BASIC_H, BASIC_TEXT_PADDING_Y * 2 + line_count * 19)
    return width, height


def render_defs() -> str:
    return "\n".join(
        [
            "<defs>",
            '<filter id="faultSoftShadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#16324F" flood-opacity="0.10"/>',
            "</filter>",
            "</defs>",
        ]
    )


def render_background_decorations(canvas_width: int, canvas_height: int) -> str:
    return "\n".join(
        [
            render_dot_grid(canvas_width - 230, 20, 8, 4),
            render_dot_grid(24, canvas_height - 120, 7, 4),
            render_circuit(canvas_width - 330, canvas_height - 88, flip=True),
        ]
    )


def render_dot_grid(x: int, y: int, cols: int, rows: int) -> str:
    dots = []
    for row in range(rows):
        for col in range(cols):
            dots.append(
                f'<circle cx="{x + col * 24}" cy="{y + row * 24}" r="3.2" fill="{PALETTE["decor"]}" opacity="0.55"/>'
            )
    return "\n".join(dots)


def render_circuit(x: int, y: int, *, flip: bool) -> str:
    sign = -1 if flip else 1
    color = PALETTE["decor"]
    return "\n".join(
        [
            f'<line x1="{x}" y1="{y}" x2="{x + sign * 155}" y2="{y}" stroke="{color}" stroke-width="2" opacity="0.55"/>',
            f'<polyline points="{x + sign * 82},{y} {x + sign * 112},{y - 30} {x + sign * 175},{y - 30}" fill="none" stroke="{color}" stroke-width="2" opacity="0.55"/>',
            f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" opacity="0.55"/>',
            f'<circle cx="{x + sign * 155}" cy="{y}" r="5" fill="none" stroke="{color}" stroke-width="2" opacity="0.55"/>',
            f'<circle cx="{x + sign * 175}" cy="{y - 30}" r="5" fill="{color}" opacity="0.55"/>',
        ]
    )


def render_title(data: dict[str, Any]) -> str:
    title = data["title"]
    title_zh = data.get("title_zh", "")
    subtitle = data["subtitle"]
    subtitle_zh = data.get("subtitle_zh", "")
    title_text = join_bilingual(title, title_zh)
    subtitle_text = join_bilingual(subtitle, subtitle_zh)
    parts = [
        f'<text x="60" y="70" font-family="{FONT_STACK}" font-size="42" font-weight="700" fill="{PALETTE["navy"]}">{xml(truncate(title_text, 45))}</text>',
    ]
    if subtitle_text:
        parts.append(
            f'<text x="62" y="112" font-family="{FONT_STACK}" font-size="25" font-weight="500" fill="{PALETTE["gray_text"]}">{xml(truncate(subtitle_text, 62))}</text>'
        )
    parts.append(f'<line x1="62" y1="132" x2="520" y2="132" stroke="{PALETTE["light_gray"]}" stroke-width="2"/>')
    return "\n".join(parts)


def render_event_detail_panel(data: dict[str, Any]) -> str:
    detail = data.get("event_detail") or {}
    title = clean_text(detail.get("title", "Event Detail")) or "Event Detail"
    text = clean_text(detail.get("text", ""))
    bullets = detail.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = []

    x = 60
    y = 52
    w = 610
    padding = 24
    title_size = 22
    body_size = 17
    line_gap = 23
    body_width = w - padding * 2
    body_char_limit = chars_for_width(body_width, body_size, latin_factor=0.54, minimum=18)

    visible_lines: list[tuple[str, bool]] = []
    for line in wrap_label(text, body_char_limit, 3) if text else []:
        visible_lines.append((line, False))
    for bullet in bullets:
        for index, line in enumerate(wrap_label(clean_text(bullet), body_char_limit - 3, 2)):
            visible_lines.append((line if index else f"- {line}", index > 0))

    max_lines_by_height = max(1, int((EVENT_DETAIL_MAX_H - 100) / line_gap))
    max_visible_lines = min(EVENT_DETAIL_MAX_LINES, max_lines_by_height)
    truncated = len(visible_lines) > max_visible_lines
    if truncated:
        visible_lines = visible_lines[:max_visible_lines]
        last_line, is_continuation = visible_lines[-1]
        visible_lines[-1] = (truncate(last_line, max(12, body_char_limit - 1)), is_continuation)
        data["diagnostics"].append("Event detail text was truncated to fit the left panel.")

    h = min(EVENT_DETAIL_MAX_H, 80 + max(1, len(visible_lines)) * line_gap + 20)
    parts = [
        f'<g id="fault-event-detail-panel" class="fault-event-detail-panel">',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#FFFFFF" stroke="{PALETTE["line_blue"]}" stroke-width="1.8" filter="url(#faultSoftShadow)"/>',
        f'<text x="{x + padding}" y="{y + 38}" font-family="{FONT_STACK}" font-size="{title_size}" font-weight="700" fill="{PALETTE["navy"]}">{xml(truncate(title, 42))}</text>',
        f'<line x1="{x + padding}" y1="{y + 56}" x2="{x + w - padding}" y2="{y + 56}" stroke="{PALETTE["light_gray"]}" stroke-width="2"/>',
    ]

    current_y = y + 86
    if visible_lines:
        for line, is_continuation in visible_lines:
            text_x = x + padding + (14 if is_continuation else 0)
            parts.append(
                f'<text x="{text_x}" y="{current_y}" font-family="{FONT_STACK}" font-size="{body_size}" font-weight="500" fill="{PALETTE["gray_text"]}">{xml(line)}</text>'
            )
            current_y += line_gap
    else:
        parts.append(
            f'<text x="{x + padding}" y="{current_y}" font-family="{FONT_STACK}" font-size="{body_size}" font-weight="500" fill="{PALETTE["gray_text"]}">No detail provided.</text>'
        )

    parts.append("</g>")
    return "\n".join(parts)


def render_legend(canvas_width: int) -> str:
    rows = [
        ("OR", "OR Gate"),
        ("AND", "AND Gate"),
        ("BASIC", "Basic Event"),
    ]
    padding_x = 24
    padding_top = 24
    padding_bottom = 18
    title_height = 24
    title_gap = 24
    row_gap = 42
    symbol_col_w = 46
    symbol_text_gap = 24
    font_size = 17
    label_w = max(estimate_text_width(label, font_size) for _, label in rows)
    legend_w = max(300, padding_x * 2 + symbol_col_w + symbol_text_gap + label_w)
    legend_h = padding_top + title_height + title_gap + row_gap * len(rows) + padding_bottom - 8
    x = canvas_width - legend_w - 70
    y = 52
    label_x = x + padding_x + symbol_col_w + symbol_text_gap
    row_start_y = y + padding_top + title_height + title_gap
    return "\n".join(
        [
            f'<g id="fault-tree-legend" class="fault-tree-legend">',
            f'<rect x="{x:.1f}" y="{y}" width="{legend_w:.1f}" height="{legend_h:.1f}" rx="12" fill="#FFFFFF" stroke="{PALETTE["border_gray"]}" stroke-width="1.5" stroke-dasharray="6 4"/>',
            f'<text x="{x + 24}" y="{y + 34}" font-family="{FONT_STACK}" font-size="20" font-weight="700" fill="{PALETTE["navy"]}">Legend</text>',
            render_gate("OR", x + padding_x + symbol_col_w / 2, row_start_y, scale=0.58),
            f'<text x="{label_x:.1f}" y="{row_start_y + 7:.1f}" font-family="{FONT_STACK}" font-size="{font_size}" font-weight="600" fill="{PALETTE["navy"]}">OR Gate</text>',
            render_gate("AND", x + padding_x + symbol_col_w / 2, row_start_y + row_gap, scale=0.58),
            f'<text x="{label_x:.1f}" y="{row_start_y + row_gap + 7:.1f}" font-family="{FONT_STACK}" font-size="{font_size}" font-weight="600" fill="{PALETTE["navy"]}">AND Gate</text>',
            f'<rect x="{x + padding_x + 4:.1f}" y="{row_start_y + row_gap * 2 - 15:.1f}" width="38" height="30" rx="7" fill="#FFFFFF" stroke="{PALETTE["line_blue"]}" stroke-width="1.5"/>',
            f'<text x="{label_x:.1f}" y="{row_start_y + row_gap * 2 + 7:.1f}" font-family="{FONT_STACK}" font-size="{font_size}" font-weight="600" fill="{PALETTE["navy"]}">Basic Event</text>',
            "</g>",
        ]
    )


def render_connectors(layout: LayoutNode) -> str:
    parts: list[str] = []
    if layout.children:
        gate_y = gate_center_y(layout)
        bus_y = min(child.y for child in layout.children) - 32
        parent_bottom = layout.y + layout.height
        parts.append(
            f'<line x1="{layout.x:.1f}" y1="{parent_bottom:.1f}" x2="{layout.x:.1f}" y2="{gate_y - 24:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
        )
        parts.append(render_gate(layout.node.gate, layout.x, gate_y))
        parts.append(
            f'<line x1="{layout.x:.1f}" y1="{gate_y + 24:.1f}" x2="{layout.x:.1f}" y2="{bus_y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
        )
        first_x = min(child.x for child in layout.children)
        last_x = max(child.x for child in layout.children)
        if len(layout.children) > 1:
            parts.append(
                f'<line x1="{first_x:.1f}" y1="{bus_y:.1f}" x2="{last_x:.1f}" y2="{bus_y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
            )
        for child in layout.children:
            parts.append(
                f'<line x1="{child.x:.1f}" y1="{bus_y:.1f}" x2="{child.x:.1f}" y2="{child.y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
            )
    for child in layout.children:
        parts.append(render_connectors(child))
    return "\n".join(part for part in parts if part)


def render_compact_connectors(layout: LayoutNode) -> str:
    if not layout.children:
        return ""
    if layout.depth == 0:
        parts = [render_top_bus_connectors(layout)]
    else:
        parts = [render_branch_trunk_connectors(layout)]
    for child in layout.children:
        parts.append(render_compact_connectors(child))
    return "\n".join(part for part in parts if part)


def render_top_bus_connectors(layout: LayoutNode) -> str:
    if not layout.children:
        return ""
    gate_y = gate_center_y(layout)
    bus_y = min(child.y for child in layout.children) - 32
    parent_bottom = layout.y + layout.height
    first_x = min(child.x for child in layout.children)
    last_x = max(child.x for child in layout.children)
    parts = [
        f'<line x1="{layout.x:.1f}" y1="{parent_bottom:.1f}" x2="{layout.x:.1f}" y2="{gate_y - 24:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>',
        render_gate(layout.node.gate, layout.x, gate_y),
        f'<line x1="{layout.x:.1f}" y1="{gate_y + 24:.1f}" x2="{layout.x:.1f}" y2="{bus_y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>',
    ]
    if len(layout.children) > 1:
        parts.append(
            f'<line x1="{first_x:.1f}" y1="{bus_y:.1f}" x2="{last_x:.1f}" y2="{bus_y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
        )
    for child in layout.children:
        parts.append(
            f'<line x1="{child.x:.1f}" y1="{bus_y:.1f}" x2="{child.x:.1f}" y2="{child.y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
        )
    return "\n".join(parts)


def render_branch_trunk_connectors(layout: LayoutNode) -> str:
    if not layout.children:
        return ""
    gate_y = gate_center_y(layout)
    parent_bottom = layout.y + layout.height
    child_midpoints = [child.y + child.height / 2 for child in layout.children]
    trunk_bottom = max(child_midpoints)
    parts = [
        f'<line x1="{layout.x:.1f}" y1="{parent_bottom:.1f}" x2="{layout.x:.1f}" y2="{gate_y - 24:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>',
        render_gate(layout.node.gate, layout.x, gate_y),
        f'<line class="fault-branch-trunk" x1="{layout.x:.1f}" y1="{gate_y + 24:.1f}" x2="{layout.x:.1f}" y2="{trunk_bottom:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>',
    ]
    for child, child_mid_y in zip(layout.children, child_midpoints):
        child_right_x = child.x + child.width / 2
        parts.append(
            f'<line class="fault-branch-line" x1="{layout.x:.1f}" y1="{child_mid_y:.1f}" x2="{child_right_x:.1f}" y2="{child_mid_y:.1f}" stroke="{PALETTE["blue"]}" stroke-width="2.2" stroke-linecap="round"/>'
        )
    return "\n".join(parts)


def render_nodes(layout: LayoutNode) -> str:
    parts = [render_node(layout)]
    for child in layout.children:
        parts.append(render_nodes(child))
    return "\n".join(parts)


def render_node(layout: LayoutNode) -> str:
    node = layout.node
    x = layout.x - layout.width / 2
    y = layout.y
    if node.kind == "top_event":
        lines = [
            f'<g class="fault-event fault-top-event">',
            f'<rect id="top-event-block" x="{x:.1f}" y="{y:.1f}" width="{layout.width}" height="{layout.height}" rx="15" fill="{PALETTE["navy"]}" filter="url(#faultSoftShadow)"/>',
            render_warning_icon(layout.x - layout.width / 2 + 36, y + 38),
        ]
        lines.extend(render_centered_text(node, layout.x + 22, y + layout.height / 2, layout.width - 72, 24, "#FFFFFF", None, bold=True))
        lines.append("</g>")
        return "\n".join(lines)

    if node.kind == "basic_event" or not node.children:
        fill = "#FFFFFF"
        stroke = PALETTE["line_blue"]
        text_size = 15
        class_name = "fault-event fault-basic-event"
        label_y = y + layout.height / 2 + 3
    else:
        fill = PALETTE["pale_blue"]
        stroke = PALETTE["blue"]
        text_size = 18
        class_name = "fault-event fault-intermediate-event"
        label_y = y + layout.height / 2

    lines = [
        f'<g class="{class_name}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{layout.width}" height="{layout.height}" rx="11" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>',
    ]
    text_width = layout.width - (BASIC_TEXT_PADDING_X * 2 if node.kind == "basic_event" or not node.children else 20)
    lines.extend(render_centered_text(node, layout.x, label_y, text_width, text_size, PALETTE["navy"], None, bold=node.kind != "basic_event"))
    lines.append("</g>")
    return "\n".join(lines)


def render_centered_text(
    node: FaultNode,
    cx: float,
    y: float,
    width: float,
    font_size: int,
    color: str,
    max_lines: int | None,
    *,
    bold: bool,
) -> list[str]:
    text = join_bilingual(node.label, node.label_zh)
    char_limit = chars_for_width(width, font_size, latin_factor=0.55, minimum=8)
    lines = wrap_label(text, char_limit, max_lines)
    line_height = font_size + 4
    visual_height = len(lines) * line_height
    start_y = y - visual_height / 2 + font_size * 0.78
    weight = "700" if bold else "600"
    return [
        f'<text x="{cx:.1f}" y="{start_y + i * line_height:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{font_size}" font-weight="{weight}" fill="{color}">{xml(line)}</text>'
        for i, line in enumerate(lines)
    ]


def estimate_text_width(text: str, font_size: int) -> float:
    return measure_text_width(text, font_size)


def render_gate(gate: str, cx: float, cy: float, *, scale: float = 1.0) -> str:
    normalized = gate if gate in {"AND", "OR"} else "OR"
    gate_class = "fault-gate-and" if normalized == "AND" else "fault-gate-or"
    rx = 34 * scale
    ry = 24 * scale
    if normalized == "AND":
        fill = PALETTE["light_blue"]
        stroke = PALETTE["blue"]
        text_fill = PALETTE["navy"]
        shape = (
            f'<path d="M {cx - rx:.1f} {cy + ry:.1f} L {cx - rx:.1f} {cy:.1f} '
            f'C {cx - rx:.1f} {cy - ry:.1f} {cx + rx:.1f} {cy - ry:.1f} {cx + rx:.1f} {cy:.1f} '
            f'L {cx + rx:.1f} {cy + ry:.1f} Z" fill="{fill}" stroke="{stroke}" stroke-width="{1.5 * scale:.1f}"/>'
        )
    else:
        fill = PALETTE["navy"]
        text_fill = "#FFFFFF"
        shape = (
            f'<path d="M {cx - rx:.1f} {cy + ry:.1f} '
            f'C {cx - rx * 0.56:.1f} {cy - ry:.1f} {cx + rx * 0.56:.1f} {cy - ry:.1f} {cx + rx:.1f} {cy + ry:.1f} '
            f'C {cx + rx * 0.40:.1f} {cy + ry * 0.48:.1f} {cx - rx * 0.40:.1f} {cy + ry * 0.48:.1f} {cx - rx:.1f} {cy + ry:.1f} Z" fill="{fill}"/>'
        )
    return "\n".join(
        [
            f'<g class="fault-gate {gate_class}" data-gate="{normalized}">',
            shape,
            f'<text x="{cx:.1f}" y="{cy + 8 * scale:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{15 * scale:.1f}" font-weight="700" fill="{text_fill}">{normalized}</text>',
            "</g>",
        ]
    )


def render_warning_icon(cx: float, cy: float) -> str:
    return "\n".join(
        [
            f'<path d="M {cx:.1f} {cy - 19:.1f} L {cx + 22:.1f} {cy + 19:.1f} L {cx - 22:.1f} {cy + 19:.1f} Z" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linejoin="round" opacity="0.92"/>',
            f'<line x1="{cx:.1f}" y1="{cy - 6:.1f}" x2="{cx:.1f}" y2="{cy + 7:.1f}" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>',
            f'<circle cx="{cx:.1f}" cy="{cy + 14:.1f}" r="2.6" fill="#FFFFFF"/>',
        ]
    )


def gate_center_y(layout: LayoutNode) -> float:
    if not layout.children:
        return layout.y + layout.height + 46
    child_top = min(child.y for child in layout.children)
    return layout.y + layout.height + (child_top - (layout.y + layout.height)) * 0.43


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    clean = text.lstrip("\ufeff")
    lines = clean.splitlines()
    metadata: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                for raw in lines[1:index]:
                    parsed = parse_key_value(raw.strip())
                    if parsed is not None:
                        metadata[parsed[0]] = parsed[1]
                return metadata, "\n".join(lines[index + 1 :])
    return metadata, clean


def parse_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)
    if not match:
        return None
    key = match.group(1).strip().lower().replace("-", "_")
    value = match.group(2).strip().strip("\"'")
    return key, value


def parse_bullet(line: str) -> tuple[int, str] | None:
    expanded = line.replace("\t", "    ")
    match = re.match(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.+)$", expanded)
    if not match:
        return None
    indent = len(match.group(1))
    level = 0 if indent == 0 else 1
    return level, match.group(2).strip()


def normalize_top_heading(text: str) -> str:
    return re.sub(r"^(?:top event|event|topic|problem)[:：]\s*", "", text.strip(), flags=re.I)


def normalize_gate(value: Any, diagnostics: list[str], context: str) -> str:
    gate = clean_text(value).upper().replace("-", "_").replace(" ", "_")
    if gate in {"AND", "OR"}:
        return gate
    if not gate:
        return "OR"
    diagnostics.append(f"Event '{context}' uses unsupported gate '{gate}'; OR was used.")
    return "OR"


def canonical_diagram_type(value: Any) -> str:
    return clean_text(value).lower().replace("-", "_").replace(" ", "_")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = clean_text(value).lower()
    return text not in {"false", "0", "no", "off"}


def join_bilingual(primary: str, secondary: str) -> str:
    if secondary and secondary != primary:
        return f"{primary} / {secondary}" if primary else secondary
    return primary


def clean_text(value: Any) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()).strip()


def wrap_label(text: str, limit: int, max_lines: int | None) -> list[str]:
    return wrap_text(text, limit, max_lines)


def truncate(text: str, limit: int) -> str:
    return truncate_text(text, limit)


def round_up(value: int, step: int) -> int:
    return int(math.ceil(value / step) * step)


def xml(value: Any) -> str:
    return escape(str(value), {'"': "&quot;"})


def validate_svg(svg: str) -> None:
    root = ElementTree.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("Generated SVG root is invalid.")

    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "top-event-block"]
    if len(top_blocks) != 1:
        raise ValueError("Fault tree SVG must contain exactly one top-event-block.")
    top_block = top_blocks[0]
    if not top_block.tag.endswith("rect") or not top_block.attrib.get("rx"):
        raise ValueError("Top event block must be a rounded rect.")

    gates = [
        element
        for element in root.iter()
        if "fault-gate" in element.attrib.get("class", "")
    ]
    if not gates:
        raise ValueError("Fault tree SVG must contain at least one gate.")
