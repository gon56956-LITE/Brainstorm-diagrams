"""Business-simple fishbone SVG renderer."""

from __future__ import annotations

import math
import re
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from renderers.text_utils import estimate_text_width, truncate_text, visual_len, wrap_text

WIDTH = 1920
HEIGHT = 1080
FONT_STACK = "Arial, Helvetica, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
ROOT = Path(__file__).resolve().parents[2]
LUCIDE_ICON_DIR = ROOT / "assets" / "lucide-candidates"
LUCIDE_ICON_CACHE: dict[str, str] = {}

SPINE_Y = 540
SPINE_START_X = 214
SPINE_END_X = 1530
PROBLEM_X = 1550
PROBLEM_Y = 360
PROBLEM_W = 280
PROBLEM_H = 330
CARD_W = 286
CARD_H = 88
TOP_CARD_Y = 132
BOTTOM_CARD_Y = 860
BRANCH_ANGLE_DEG = 75
STANDARD_BRANCH_LENGTH = 230
MEDIUM_BRANCH_LENGTH = 270
SHORT_BRANCH_LENGTH = 180
CHILD_ROW_GAP = 20
ROW_EDGE_PADDING = 38
MIN_ROW_CENTER_GAP = 36
ROW_CLEARANCE = 10
LAYOUT_LEFT_SAFE_X = 260
LAYOUT_RIGHT_SAFE_X = 1480
COLUMN_MIN_X = 430
COLUMN_MAX_X = 1325
ROW_MIN_GAP = 36
RIGHT_MARGIN = 90
TOPIC_CONTENT_GAP = 90
SPINE_TOPIC_GAP = 24
CANVAS_WIDTH_STEP = 80
CANVAS_HEIGHT_STEP = 60
CANVAS_TOP_MARGIN = 70
CANVAS_BOTTOM_MARGIN = 70

PALETTE = {
    "background": "#FFFFFF",
    "navy": "#0B3A75",
    "navy_2": "#174B86",
    "blue": "#1E5AA8",
    "soft_blue": "#BFD5EB",
    "light_blue": "#D9E8F7",
    "pale_blue": "#EEF6FE",
    "line_blue": "#6E93BD",
    "gray": "#7A8797",
    "light_gray": "#D6DEE8",
    "text": "#16324F",
    "muted_text": "#52677A",
    "decor": "#BCD2EA",
}

ACCENTS = ["#0B5CAD", "#168DAA", "#315B93", "#4B9B6A", "#476C9B", "#5C7FA3", "#7E5AC8", "#C75C5C"]
MAX_CATEGORIES = 8
MIN_CATEGORIES = 4
MAX_ENTRIES_PER_CATEGORY = 5
MAX_CHILDREN_PER_SUBCATEGORY = 3

DEFAULT_CATEGORIES = [
    {"name_en": "People", "name_zh": "人员", "items": []},
    {"name_en": "Process", "name_zh": "流程", "items": []},
    {"name_en": "Tools", "name_zh": "工具", "items": []},
    {"name_en": "Environment", "name_zh": "环境", "items": []},
    {"name_en": "Methods", "name_zh": "方法", "items": []},
    {"name_en": "Materials", "name_zh": "材料", "items": []},
]

ICON_ALIASES = {
    "people": "people",
    "person": "people",
    "operator": "people",
    "operators": "people",
    "personnel": "people",
    "staff": "people",
    "人员": "people",
    "人": "people",
    "人员与操作": "people",
    "操作": "people",
    "user": "people",
    "user needs": "people",
    "needs": "people",
    "process": "process",
    "system": "lucide:workflow",
    "workflow": "lucide:workflow",
    "architecture": "lucide:network",
    "system architecture": "lucide:network",
    "functions": "layers",
    "function": "layers",
    "features": "layers",
    "feature": "layers",
    "optical": "lucide:aperture",
    "optical design": "lucide:aperture",
    "thermal": "lucide:thermometer",
    "thermal design": "lucide:thermometer",
    "electrical": "lucide:circuit-board",
    "electrical design": "lucide:circuit-board",
    "mechanical": "lucide:cog",
    "mechanical design": "lucide:cog",
    "assembly": "lucide:wrench",
    "manufacturing": "lucide:wrench",
    "manufacturing assembly": "lucide:wrench",
    "manufacturing & assembly": "lucide:wrench",
    "manufacturing and assembly": "lucide:wrench",
    "performance": "gauge",
    "speed": "gauge",
    "capacity": "gauge",
    "reliability": "lucide:shield-check",
    "reliability field use": "lucide:shield-check",
    "field use": "lucide:map-pin",
    "quality": "shield",
    "robustness": "shield",
    "test/measurement": "lucide:gauge",
    "test and measurement": "lucide:gauge",
    "verification": "lucide:chart-line",
    "dvt": "lucide:chart-line",
    "svt": "lucide:chart-line",
    "evt": "lucide:chart-line",
    "edvt": "lucide:chart-line",
    "cost": "lucide:circle-dollar-sign",
    "costs": "lucide:circle-dollar-sign",
    "price": "lucide:circle-dollar-sign",
    "budget": "lucide:circle-dollar-sign",
    "business": "lucide:chart-no-axes-column-increasing",
    "tools": "tools",
    "tool": "tools",
    "equipment": "tools",
    "machine": "tools",
    "machines": "tools",
    "fixture": "tools",
    "fixtures": "tools",
    "jig": "tools",
    "jigs": "tools",
    "设备": "tools",
    "治具": "tools",
    "机": "tools",
    "设备与治具": "tools",
    "environment": "environment",
    "环境": "environment",
    "环": "environment",
    "环境与物流": "environment",
    "物流": "environment",
    "methods": "methods",
    "method": "methods",
    "process method": "methods",
    "工艺": "methods",
    "方法": "methods",
    "法": "methods",
    "工艺与方法": "methods",
    "materials": "lucide:boxes",
    "material": "lucide:boxes",
    "supply": "lucide:boxes",
    "supplier": "lucide:boxes",
    "材料": "materials",
    "物料": "materials",
    "供应": "materials",
    "料": "materials",
    "材料与供应": "materials",
    "factory": "lucide:wrench",
    "testing": "lucide:gauge",
    "test": "lucide:gauge",
    "measurement": "lucide:gauge",
    "measure": "lucide:gauge",
    "测试": "gauge",
    "测量": "gauge",
    "判定": "gauge",
    "测": "gauge",
    "测试与判定": "gauge",
}


@dataclass
class FishboneEntry:
    kind: str
    text: str
    children: list[str]


@dataclass
class Category:
    name_en: str
    name_zh: str
    items: list[FishboneEntry]


@dataclass
class CategoryLayout:
    category: Category
    category_index: int
    x: int
    top: bool
    start_side: str


@dataclass
class RenderLayout:
    width: int
    height: int
    spine_y: int
    spine_start_x: int
    spine_end_x: int
    problem_x: int
    problem_y: int
    layout_left_safe_x: int
    layout_right_safe_x: int
    column_min_x: int
    column_max_x: int


def render_fishbone_to_file(data: dict[str, Any], output_path: Path) -> dict[str, str]:
    normalized = normalize_input(data)
    svg = render_fishbone(normalized)
    validate_svg(svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "path": str(output_path),
        "format": "svg",
        "diagram_type": "fishbone",
        "theme": normalized["theme"],
        "diagnostics": normalized["diagnostics"],
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    diagram_type = str(data.get("diagram_type", "fishbone")).strip().lower() or "fishbone"
    if diagram_type != "fishbone":
        raise ValueError(
            'This version of brainstorm-diagrams supports only diagram_type="fishbone". '
            "The requested diagram type can be added in a future version."
        )

    output = str(data.get("output", "svg")).strip().lower() or "svg"
    if output != "svg":
        raise ValueError("The renderer outputs SVG only. Render SVG first, then use scripts/export_png.py for PNG.")

    language = str(data.get("language", "as_written")).strip().lower() or "as_written"
    if language not in {"bilingual", "english", "chinese"}:
        language = "as_written"

    diagnostics = list(data.get("_diagnostics", [])) if isinstance(data.get("_diagnostics"), list) else []
    if clean_text(data.get("topic_zh", "")):
        diagnostics.append("Legacy field 'topic_zh' is accepted for compatibility but is not rendered automatically.")
    if language != "as_written":
        diagnostics.append("Legacy field 'language' is accepted for compatibility; text is rendered as supplied.")
    categories = normalize_categories(data.get("categories"), diagnostics)

    return {
        "diagram_type": "fishbone",
        "title": clean_text(data.get("title", "")),
        "topic": clean_text(data.get("topic", "Problem / Topic")),
        "topic_zh": clean_text(data.get("topic_zh", "")),
        "subtitle": clean_text(data.get("subtitle", "")),
        "language": language,
        "output": "svg",
        "theme": clean_text(data.get("theme", "business_simple")) or "business_simple",
        "categories": categories,
        "diagnostics": diagnostics,
    }


def normalize_categories(raw_categories: Any, diagnostics: list[str]) -> list[Category]:
    categories: list[Category] = []

    if isinstance(raw_categories, list):
        original_count = len(raw_categories)
        for raw_index, raw in enumerate(raw_categories, start=1):
            if not isinstance(raw, dict):
                diagnostics.append(f"Ignored category #{raw_index}: expected an object.")
                continue
            name_en = clean_text(raw.get("name_en") or raw.get("name") or raw.get("title") or "")
            name_zh = clean_text(raw.get("name_zh", ""))
            if not name_en and name_zh:
                name_en = name_zh
            elif name_zh:
                diagnostics.append(f"Legacy field 'name_zh' in category '{name_en}' is accepted but is not rendered as a second label.")
            if not name_en:
                diagnostics.append(f"Ignored category #{raw_index}: missing name.")
                continue
            items = raw.get("items", [])
            if not isinstance(items, list):
                diagnostics.append(f"Category '{name_en}' has non-list items; using an empty item list.")
                items = []
            normalized_items = normalize_entries(items, name_en, diagnostics)
            categories.append(
                Category(
                    name_en=name_en,
                    name_zh=name_zh,
                    items=normalized_items,
                )
            )
        if original_count > MAX_CATEGORIES:
            diagnostics.append(f"Input provided {original_count} categories; only the first {MAX_CATEGORIES} valid categories are rendered.")

    if not categories:
        diagnostics.append("No categories were provided; default six categories were used.")
        categories = [Category(item["name_en"], item["name_zh"], []) for item in DEFAULT_CATEGORIES]

    default_index = 0
    existing = {category.name_en.lower() for category in categories}
    original_valid_count = len(categories)
    while len(categories) < MIN_CATEGORIES:
        default = DEFAULT_CATEGORIES[default_index % len(DEFAULT_CATEGORIES)]
        default_index += 1
        if default["name_en"].lower() in existing:
            continue
        categories.append(Category(default["name_en"], default["name_zh"], []))
        existing.add(default["name_en"].lower())
    if original_valid_count < MIN_CATEGORIES:
        diagnostics.append(f"Only {original_valid_count} valid categories were provided; default categories were added to reach {MIN_CATEGORIES}.")

    return categories[:MAX_CATEGORIES]


def normalize_entries(raw_items: list[Any], category_name: str, diagnostics: list[str]) -> list[FishboneEntry]:
    entries: list[FishboneEntry] = []
    for item_index, raw_item in enumerate(raw_items, start=1):
        if isinstance(raw_item, str):
            text = clean_text(raw_item)
            if text:
                entries.append(FishboneEntry(kind="cause", text=text, children=[]))
            continue

        if isinstance(raw_item, dict):
            subcategory = clean_text(raw_item.get("subcategory", ""))
            if subcategory:
                children_raw = raw_item.get("items", [])
                if not isinstance(children_raw, list):
                    diagnostics.append(f"Subcategory '{subcategory}' in '{category_name}' has non-list items; using an empty child list.")
                    children_raw = []
                clean_children = [clean_text(child) for child in children_raw if isinstance(child, str) and clean_text(child)]
                if len(clean_children) > MAX_CHILDREN_PER_SUBCATEGORY:
                    diagnostics.append(
                        f"Subcategory '{subcategory}' in '{category_name}' has {len(clean_children)} child items; only the first {MAX_CHILDREN_PER_SUBCATEGORY} are rendered."
                    )
                entries.append(FishboneEntry(kind="subcategory", text=subcategory, children=clean_children[:MAX_CHILDREN_PER_SUBCATEGORY]))
                continue

            text = clean_text(raw_item.get("text") or raw_item.get("name") or raw_item.get("title") or "")
            if text:
                child_source = raw_item.get("children", [])
                if isinstance(child_source, list) and child_source:
                    clean_children = [clean_text(child) for child in child_source if isinstance(child, str) and clean_text(child)]
                    if len(clean_children) > MAX_CHILDREN_PER_SUBCATEGORY:
                        diagnostics.append(
                            f"Entry '{text}' in '{category_name}' has {len(clean_children)} child items; only the first {MAX_CHILDREN_PER_SUBCATEGORY} are rendered as a subcategory."
                        )
                    entries.append(FishboneEntry(kind="subcategory", text=text, children=clean_children[:MAX_CHILDREN_PER_SUBCATEGORY]))
                else:
                    entries.append(FishboneEntry(kind="cause", text=text, children=[]))
                continue

        diagnostics.append(f"Ignored item #{item_index} in category '{category_name}': expected text or subcategory object.")

    if len(entries) > MAX_ENTRIES_PER_CATEGORY:
        diagnostics.append(f"Category '{category_name}' has {len(entries)} primary entries; only the first {MAX_ENTRIES_PER_CATEGORY} are rendered.")

    return entries[:MAX_ENTRIES_PER_CATEGORY]


def clean_text(value: Any) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split()).strip()


def render_fishbone(data: dict[str, Any]) -> str:
    categories: list[Category] = data["categories"]
    render_layout, top_layouts, bottom_layouts = plan_render_layout(categories)
    if (render_layout.width, render_layout.height) != (WIDTH, HEIGHT):
        data["diagnostics"].append(
            f"Canvas expanded to {render_layout.width}x{render_layout.height} to fit dense content."
        )

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{render_layout.width}" height="{render_layout.height}" viewBox="0 0 {render_layout.width} {render_layout.height}" role="img" aria-label="{xml(data["topic"])}">',
        render_defs(),
        f'<rect x="0" y="0" width="{render_layout.width}" height="{render_layout.height}" fill="{PALETTE["background"]}"/>',
        render_background_decorations(render_layout),
        render_title(data),
        render_chevrons(render_layout),
        render_spine(render_layout),
    ]

    for layout in top_layouts:
        parts.append(render_branch(layout, render_layout))

    for layout in bottom_layouts:
        parts.append(render_branch(layout, render_layout))

    parts.append(render_topic_block(data, render_layout))
    parts.append("</svg>")
    return "\n".join(parts)


def render_defs() -> str:
    return "\n".join(
        [
            "<defs>",
            '<linearGradient id="topCardGradient" x1="0" y1="0" x2="1" y2="1">',
            '<stop offset="0%" stop-color="#0B3A75"/>',
            '<stop offset="100%" stop-color="#1F5A98"/>',
            "</linearGradient>",
            '<linearGradient id="bottomCardGradient" x1="0" y1="0" x2="1" y2="1">',
            '<stop offset="0%" stop-color="#DDECF9"/>',
            '<stop offset="100%" stop-color="#BCD5ED"/>',
            "</linearGradient>",
            '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="0" dy="7" stdDeviation="8" flood-color="#16324F" flood-opacity="0.12"/>',
            "</filter>",
            "</defs>",
        ]
    )


def render_background_decorations(layout: RenderLayout) -> str:
    parts = [
        render_dot_grid(layout.width - 224, 16, 9, 4),
        render_dot_grid(layout.width - 160, layout.height - 232, 7, 5),
        render_dot_grid(16, layout.height - 98, 6, 4),
        render_circuit(layout.width - 310, 98, flip=False),
        render_circuit(layout.width - 390, layout.height - 80, flip=True),
    ]
    return "\n".join(parts)


def render_dot_grid(x: int, y: int, cols: int, rows: int) -> str:
    dots = []
    for row in range(rows):
        for col in range(cols):
            dots.append(
                f'<circle cx="{x + col * 24}" cy="{y + row * 24}" r="3.5" fill="{PALETTE["decor"]}" opacity="0.65"/>'
            )
    return "\n".join(dots)


def render_circuit(x: int, y: int, *, flip: bool) -> str:
    sign = -1 if flip else 1
    color = PALETTE["decor"]
    return "\n".join(
        [
            f'<line x1="{x}" y1="{y}" x2="{x + sign * 160}" y2="{y}" stroke="{color}" stroke-width="2" opacity="0.65"/>',
            f'<polyline points="{x + sign * 82},{y} {x + sign * 112},{y + 32} {x + sign * 178},{y + 32}" fill="none" stroke="{color}" stroke-width="2" opacity="0.65"/>',
            f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" opacity="0.65"/>',
            f'<circle cx="{x + sign * 160}" cy="{y}" r="5" fill="none" stroke="{color}" stroke-width="2" opacity="0.65"/>',
            f'<circle cx="{x + sign * 178}" cy="{y + 32}" r="5" fill="{color}" opacity="0.65"/>',
        ]
    )


def render_title(data: dict[str, Any]) -> str:
    title = data["title"]
    if not title:
        return ""
    return "\n".join(
        [
            f'<text x="92" y="64" font-family="{FONT_STACK}" font-size="22" font-weight="700" fill="{PALETTE["navy"]}" opacity="0.82">{xml(truncate(title, 42))}</text>',
            f'<line x1="92" y1="84" x2="380" y2="84" stroke="{PALETTE["light_gray"]}" stroke-width="2" opacity="0.55"/>',
        ]
    )


def render_chevrons(layout: RenderLayout) -> str:
    chevrons = []
    y = layout.spine_y
    for offset, color, width, opacity in [
        (0, PALETTE["navy"], 24, 0.98),
        (38, PALETTE["soft_blue"], 24, 0.94),
        (76, PALETTE["light_blue"], 24, 0.92),
    ]:
        x = 78 + offset
        chevrons.append(
            f'<polyline points="{x},{y - 48} {x + 42},{y} {x},{y + 48}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="butt" stroke-linejoin="miter" opacity="{opacity}"/>'
        )
    return "\n".join(chevrons)


def render_spine(layout: RenderLayout) -> str:
    return "\n".join(
        [
            f'<line x1="{layout.spine_start_x}" y1="{layout.spine_y}" x2="{layout.spine_end_x}" y2="{layout.spine_y}" stroke="{PALETTE["navy"]}" stroke-width="6" stroke-linecap="round"/>',
            f'<line x1="{layout.spine_end_x - 24}" y1="{layout.spine_y - 24}" x2="{layout.spine_end_x}" y2="{layout.spine_y}" stroke="{PALETTE["navy"]}" stroke-width="6" stroke-linecap="round"/>',
            f'<line x1="{layout.spine_end_x - 24}" y1="{layout.spine_y + 24}" x2="{layout.spine_end_x}" y2="{layout.spine_y}" stroke="{PALETTE["navy"]}" stroke-width="6" stroke-linecap="round"/>',
        ]
    )


def layout_categories(categories: list[Category]) -> tuple[list[CategoryLayout], list[CategoryLayout]]:
    _, top_layouts, bottom_layouts = plan_render_layout(categories)
    return top_layouts, bottom_layouts


def plan_render_layout(categories: list[Category]) -> tuple[RenderLayout, list[CategoryLayout], list[CategoryLayout]]:
    top_indices = choose_top_indices(categories)
    top_set = set(top_indices)
    top_categories = [(index, category) for index, category in enumerate(categories) if index in top_set]
    bottom_categories = [(index, category) for index, category in enumerate(categories) if index not in top_set]
    return place_category_columns(top_categories, bottom_categories)


def choose_top_indices(categories: list[Category]) -> tuple[int, ...]:
    top_count = (len(categories) + 1) // 2
    loads = [category_layout_load(category) for category in categories]
    best_indices: tuple[int, ...] | None = None
    best_score: tuple[float, float] | None = None
    simple_top = tuple(range(top_count))

    for candidate in combinations(range(len(categories)), top_count):
        top_load = sum(loads[index] for index in candidate)
        bottom_load = sum(loads) - top_load
        moved = sum(1 for index in candidate if index not in simple_top)
        score = (abs(top_load - bottom_load), moved * 0.01)
        if best_score is None or score < best_score:
            best_indices = candidate
            best_score = score

    return best_indices or simple_top


def category_layout_load(category: Category) -> float:
    subcategory_count = sum(1 for item in category.items if item.kind == "subcategory")
    child_count = sum(len(item.children) for item in category.items if item.kind == "subcategory")
    return required_branch_length(category.items) + subcategory_count * 90 + child_count * 18 + len(category.items) * 12


def build_render_layout(
    top_categories: list[tuple[int, Category]],
    bottom_categories: list[tuple[int, Category]],
    column_footprints: list[tuple[float, float]],
) -> RenderLayout:
    total_column_width = sum(left + right for left, right in column_footprints)
    total_gap = ROW_MIN_GAP * max(0, len(column_footprints) - 1)
    required_width = LAYOUT_LEFT_SAFE_X + total_column_width + total_gap + TOPIC_CONTENT_GAP + PROBLEM_W + RIGHT_MARGIN
    width = round_up(max(WIDTH, math.ceil(required_width)), CANVAS_WIDTH_STEP)

    problem_x = width - RIGHT_MARGIN - PROBLEM_W
    layout_right_safe_x = problem_x - TOPIC_CONTENT_GAP
    spine_end_x = problem_x - SPINE_TOPIC_GAP

    top_max = max([branch_length_for_category(category) for _, category in top_categories] or [MEDIUM_BRANCH_LENGTH])
    bottom_max = max([branch_length_for_category(category) for _, category in bottom_categories] or [MEDIUM_BRANCH_LENGTH])
    half_span = max(top_max, bottom_max)
    required_height = CANVAS_TOP_MARGIN + CARD_H + half_span * 2 + CARD_H + CANVAS_BOTTOM_MARGIN
    height = round_up(max(HEIGHT, math.ceil(required_height)), CANVAS_HEIGHT_STEP)
    spine_y = height // 2
    problem_y = round(spine_y - PROBLEM_H / 2)

    if column_footprints:
        first_left = column_footprints[0][0]
        last_right = column_footprints[-1][1]
    else:
        first_left = CARD_W / 2
        last_right = CARD_W / 2

    column_min_x = max(COLUMN_MIN_X, LAYOUT_LEFT_SAFE_X + first_left)
    if width > WIDTH:
        column_max_x = layout_right_safe_x - last_right
    else:
        column_max_x = min(COLUMN_MAX_X, layout_right_safe_x - last_right)
    if column_max_x < column_min_x:
        column_max_x = column_min_x

    return RenderLayout(
        width=width,
        height=height,
        spine_y=spine_y,
        spine_start_x=SPINE_START_X,
        spine_end_x=spine_end_x,
        problem_x=problem_x,
        problem_y=problem_y,
        layout_left_safe_x=LAYOUT_LEFT_SAFE_X,
        layout_right_safe_x=layout_right_safe_x,
        column_min_x=round(column_min_x),
        column_max_x=round(column_max_x),
    )


def round_up(value: int, step: int) -> int:
    return int(math.ceil(value / step) * step)


def place_category_columns(
    top_categories: list[tuple[int, Category]],
    bottom_categories: list[tuple[int, Category]],
) -> tuple[RenderLayout, list[CategoryLayout], list[CategoryLayout]]:
    column_count = max(len(top_categories), len(bottom_categories))
    if column_count == 0:
        render_layout = build_render_layout([], [], [])
        return render_layout, [], []

    top_starts = choose_column_start_sides(top_categories, column_count)
    bottom_starts = choose_column_start_sides(bottom_categories, column_count)
    top_footprints = [category_footprint(category, start) for (_, category), start in zip(top_categories, top_starts)]
    bottom_footprints = [category_footprint(category, start) for (_, category), start in zip(bottom_categories, bottom_starts)]

    column_footprints: list[tuple[float, float]] = []
    for column_index in range(column_count):
        candidates = []
        if column_index < len(top_footprints):
            candidates.append(top_footprints[column_index])
        if column_index < len(bottom_footprints):
            candidates.append(bottom_footprints[column_index])
        left = max(footprint[0] for footprint in candidates)
        right = max(footprint[1] for footprint in candidates)
        column_footprints.append((left, right))

    render_layout = build_render_layout(top_categories, bottom_categories, column_footprints)
    column_xs = shared_column_xs(column_footprints, render_layout)

    top_layouts = [
        CategoryLayout(category=category, category_index=category_index, x=column_xs[column_index], top=True, start_side=start_side)
        for column_index, ((category_index, category), start_side) in enumerate(zip(top_categories, top_starts))
    ]
    bottom_layouts = [
        CategoryLayout(category=category, category_index=category_index, x=column_xs[column_index], top=False, start_side=start_side)
        for column_index, ((category_index, category), start_side) in enumerate(zip(bottom_categories, bottom_starts))
    ]
    return render_layout, top_layouts, bottom_layouts


def choose_column_start_sides(indexed_categories: list[tuple[int, Category]], column_count: int) -> list[str]:
    starts: list[str] = []
    for column_index, (_, category) in enumerate(indexed_categories):
        if column_count == 1:
            starts.append(best_balanced_start_side(category))
        elif column_index == 0:
            starts.append(start_side_for_edge(category, prefer="right"))
        elif column_index == column_count - 1:
            starts.append(start_side_for_edge(category, prefer="left"))
        else:
            starts.append(best_balanced_start_side(category))
    return starts


def start_side_for_edge(category: Category, *, prefer: str) -> str:
    preferred = category_footprint(category, prefer)
    alternate_side = opposite_side(prefer)
    alternate = category_footprint(category, alternate_side)
    preferred_edge = preferred[0] if prefer == "right" else preferred[1]
    alternate_edge = alternate[0] if prefer == "right" else alternate[1]
    if preferred_edge <= alternate_edge + 80:
        return prefer
    return alternate_side


def best_balanced_start_side(category: Category) -> str:
    left_footprint = category_footprint(category, "left")
    right_footprint = category_footprint(category, "right")
    left_spread = max(left_footprint)
    right_spread = max(right_footprint)
    return "left" if left_spread < right_spread else "right"


def shared_column_xs(column_footprints: list[tuple[float, float]], layout: RenderLayout) -> list[int]:
    if len(column_footprints) == 1:
        left, right = column_footprints[0]
        x = max(layout.column_min_x, min(820, layout.layout_right_safe_x - right))
        x = max(x, layout.layout_left_safe_x + left)
        return [round(x)]

    positions = [
        layout.column_min_x + (layout.column_max_x - layout.column_min_x) * index / (len(column_footprints) - 1)
        for index in range(len(column_footprints))
    ]
    positions = enforce_column_constraints(positions, column_footprints, layout)
    return [round(position) for position in positions]


def enforce_column_constraints(positions: list[float], footprints: list[tuple[float, float]], layout: RenderLayout) -> list[float]:
    positions = positions[:]
    for index, (left, right) in enumerate(footprints):
        positions[index] = max(positions[index], layout.layout_left_safe_x + left)
        positions[index] = min(positions[index], layout.layout_right_safe_x - right)

    for index in range(1, len(positions)):
        previous_right = footprints[index - 1][1]
        current_left = footprints[index][0]
        positions[index] = max(positions[index], positions[index - 1] + previous_right + current_left + ROW_MIN_GAP)

    overflow = positions[-1] + footprints[-1][1] - layout.layout_right_safe_x
    if overflow > 0:
        for index in reversed(range(len(positions))):
            min_position = layout.layout_left_safe_x + footprints[index][0]
            if index > 0:
                min_position = max(min_position, positions[index - 1] + footprints[index - 1][1] + footprints[index][0] + ROW_MIN_GAP)
            shift = min(overflow, max(0, positions[index] - min_position))
            positions[index] -= shift
            overflow -= shift
            if overflow <= 0:
                break

    return positions


def category_footprint(category: Category, start_side: str) -> tuple[float, float]:
    left = CARD_W / 2
    right = CARD_W / 2
    ordered = category.items if category.items else [FishboneEntry(kind="cause", text="", children=[]) for _ in range(4)]
    for row, item in enumerate(ordered):
        width = item_horizontal_extent(item)
        if side_for_item(row, start_side) == "left":
            left = max(left, width)
        else:
            right = max(right, width)
    return left, right


def item_horizontal_extent(item: FishboneEntry) -> int:
    if item.kind == "subcategory" and item.text:
        title_lines = wrap_text(item.text, 16, 3)
        card_w = max(118, min(176, 42 + estimate_text_width(max(title_lines, key=visual_len), 15)))
        child_width = max([max(text_width(line, 13, 22) for line in wrap_text(child, 22, 2)) for child in item.children] or [0])
        return 56 + card_w + 18 + 24 + child_width + 18
    return 34 + 14 + text_width(item.text, 17, 22)


def text_width(text: str, font_size: int, limit: int) -> int:
    return round(estimate_text_width(truncate_text(text, limit), font_size))


def render_branch(category_layout: CategoryLayout, render_layout: RenderLayout) -> str:
    category = category_layout.category
    x = category_layout.x
    top = category_layout.top
    card_x = x - CARD_W // 2
    branch_length = branch_length_for_category(category, category_layout.start_side)
    card_y = render_layout.spine_y - CARD_H - branch_length if top else render_layout.spine_y + branch_length
    connector_end_y = card_y + CARD_H if top else card_y
    connector_dx = min(branch_dx(abs(render_layout.spine_y - connector_end_y)), CARD_W / 2 - 34)
    connector_end_x = x - connector_dx
    connector_stroke = PALETTE["navy"] if top else PALETTE["line_blue"]

    return "\n".join(
        [
            f'<line x1="{x}" y1="{render_layout.spine_y}" x2="{connector_end_x}" y2="{connector_end_y}" stroke="{connector_stroke}" stroke-width="2.6" stroke-linecap="round"/>',
            render_node(x, render_layout),
            render_category_card(category, category_layout.category_index, card_x, card_y, top=top),
            render_items(category.items, x, connector_end_x, connector_end_y, top=top, start_side=category_layout.start_side, spine_y=render_layout.spine_y),
        ]
    )


def render_node(x: int, layout: RenderLayout) -> str:
    return "\n".join(
        [
            f'<circle cx="{x}" cy="{layout.spine_y}" r="17" fill="{PALETTE["background"]}" stroke="{PALETTE["navy"]}" stroke-width="3"/>',
            f'<circle cx="{x}" cy="{layout.spine_y}" r="9" fill="{PALETTE["pale_blue"]}" stroke="{PALETTE["blue"]}" stroke-width="2"/>',
        ]
    )


def render_category_card(category: Category, category_index: int, x: int, y: int, *, top: bool) -> str:
    fill = "url(#topCardGradient)" if top else "url(#bottomCardGradient)"
    stroke = "none" if top else PALETTE["soft_blue"]
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{CARD_H}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1" filter="url(#softShadow)"/>',
            render_icon_badge(category, x + 48, y + CARD_H / 2, top=top),
            render_category_text(category, x + 102, y, top=top),
        ]
    )


def render_icon_badge(category: Category, cx: float, cy: float, *, top: bool) -> str:
    icon_name = icon_for_category(category)
    ring = PALETTE["light_blue"] if top else PALETTE["soft_blue"]
    return "\n".join(
        [
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="34" fill="#FFFFFF" stroke="{ring}" stroke-width="2"/>',
            render_icon(icon_name, cx, cy),
        ]
    )


def icon_for_category(category: Category) -> str:
    key = category.name_en.strip().lower()
    if not key:
        return "generic"
    if key in ICON_ALIASES:
        return ICON_ALIASES[key]
    for token in re.split(r"[\s/_&|,，、:：()（）-]+", key):
        if token in ICON_ALIASES:
            return ICON_ALIASES[token]
    for alias, icon_name in ICON_ALIASES.items():
        if contains_cjk(alias) and alias in key:
            return icon_name
    return "generic"


def render_icon(name: str, cx: float, cy: float) -> str:
    if name.startswith("lucide:"):
        return render_lucide_icon(name.removeprefix("lucide:"), cx, cy)
    color = PALETTE["blue"]
    x = cx
    y = cy
    if name == "people":
        return "\n".join(
            [
                f'<circle cx="{x:.0f}" cy="{y - 12:.0f}" r="8" fill="{color}"/>',
                f'<path d="M {x - 17:.0f} {y + 19:.0f} Q {x:.0f} {y - 2:.0f} {x + 17:.0f} {y + 19:.0f} Z" fill="{color}"/>',
            ]
        )
    if name == "process":
        return "\n".join(
            [
                f'<circle cx="{x:.0f}" cy="{y:.0f}" r="14" fill="none" stroke="{color}" stroke-width="5"/>',
                f'<line x1="{x:.0f}" y1="{y - 22:.0f}" x2="{x:.0f}" y2="{y - 14:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<line x1="{x:.0f}" y1="{y + 14:.0f}" x2="{x:.0f}" y2="{y + 22:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<line x1="{x - 22:.0f}" y1="{y:.0f}" x2="{x - 14:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<line x1="{x + 14:.0f}" y1="{y:.0f}" x2="{x + 22:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
            ]
        )
    if name == "tools":
        return "\n".join(
            [
                f'<line x1="{x - 16:.0f}" y1="{y - 16:.0f}" x2="{x + 16:.0f}" y2="{y + 16:.0f}" stroke="{color}" stroke-width="7" stroke-linecap="round"/>',
                f'<line x1="{x + 14:.0f}" y1="{y - 17:.0f}" x2="{x - 14:.0f}" y2="{y + 17:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<circle cx="{x - 18:.0f}" cy="{y - 18:.0f}" r="4" fill="{color}"/>',
            ]
        )
    if name == "layers":
        return "\n".join(
            [
                f'<rect x="{x - 18:.0f}" y="{y - 19:.0f}" width="28" height="22" rx="5" fill="none" stroke="{color}" stroke-width="4"/>',
                f'<rect x="{x - 10:.0f}" y="{y - 4:.0f}" width="28" height="22" rx="5" fill="none" stroke="{color}" stroke-width="4"/>',
            ]
        )
    if name == "gauge":
        return "\n".join(
            [
                f'<path d="M {x - 22:.0f} {y + 12:.0f} A 24 24 0 0 1 {x + 22:.0f} {y + 12:.0f}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<line x1="{x:.0f}" y1="{y + 8:.0f}" x2="{x + 14:.0f}" y2="{y - 8:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
                f'<circle cx="{x:.0f}" cy="{y + 10:.0f}" r="5" fill="{color}"/>',
            ]
        )
    if name == "shield":
        return "\n".join(
            [
                f'<path d="M {x:.0f} {y - 22:.0f} L {x + 20:.0f} {y - 12:.0f} L {x + 16:.0f} {y + 12:.0f} Q {x:.0f} {y + 24:.0f} {x - 16:.0f} {y + 12:.0f} L {x - 20:.0f} {y - 12:.0f} Z" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>',
                f'<polyline points="{x - 9:.0f},{y:.0f} {x - 1:.0f},{y + 8:.0f} {x + 12:.0f},{y - 8:.0f}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
            ]
        )
    if name == "coin":
        return "\n".join(
            [
                f'<circle cx="{x:.0f}" cy="{y:.0f}" r="22" fill="none" stroke="{color}" stroke-width="4"/>',
                f'<text x="{x:.0f}" y="{y + 9:.0f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="26" font-weight="700" fill="{color}">$</text>',
            ]
        )
    if name == "environment":
        return f'<path d="M {x + 14:.0f} {y - 20:.0f} C {x - 12:.0f} {y - 18:.0f} {x - 20:.0f} {y + 2:.0f} {x - 6:.0f} {y + 18:.0f} C {x + 10:.0f} {y + 6:.0f} {x + 18:.0f} {y - 8:.0f} {x + 14:.0f} {y - 20:.0f} Z M {x - 8:.0f} {y + 22:.0f} C {x - 2:.0f} {y + 2:.0f} {x + 8:.0f} {y - 8:.0f} {x + 16:.0f} {y - 16:.0f}" fill="{color}" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
    if name == "methods":
        return "\n".join(
            [
                f'<rect x="{x - 14:.0f}" y="{y - 18:.0f}" width="28" height="36" rx="3" fill="none" stroke="{color}" stroke-width="4"/>',
                f'<line x1="{x - 7:.0f}" y1="{y - 6:.0f}" x2="{x + 8:.0f}" y2="{y - 6:.0f}" stroke="{color}" stroke-width="3"/>',
                f'<line x1="{x - 7:.0f}" y1="{y + 4:.0f}" x2="{x + 8:.0f}" y2="{y + 4:.0f}" stroke="{color}" stroke-width="3"/>',
                f'<line x1="{x - 7:.0f}" y1="{y + 14:.0f}" x2="{x + 5:.0f}" y2="{y + 14:.0f}" stroke="{color}" stroke-width="3"/>',
            ]
        )
    if name == "materials":
        return "\n".join(
            [
                f'<polygon points="{x:.0f},{y - 20:.0f} {x + 18:.0f},{y - 10:.0f} {x + 18:.0f},{y + 10:.0f} {x:.0f},{y + 20:.0f} {x - 18:.0f},{y + 10:.0f} {x - 18:.0f},{y - 10:.0f}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>',
                f'<line x1="{x - 18:.0f}" y1="{y - 10:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="3"/>',
                f'<line x1="{x + 18:.0f}" y1="{y - 10:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{color}" stroke-width="3"/>',
                f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y + 20:.0f}" stroke="{color}" stroke-width="3"/>',
            ]
        )
    return "\n".join(
        [
            f'<rect x="{x - 15:.0f}" y="{y - 15:.0f}" width="30" height="30" rx="6" fill="none" stroke="{color}" stroke-width="4"/>',
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{color}"/>',
        ]
    )


def render_lucide_icon(name: str, cx: float, cy: float) -> str:
    inner = lucide_inner_svg(name)
    if not inner:
        return render_icon("generic", cx, cy)
    scale = 2.05
    x = cx - 12 * scale
    y = cy - 12 * scale
    return (
        f'<g class="lucide-icon" transform="translate({x:.1f} {y:.1f}) scale({scale:.2f})" '
        f'fill="none" stroke="{PALETTE["blue"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</g>"
    )


def lucide_inner_svg(name: str) -> str:
    if name in LUCIDE_ICON_CACHE:
        return LUCIDE_ICON_CACHE[name]
    path = LUCIDE_ICON_DIR / f"{name}.svg"
    if not path.exists():
        LUCIDE_ICON_CACHE[name] = ""
        return ""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^.*?<svg\b[^>]*>", "", text, flags=re.S)
    text = re.sub(r"</svg>\s*$", "", text, flags=re.S)
    LUCIDE_ICON_CACHE[name] = text.strip()
    return LUCIDE_ICON_CACHE[name]


def render_category_text(category: Category, x: int, y: int, *, top: bool) -> str:
    primary = category.name_en or category.name_zh
    fill_primary = "#FFFFFF" if top else PALETTE["navy"]
    lines = wrap_category_label(primary)
    primary_size = category_label_font_size(lines)
    line_gap = primary_size + 4
    start_y = y + 46 - (len(lines) - 1) * line_gap / 2

    return "\n".join(
        f'<text x="{x}" y="{start_y + index * line_gap:.0f}" font-family="{FONT_STACK}" font-size="{primary_size}" font-weight="700" fill="{fill_primary}">{xml(line)}</text>'
        for index, line in enumerate(lines)
    )


def wrap_category_label(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return [""]
    if visual_len(text) <= 12:
        return [text]
    if any(separator in text for separator in [" ", "/", "&", "|", "-", "、", "，"]):
        return wrap_label(text, 12, 2)
    lines = wrap_text(text, 12, 2)
    if len(lines) == 1:
        split_at = math.ceil(len(text) / 2)
        lines = [text[:split_at], text[split_at:]]
    if visual_len(lines[1]) > 12:
        lines[1] = truncate(lines[1], 12)
    return lines


def category_label_font_size(lines: list[str]) -> int:
    longest = max((visual_len(line) for line in lines), default=0)
    if len(lines) > 1:
        if longest > 10:
            return 18
        return 20
    if longest > 15:
        return 21
    if longest > 12:
        return 23
    return 26


def render_items(items: list[FishboneEntry], node_x: int, connector_x: int, connector_y: int, *, top: bool, start_side: str, spine_y: int) -> str:
    lines = []
    ordered = items if items else [FishboneEntry(kind="cause", text="", children=[]) for _ in range(4)]
    row_centers = row_center_offsets(ordered, start_side)
    segment_top = min(connector_y, spine_y)
    segment_bottom = max(connector_y, spine_y)
    usable_top = segment_top + ROW_EDGE_PADDING
    usable_bottom = segment_bottom - ROW_EDGE_PADDING
    group_top = -item_top_extent(ordered[0])
    group_bottom = row_centers[-1] + item_bottom_extent(ordered[-1])
    group_height = group_bottom - group_top
    start_y = (segment_top + segment_bottom - group_height) / 2 - group_top
    start_y = max(usable_top - group_top, min(start_y, usable_bottom - group_bottom))

    for row, item in enumerate(ordered):
        yy = round(start_y + row_centers[row])
        branch_x_at_y = interpolate_x(node_x, spine_y, connector_x, connector_y, yy)
        side = side_for_item(row, start_side)
        if item.kind == "subcategory" and item.text:
            lines.append(render_subcategory_entry(item, branch_x_at_y, yy, side=side))
        else:
            lines.append(render_cause_entry(item.text, branch_x_at_y, yy, side=side))
    return "\n".join(lines)


def render_cause_entry(text: str, anchor_x: int, yy: int, *, side: str) -> str:
    connector_len = 34
    if side == "right":
        line_x2 = anchor_x + connector_len
        text_x = line_x2 + 14
        anchor = "start"
        placeholder_x1 = text_x
        placeholder_x2 = text_x + 190
    else:
        line_x2 = anchor_x - connector_len
        text_x = line_x2 - 14
        anchor = "end"
        placeholder_x1 = text_x - 190
        placeholder_x2 = text_x
    parts = [
        f'<line x1="{anchor_x}" y1="{yy - 6}" x2="{line_x2}" y2="{yy - 6}" stroke="{PALETTE["line_blue"]}" stroke-width="2" stroke-linecap="round"/>',
        f'<circle cx="{anchor_x}" cy="{yy - 6}" r="7" fill="{PALETTE["background"]}" stroke="{PALETTE["blue"]}" stroke-width="3"/>',
    ]
    if text:
        for line_index, line in enumerate(wrap_text(text, 22, 2)):
            parts.append(f'<text x="{text_x}" y="{yy + line_index * 18 - (9 if line_index == 0 and visual_len(text) > 22 else 0)}" text-anchor="{anchor}" font-family="{FONT_STACK}" font-size="17" fill="{PALETTE["text"]}">{xml(line)}</text>')
    else:
        parts.append(f'<line x1="{placeholder_x1}" y1="{yy - 6}" x2="{placeholder_x2}" y2="{yy - 6}" stroke="{PALETTE["light_gray"]}" stroke-width="2"/>')
    return "\n".join(parts)


def render_subcategory_entry(entry: FishboneEntry, anchor_x: int, yy: int, *, side: str) -> str:
    title_lines = wrap_text(entry.text, 16, 3)
    card_w = max(118, min(176, 42 + estimate_text_width(max(title_lines, key=visual_len), 15)))
    card_h = 34 + (len(title_lines) - 1) * 16
    child_lines = [wrap_text(child, 22, 2) for child in entry.children]
    child_row_heights = [len(lines) * 14 for lines in child_lines]
    child_row_gap = 8
    child_block_h = sum(child_row_heights) + max(0, len(child_row_heights) - 1) * child_row_gap
    connection_len = 56
    if side == "right":
        card_x = anchor_x + connection_len
        text_x = card_x + 14
        text_anchor = "start"
        line_x2 = card_x
        brace_x = card_x + card_w + 18
        child_text_x = brace_x + 24
        child_anchor = "start"
        child_circle_x = brace_x + 10
    else:
        card_x = anchor_x - connection_len - card_w
        text_x = card_x + card_w - 14
        text_anchor = "end"
        line_x2 = card_x + card_w
        brace_x = card_x - 18
        child_text_x = brace_x - 24
        child_anchor = "end"
        child_circle_x = brace_x - 10
    card_y = yy - 25
    child_top_y = card_y + card_h / 2 - child_block_h / 2
    parts = [
        f'<line x1="{anchor_x}" y1="{yy - 6}" x2="{line_x2}" y2="{yy - 6}" stroke="{PALETTE["line_blue"]}" stroke-width="2" stroke-linecap="round"/>',
        f'<circle cx="{anchor_x}" cy="{yy - 6}" r="8" fill="{PALETTE["background"]}" stroke="{PALETTE["blue"]}" stroke-width="3"/>',
        f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="8" fill="#F8FBFF" stroke="{PALETTE["soft_blue"]}" stroke-width="2"/>',
    ]
    title_start_y = card_y + 22 - (len(title_lines) - 1) * 2
    for line_index, line in enumerate(title_lines):
        parts.append(f'<text x="{text_x}" y="{title_start_y + line_index * 16}" text-anchor="{text_anchor}" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="{PALETTE["navy"]}">{xml(line)}</text>')
    if entry.children:
        parts.append(render_child_brace(brace_x, card_y + card_h / 2, len(entry.children), side=side, height=child_block_h))
    cursor_y = child_top_y
    for child_index, lines in enumerate(child_lines):
        child_y = cursor_y + 13
        parts.append(f'<circle cx="{child_circle_x}" cy="{child_y - 5}" r="4.5" fill="{PALETTE["background"]}" stroke="{PALETTE["gray"]}" stroke-width="1.6"/>')
        for line_index, line in enumerate(lines):
            parts.append(f'<text x="{child_text_x}" y="{child_y + line_index * 14}" text-anchor="{child_anchor}" font-family="{FONT_STACK}" font-size="13" fill="{PALETTE["muted_text"]}">{xml(line)}</text>')
        cursor_y += child_row_heights[child_index] + child_row_gap
    return "\n".join(parts)


def branch_length_for_category(category: Category, start_side: str | None = None) -> int:
    has_subcategory = any(item.kind == "subcategory" for item in category.items)
    if start_side is None:
        required_length = max(required_branch_length(category.items, "right"), required_branch_length(category.items, "left"))
    else:
        required_length = required_branch_length(category.items, start_side)
    if has_subcategory:
        return max(MEDIUM_BRANCH_LENGTH, required_length)
    if len(category.items) <= 2:
        return max(SHORT_BRANCH_LENGTH, required_length)
    return max(STANDARD_BRANCH_LENGTH, required_length)


def required_branch_length(items: list[FishboneEntry], start_side: str = "right") -> int:
    ordered = items if items else [FishboneEntry(kind="cause", text="", children=[]) for _ in range(4)]
    centers = row_center_offsets(ordered, start_side)
    visual_height = item_top_extent(ordered[0]) + centers[-1] + item_bottom_extent(ordered[-1])
    return math.ceil(visual_height + ROW_EDGE_PADDING * 2)


def row_center_offsets(items: list[FishboneEntry], start_side: str = "right") -> list[float]:
    offsets = [0.0]
    last_by_side: dict[str, tuple[float, FishboneEntry]] = {side_for_item(0, start_side): (0.0, items[0])}
    for index, current in enumerate(items[1:], start=1):
        side = side_for_item(index, start_side)
        next_offset = offsets[-1] + MIN_ROW_CENTER_GAP
        if side in last_by_side:
            previous_center, previous = last_by_side[side]
            next_offset = max(next_offset, previous_center + item_bottom_extent(previous) + item_top_extent(current) + ROW_CLEARANCE)
        offsets.append(next_offset)
        last_by_side[side] = (next_offset, current)
    return offsets


def item_visual_height(item: FishboneEntry) -> int:
    return item_top_extent(item) + item_bottom_extent(item)


def item_top_extent(item: FishboneEntry) -> int:
    if item.kind == "subcategory" and item.text:
        title_extra = max(0, len(wrap_text(item.text, 16, 3)) - 1) * 8
        child_block_h = subcategory_child_block_height(item)
        return math.ceil(max(25, 8 + title_extra + child_block_h / 2))
    return 30 if len(wrap_text(item.text, 22, 2)) > 1 else 20


def item_bottom_extent(item: FishboneEntry) -> int:
    if item.kind == "subcategory" and item.text:
        title_extra = max(0, len(wrap_text(item.text, 16, 3)) - 1) * 8
        child_block_h = subcategory_child_block_height(item)
        return math.ceil(max(9, title_extra + child_block_h / 2 - 8))
    return 16 if len(wrap_text(item.text, 22, 2)) > 1 else 8


def subcategory_child_block_height(item: FishboneEntry) -> int:
    if not item.children:
        return 34
    line_counts = [len(wrap_text(child, 22, 2)) for child in item.children]
    return sum(count * 14 for count in line_counts) + max(0, len(line_counts) - 1) * 8


def side_for_item(row: int, start_side: str) -> str:
    return start_side if row % 2 == 0 else opposite_side(start_side)


def opposite_side(side: str) -> str:
    return "left" if side == "right" else "right"


def render_child_brace(x: float, center_y: float, child_count: int, *, side: str, height: float | None = None) -> str:
    height_by_count = {1: 24, 2: 44, 3: 62}
    height = max(height_by_count.get(child_count, 62), height or 0)
    top = center_y - height / 2
    bottom = center_y + height / 2
    mid = center_y
    sign = 1 if side == "right" else -1
    end_x = x + sign * 11
    body_x = x + sign * 1
    cusp_x = x - sign * 11
    d = (
        f"M {end_x:.1f} {top:.1f} "
        f"C {body_x:.1f} {top:.1f} {body_x:.1f} {top + 5:.1f} {body_x:.1f} {top + 11:.1f} "
        f"L {body_x:.1f} {mid - 8:.1f} "
        f"C {body_x:.1f} {mid - 3:.1f} {cusp_x:.1f} {mid - 3:.1f} {cusp_x:.1f} {mid:.1f} "
        f"C {cusp_x:.1f} {mid + 3:.1f} {body_x:.1f} {mid + 3:.1f} {body_x:.1f} {mid + 8:.1f} "
        f"L {body_x:.1f} {bottom - 11:.1f} "
        f"C {body_x:.1f} {bottom - 5:.1f} {body_x:.1f} {bottom:.1f} {end_x:.1f} {bottom:.1f}"
    )
    return f'<path class="child-curly-brace" d="{d}" fill="none" stroke="{PALETTE["line_blue"]}" stroke-width="2" stroke-linecap="round"/>'


def render_topic_block(data: dict[str, Any], layout: RenderLayout) -> str:
    x = layout.problem_x
    y = layout.problem_y
    w = PROBLEM_W
    h = PROBLEM_H
    topic_lines = wrap_label(data["topic"], 15, 3)
    subtitle = data["subtitle"]

    lines = [
        f'<rect id="topic-block" x="{x}" y="{y}" width="{w}" height="{h}" rx="14" ry="14" fill="#F8FBFF" stroke="{PALETTE["navy"]}" stroke-width="3" filter="url(#softShadow)"/>',
        render_target_icon(x + w / 2, y + 70),
    ]

    topic_size = topic_font_size(data["topic"])
    start_y = y + 184 - max(0, len(topic_lines) - 1) * (topic_size * 0.62)
    for i, line in enumerate(topic_lines):
        lines.append(f'<text x="{x + w / 2:.0f}" y="{start_y + i * (topic_size + 5):.0f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{topic_size}" font-weight="700" fill="{PALETTE["navy"]}">{xml(line)}</text>')

    if subtitle:
        divider_y = y + h - 92
        subtitle_y = divider_y + 52
        lines.extend(
            [
                f'<line x1="{x + 42}" y1="{divider_y}" x2="{x + w - 42}" y2="{divider_y}" stroke="{PALETTE["soft_blue"]}" stroke-width="2" stroke-dasharray="7 6"/>',
                f'<text x="{x + w / 2:.0f}" y="{subtitle_y}" text-anchor="middle" font-family="{FONT_STACK}" font-size="22" font-weight="700" fill="{PALETTE["navy"]}">{xml(truncate(subtitle, 20))}</text>',
            ]
        )
    return "\n".join(lines)


def topic_font_size(text: str) -> int:
    if visual_len(text) > 34:
        return 25
    if visual_len(text) > 25:
        return 28
    return 31


def branch_dx(vertical_distance: int) -> int:
    return round(vertical_distance / math.tan(math.radians(BRANCH_ANGLE_DEG)))


def interpolate_x(x1: int, y1: int, x2: int, y2: int, y: int) -> int:
    if y1 == y2:
        return x1
    ratio = (y - y1) / (y2 - y1)
    return round(x1 + (x2 - x1) * ratio)


def render_target_icon(cx: float, cy: float) -> str:
    color = PALETTE["blue"]
    return "\n".join(
        [
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="38" fill="{PALETTE["light_blue"]}" opacity="0.9"/>',
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="24" fill="none" stroke="{color}" stroke-width="5"/>',
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="10" fill="none" stroke="{color}" stroke-width="5"/>',
            f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{cx + 25:.0f}" y2="{cy - 25:.0f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>',
            f'<polyline points="{cx + 17:.0f},{cy - 25:.0f} {cx + 28:.0f},{cy - 28:.0f} {cx + 25:.0f},{cy - 17:.0f}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
        ]
    )


def wrap_label(text: str, limit: int, max_lines: int) -> list[str]:
    return wrap_text(text, limit, max_lines)


def truncate(text: str, limit: int) -> str:
    return truncate_text(text, limit)


def contains_cjk(text: str) -> bool:
    return any(visual_len(char) == 2 for char in text)


def xml(value: Any) -> str:
    return escape(str(value), {'"': "&quot;"})


def validate_svg(svg: str) -> None:
    root = ElementTree.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("Generated SVG root is invalid.")

    topic_block_found = False
    for element in root.iter():
        if element.attrib.get("id") == "topic-block":
            if not element.tag.endswith("rect"):
                raise ValueError("Topic block must be a rect element.")
            if not element.attrib.get("rx"):
                raise ValueError("Topic block must be a rounded rectangle with rx.")
            topic_block_found = True

    if not topic_block_found:
        raise ValueError("Topic block validation failed.")
