#!/usr/bin/env python3
"""Verify maintained testcases, templates, and key SVG layout invariants."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TESTCASES = ROOT / "testcases" / "fishbone"
FAULT_TREE_TESTCASES = ROOT / "testcases" / "fault-tree"
TEMPLATES = ROOT / "templates"
WORK = ROOT / "work" / "fishbone"
FAULT_TREE_WORK = ROOT / "work" / "fault-tree"
LUCIDE_CANDIDATES = ROOT / "assets" / "lucide-candidates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
NEW_FISHBONE = ROOT / "scripts" / "new_fishbone.py"
NEW_FAULT_TREE = ROOT / "scripts" / "new_fault_tree.py"
RENDER_WORK = ROOT / "scripts" / "render_work.py"
RENDER_FAULT_TREE_WORK = ROOT / "scripts" / "render_fault_tree_work.py"
EXPORT_PNG = ROOT / "scripts" / "export_png.py"
EXPORT_FAULT_TREE_PNG = ROOT / "scripts" / "export_fault_tree_png.py"
PYTHON = Path(sys.executable)

REQUIRED_LUCIDE_ICONS = [
    "workflow",
    "network",
    "aperture",
    "thermometer",
    "cog",
    "circuit-board",
    "boxes",
    "wrench",
    "shield-check",
    "map-pin",
    "gauge",
    "chart-line",
    "circle-dollar-sign",
    "chart-no-axes-column-increasing",
    "cloud",
    "cloud-cog",
    "cloud-upload",
    "server",
    "server-cog",
    "database",
    "database-backup",
    "hard-drive",
    "monitor-cloud",
    "router",
    "ethernet-port",
    "container",
    "webhook",
]

TESTCASE_PAIRS = [
    ("fishbone.input.example.json", "fishbone.output.example.svg"),
    ("fishbone.input.example.md", "fishbone.output.example.svg"),
    ("fishbone.subcategory.example.md", "fishbone.subcategory.output.md.svg"),
    ("fishbone.subcategory.example.json", "fishbone.subcategory.output.json.svg"),
    ("fishbone.five-primary.example.json", "fishbone.five-primary.output.svg"),
    ("fishbone.five-subcategories.example.json", "fishbone.five-subcategories.output.svg"),
    ("fishbone.dense-collision.example.json", "fishbone.dense-collision.output.svg"),
]

FAULT_TREE_TESTCASE_PAIRS = [
    ("fault-tree.input.example.json", "fault-tree.output.example.svg"),
    ("fault-tree.input.example.md", "fault-tree.output.md.svg"),
    ("fault-tree.mixed-gates.example.json", "fault-tree.mixed-gates.output.svg"),
    ("fault-tree.nested-gates.example.json", "fault-tree.nested-gates.output.svg"),
    ("fault-tree.multi-nested.example.json", "fault-tree.multi-nested.output.svg"),
]

FORBIDDEN_WORDS = [
    "fish head",
    "fish tail",
    "fish eye",
    "fish mouth",
    "fish scales",
    "fish fins",
    "skeleton fish",
    "ocean waves",
    "marine decoration",
]


def main() -> int:
    for input_name, output_name in TESTCASE_PAIRS:
        run_generate(TESTCASES / input_name, TESTCASES / output_name)

    for input_name, output_name in FAULT_TREE_TESTCASE_PAIRS:
        run_generate(FAULT_TREE_TESTCASES / input_name, FAULT_TREE_TESTCASES / output_name)

    for _, output_name in TESTCASE_PAIRS:
        verify_svg_basics(TESTCASES / output_name)

    for _, output_name in FAULT_TREE_TESTCASE_PAIRS:
        verify_fault_tree_svg_basics(FAULT_TREE_TESTCASES / output_name)
    verify_fault_tree_nested_gates(FAULT_TREE_TESTCASES / "fault-tree.nested-gates.output.svg")
    verify_fault_tree_multi_nested(FAULT_TREE_TESTCASES / "fault-tree.multi-nested.output.svg")

    verify_canvas_dimensions()
    verify_subcategory_braces(TESTCASES / "fishbone.subcategory.output.md.svg")
    verify_primary_cause_connectors(TESTCASES / "fishbone.five-primary.output.svg")
    verify_branch_lengths()
    verify_category_labels_and_icons()
    verify_lucide_badge_candidates()
    verify_global_layout_planner()
    verify_templates()
    verify_new_fishbone_entrypoint()
    verify_new_fault_tree_entrypoint()
    verify_render_work_entrypoint()
    verify_render_fault_tree_work_entrypoint()
    verify_export_png_entrypoint()
    verify_export_fault_tree_png_entrypoint()
    verify_work_name_validation()
    verify_no_tmp_files(TESTCASES)
    verify_no_tmp_files(FAULT_TREE_TESTCASES)
    verify_no_tmp_files(TEMPLATES)
    verify_no_tmp_files(WORK)
    verify_no_tmp_files(FAULT_TREE_WORK)

    print("Verification passed")
    return 0


def run_generate(input_path: Path, output_path: Path) -> None:
    result = subprocess.run(
        [str(PYTHON), str(GENERATE), str(input_path), str(output_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"Failed to generate {output_path.name}:\n{result.stderr}")


def verify_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")

    topic_blocks = [element for element in root.iter() if element.attrib.get("id") == "topic-block"]
    if not topic_blocks:
        raise AssertionError(f"{path.name}: missing topic-block")
    topic_block = topic_blocks[0]
    if not topic_block.tag.endswith("rect") or not topic_block.attrib.get("rx"):
        raise AssertionError(f"{path.name}: topic-block must be a rounded rect")

    text = path.read_text(encoding="utf-8").lower()
    hits = [word for word in FORBIDDEN_WORDS if word in text]
    if hits:
        raise AssertionError(f"{path.name}: forbidden words found: {hits}")


def verify_fault_tree_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width < 1920 or height < 1080:
        raise AssertionError(f"{path.name}: canvas must not shrink below 1920x1080, got {width}x{height}")

    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "top-event-block"]
    if len(top_blocks) != 1:
        raise AssertionError(f"{path.name}: expected one top-event-block, got {len(top_blocks)}")
    top_block = top_blocks[0]
    if not top_block.tag.endswith("rect") or not top_block.attrib.get("rx"):
        raise AssertionError(f"{path.name}: top-event-block must be a rounded rect")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    for required_class in ["fault-gate-or", "fault-gate-and", "fault-basic-event", "fault-intermediate-event"]:
        if required_class not in classes:
            raise AssertionError(f"{path.name}: missing required class {required_class}")

    legends = [element for element in root.iter() if element.attrib.get("id") == "fault-tree-legend"]
    if len(legends) != 1:
        raise AssertionError(f"{path.name}: expected one fault-tree-legend, got {len(legends)}")

    detail_panels = [element for element in root.iter() if element.attrib.get("id") == "fault-event-detail-panel"]
    if len(detail_panels) != 1:
        raise AssertionError(f"{path.name}: expected one fault-event-detail-panel, got {len(detail_panels)}")

    verify_fault_tree_basic_events(root, path.name)
    verify_fault_event_rects_within_canvas(root, path.name)

    text = path.read_text(encoding="utf-8").lower()
    hits = [word for word in FORBIDDEN_WORDS if word in text]
    if hits:
        raise AssertionError(f"{path.name}: forbidden words found: {hits}")


def verify_fault_tree_basic_events(root: ET.Element, label: str) -> None:
    basic_groups = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "fault-basic-event" in element.attrib.get("class", "")
    ]
    if not basic_groups:
        raise AssertionError(f"{label}: missing fault-basic-event groups")

    has_content_sized_card = False
    for group in basic_groups:
        child_tags = [child.tag for child in list(group)]
        if any(tag.endswith("circle") for tag in child_tags):
            raise AssertionError(f"{label}: basic events must not render an internal circle marker")
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            raise AssertionError(f"{label}: basic event group missing rect")
        width = float(rects[0].attrib.get("width", "0"))
        height = float(rects[0].attrib.get("height", "0"))
        has_content_sized_card = has_content_sized_card or width > 170 or height > 62

    if not has_content_sized_card:
        raise AssertionError(f"{label}: expected at least one content-sized basic event card")


def verify_fault_tree_nested_gates(path: Path) -> None:
    root = ET.parse(path).getroot()
    text_values = [element.text or "" for element in root.iter() if element.tag.endswith("text")]
    required_labels = [
        "Power Path Issue",
        "Fuse Opens Under",
        "Startup Surge",
        "Control Path Issue",
        "Ready Signal Not",
        "Detected",
    ]
    missing = [label for label in required_labels if label not in text_values]
    if missing:
        raise AssertionError(f"{path.name}: missing expected nested-gate labels: {missing}")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    if classes.count("fault-intermediate-event") < 4:
        raise AssertionError(f"{path.name}: expected nested intermediate events")
    if classes.count("fault-gate-or") < 2 or classes.count("fault-gate-and") < 2:
        raise AssertionError(f"{path.name}: expected multiple AND and OR gates in nested subtrees")
    verify_fault_tree_branch_connectors(root, path.name, min_trunks=4, min_branches=8)


def verify_fault_tree_multi_nested(path: Path) -> None:
    root = ET.parse(path).getroot()
    svg_text = path.read_text(encoding="utf-8")
    required_labels = [
        "Safety Path",
        "Relay Logic",
        "Sensor Logic",
        "Emergency Stop",
        "Controller Path",
    ]
    missing = [label for label in required_labels if label not in svg_text]
    if missing:
        raise AssertionError(f"{path.name}: missing expected multi-nested labels: {missing}")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    if classes.count("fault-intermediate-event") < 4:
        raise AssertionError(f"{path.name}: expected one first-level event with multiple nested intermediate events")
    if classes.count("fault-gate-or") < 3 or classes.count("fault-gate-and") < 2:
        raise AssertionError(f"{path.name}: expected mixed gates across first-level and nested events")

    verify_fault_tree_branch_connectors(root, path.name, min_trunks=4, min_branches=7)
    nested_centers = fault_event_centers_by_label(root, ["Relay", "Sensor"])
    safety_centers = fault_event_centers_by_label(root, ["Safety"])
    if len(nested_centers) != 2 or len(safety_centers) != 1:
        raise AssertionError(f"{path.name}: could not locate Safety Path with two nested intermediate events")
    safety_x, safety_y = safety_centers[0]
    for nested_x, nested_y in nested_centers:
        if not (nested_x < safety_x and nested_y > safety_y):
            raise AssertionError(f"{path.name}: nested intermediate events must branch left and below Safety Path")


def fault_event_centers_by_label(root: ET.Element, label_fragments: list[str]) -> list[tuple[float, float]]:
    centers: list[tuple[float, float]] = []
    for group in root.iter():
        if not group.tag.endswith("g") or "fault-intermediate-event" not in group.attrib.get("class", ""):
            continue
        label_text = " ".join(child.text or "" for child in list(group) if child.tag.endswith("text"))
        if not any(fragment in label_text for fragment in label_fragments):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            continue
        rect = rects[0]
        x = float(rect.attrib.get("x", "0"))
        y = float(rect.attrib.get("y", "0"))
        width = float(rect.attrib.get("width", "0"))
        height = float(rect.attrib.get("height", "0"))
        centers.append((x + width / 2, y + height / 2))
    return centers


def verify_fault_event_rects_within_canvas(root: ET.Element, label: str) -> None:
    canvas_width = float(root.attrib["width"])
    canvas_height = float(root.attrib["height"])
    for group in root.iter():
        if not group.tag.endswith("g") or "fault-event" not in group.attrib.get("class", ""):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            raise AssertionError(f"{label}: fault event group missing rect")
        rect = rects[0]
        x = float(rect.attrib.get("x", "0"))
        y = float(rect.attrib.get("y", "0"))
        width = float(rect.attrib.get("width", "0"))
        height = float(rect.attrib.get("height", "0"))
        if x < -0.1 or y < -0.1 or x + width > canvas_width + 0.1 or y + height > canvas_height + 0.1:
            raise AssertionError(
                f"{label}: fault event rect outside canvas: x={x}, y={y}, w={width}, h={height}, canvas={canvas_width}x{canvas_height}"
            )


def verify_fault_tree_branch_connectors(root: ET.Element, label: str, *, min_trunks: int, min_branches: int) -> None:
    trunks = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and "fault-branch-trunk" in element.attrib.get("class", "")
    ]
    branches = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and "fault-branch-line" in element.attrib.get("class", "")
    ]
    if len(trunks) < min_trunks:
        raise AssertionError(f"{label}: expected at least {min_trunks} compact branch trunks, got {len(trunks)}")
    if len(branches) < min_branches:
        raise AssertionError(f"{label}: expected at least {min_branches} compact branch lines, got {len(branches)}")
    rightward = [
        line
        for line in branches
        if float(line.attrib.get("x2", "0")) >= float(line.attrib.get("x1", "0"))
    ]
    if rightward:
        raise AssertionError(f"{label}: compact branch lines must run left from the parent trunk")


def verify_canvas_dimensions() -> None:
    base_size = svg_dimensions(TESTCASES / "fishbone.output.example.svg")
    if base_size != (1920, 1080):
        raise AssertionError(f"Basic fishbone should keep the base 1920x1080 canvas, got {base_size}")

    dense_size = svg_dimensions(TESTCASES / "fishbone.dense-collision.output.svg")
    if dense_size[0] <= 1920 and dense_size[1] <= 1080:
        raise AssertionError(f"Dense fishbone should expand the canvas, got {dense_size}")

    for _, output_name in TESTCASE_PAIRS:
        size = svg_dimensions(TESTCASES / output_name)
        if size[0] < 1920 or size[1] < 1080:
            raise AssertionError(f"{output_name}: canvas must not shrink below 1920x1080, got {size}")


def svg_dimensions(path: Path) -> tuple[int, int]:
    root = ET.parse(path).getroot()
    return int(float(root.attrib["width"])), int(float(root.attrib["height"]))


def verify_subcategory_braces(path: Path) -> None:
    root = ET.parse(path).getroot()
    braces = [
        element.attrib["d"]
        for element in root.iter()
        if element.tag.endswith("path") and element.attrib.get("class") == "child-curly-brace"
    ]
    if not braces:
        raise AssertionError(f"{path.name}: missing child-curly-brace paths")

    has_right_brace = False
    has_left_brace = False
    for brace in braces:
        values = parse_path_numbers(brace)
        end_x = values[0]
        body_x = values[2]
        cusp_x = values[14]
        has_right_brace = has_right_brace or (end_x > body_x and cusp_x < body_x)
        has_left_brace = has_left_brace or (end_x < body_x and cusp_x > body_x)

    if not has_right_brace:
        raise AssertionError(f"{path.name}: missing right-side child brace shaped like '{{'")
    if not has_left_brace:
        raise AssertionError(f"{path.name}: missing left-side child brace shaped like '}}'")


def verify_primary_cause_connectors(path: Path) -> None:
    svg = path.read_text(encoding="utf-8")
    root = ET.fromstring(svg)
    texts = [
        (element.text or "", float(element.attrib.get("y", 0)))
        for element in root.iter()
        if element.tag.endswith("text")
    ]
    training_y = next(y for text, y in texts if text == "Training")
    connector_y = training_y - 6
    lines = [
        element
        for element in root.iter()
        if element.tag.endswith("line")
        and abs(float(element.attrib.get("y1", 9999)) - connector_y) < 0.1
        and abs(float(element.attrib.get("y2", 9999)) - connector_y) < 0.1
    ]
    if not lines:
        raise AssertionError(f"{path.name}: primary cause must have a short connector line")

    line_index = svg.index(f'y1="{connector_y:.0f}"')
    circle_index = svg.index('r="7" fill="#FFFFFF" stroke="#1E5AA8"', line_index)
    if line_index > circle_index:
        raise AssertionError(f"{path.name}: anchor circle must render above the connector line")


def verify_branch_lengths() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from renderers.fishbone import branch_length_for_category, normalize_input

    data = normalize_input(
        {
            "diagram_type": "fishbone",
            "topic": "Branch length test",
            "categories": [
                {"name_en": "Sparse", "items": ["One", "Two"]},
                {"name_en": "Plain3", "items": ["One", "Two", "Three"]},
                {"name_en": "WithSub", "items": [{"subcategory": "Group", "items": ["A", "B"]}, "Two", "Three"]},
                {"name_en": "Other", "items": []},
            ],
        }
    )
    categories = data["categories"]
    sparse = branch_length_for_category(categories[0])
    plain3 = branch_length_for_category(categories[1])
    with_sub = branch_length_for_category(categories[2])
    if (sparse, plain3, with_sub) != (180, 230, 270):
        raise AssertionError(f"Unexpected branch lengths: {sparse}, {plain3}, {with_sub}")
    verify_dense_subcategory_branch_expands()


def verify_dense_subcategory_branch_expands() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from renderers.fishbone import branch_length_for_category, normalize_input

    data = normalize_input(
        {
            "diagram_type": "fishbone",
            "topic": "Dense subcategory test",
            "categories": [
                {
                    "name_en": "Dense",
                    "items": [
                        {"subcategory": "One", "items": ["A", "B", "C"]},
                        {"subcategory": "Two", "items": ["A", "B", "C"]},
                        {"subcategory": "Three", "items": ["A", "B", "C"]},
                        {"subcategory": "Four", "items": ["A", "B", "C"]},
                        {"subcategory": "Five", "items": ["A", "B", "C"]},
                    ],
                },
                {"name_en": "Plain", "items": ["One", "Two", "Three"]},
                {"name_en": "Other", "items": []},
                {"name_en": "More", "items": []},
            ],
        }
    )
    branch_length = branch_length_for_category(data["categories"][0])
    if branch_length <= 270:
        raise AssertionError(f"Dense subcategory branch should expand beyond base length, got {branch_length}")


def verify_category_labels_and_icons() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from renderers.fishbone import Category, icon_for_category, normalize_input, render_fishbone, wrap_category_label

    expected_icons = {
        "人员与操作": "people",
        "设备与治具": "tools",
        "材料与供应": "materials",
        "工艺与方法": "methods",
        "环境与物流": "environment",
        "测试与判定": "gauge",
    }
    expected_icons.update(
        {
            "System": "lucide:workflow",
            "Architecture": "lucide:network",
            "Optical Design": "lucide:aperture",
            "Thermal Design": "lucide:thermometer",
            "Mechanical Design": "lucide:cog",
            "Electrical Design": "lucide:circuit-board",
            "Materials": "lucide:boxes",
            "Manufacturing": "lucide:wrench",
            "Reliability": "lucide:shield-check",
            "Field Use": "lucide:map-pin",
            "Test/Measurement": "lucide:gauge",
            "Verification/DVT/SVT/EVT/EDVT": "lucide:chart-line",
            "Cost": "lucide:circle-dollar-sign",
            "Business": "lucide:chart-no-axes-column-increasing",
        }
    )
    for label, expected_icon in expected_icons.items():
        actual_icon = icon_for_category(Category(label, "", []))
        if actual_icon != expected_icon:
            raise AssertionError(f"Category '{label}' mapped to {actual_icon}, expected {expected_icon}")

    long_label = "非常长的中文主分类标题需要换行"
    label_lines = wrap_category_label(long_label)
    if len(label_lines) != 2:
        raise AssertionError(f"Long category label should wrap to two lines, got {label_lines}")

    data = normalize_input(
        {
            "diagram_type": "fishbone",
            "topic": "Category label wrap test",
            "categories": [
                {"name_en": long_label, "items": ["One", "Two"]},
                {"name_en": "设备与治具", "items": ["One", "Two"]},
                {"name_en": "材料与供应", "items": ["One", "Two"]},
                {"name_en": "测试与判定", "items": ["One", "Two"]},
            ],
        }
    )
    svg = render_fishbone(data)
    root = ET.fromstring(svg)
    text_values = [element.text or "" for element in root.iter() if element.tag.endswith("text")]
    if not all(line in text_values for line in label_lines):
        raise AssertionError(f"Wrapped category label lines missing from SVG: {label_lines}")


def verify_lucide_badge_candidates() -> None:
    if not LUCIDE_CANDIDATES.exists():
        raise AssertionError("Missing Lucide candidate badge directory")

    for icon_name in REQUIRED_LUCIDE_ICONS:
        icon_path = LUCIDE_CANDIDATES / f"{icon_name}.svg"
        if not icon_path.exists():
            raise AssertionError(f"Missing required Lucide candidate icon: {icon_path.relative_to(ROOT)}")
        if icon_path.stat().st_size == 0:
            raise AssertionError(f"Lucide candidate icon is empty: {icon_path.relative_to(ROOT)}")
        ET.parse(icon_path)

    sys.path.insert(0, str(ROOT / "scripts"))
    import render_lucide_candidate_catalog

    referenced_icons = {
        icon_name
        for _group_name, icons in render_lucide_candidate_catalog.GROUPS
        for icon_name in icons
    }
    for icon_name in referenced_icons:
        icon_path = LUCIDE_CANDIDATES / f"{icon_name}.svg"
        if not icon_path.exists():
            raise AssertionError(f"Lucide catalog references missing icon: {icon_path.relative_to(ROOT)}")

    catalog_svg = render_lucide_candidate_catalog.render_catalog()
    root = ET.fromstring(catalog_svg)
    if not root.tag.endswith("svg"):
        raise AssertionError("Lucide candidate catalog did not render an SVG root")
    width = int(float(root.attrib.get("width", "0")))
    height = int(float(root.attrib.get("height", "0")))
    if width <= 0 or height <= 0:
        raise AssertionError(f"Lucide candidate catalog has invalid dimensions: {width}x{height}")


def verify_global_layout_planner() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from renderers.fishbone import CARD_W, HEIGHT, WIDTH, category_footprint, normalize_input, plan_render_layout, side_for_item

    data = normalize_input(
        {
            "diagram_type": "fishbone",
            "topic": "Layout planner test",
            "categories": [
                dense_category("Dense A"),
                dense_category("Dense B"),
                dense_category("Dense C"),
                {"name_en": "Sparse D", "items": ["One", "Two"]},
                {"name_en": "Sparse E", "items": ["One", "Two"]},
                {"name_en": "Sparse F", "items": ["One", "Two"]},
            ],
        }
    )
    render_layout, top_layouts, bottom_layouts = plan_render_layout(data["categories"])
    top_indices = [layout.category_index for layout in top_layouts]
    bottom_indices = [layout.category_index for layout in bottom_layouts]

    if len(top_layouts) != 3 or len(bottom_layouts) != 3:
        raise AssertionError("Six categories must remain balanced as 3 top / 3 bottom")
    if top_indices == [0, 1, 2] and bottom_indices == [3, 4, 5]:
        raise AssertionError("Dense first-half categories should not stay as a simple split")
    if top_indices != sorted(top_indices) or bottom_indices != sorted(bottom_indices):
        raise AssertionError("Top and bottom category order must preserve input-relative order")
    if render_layout.width <= WIDTH and render_layout.height <= HEIGHT:
        raise AssertionError("Dense global layout should expand the canvas instead of crowding the base canvas")

    for column_index in range(min(len(top_layouts), len(bottom_layouts))):
        if top_layouts[column_index].x != bottom_layouts[column_index].x:
            raise AssertionError("Top and bottom layouts in the same column must share one anchor x")

    for layout in top_layouts + bottom_layouts:
        left, _ = category_footprint(layout.category, layout.start_side)
        if layout.x - left < render_layout.layout_left_safe_x:
            raise AssertionError(f"Category {layout.category.name_en} enters the chevron safe area")
        _, right = category_footprint(layout.category, layout.start_side)
        if layout.x + max(CARD_W / 2, right) > render_layout.layout_right_safe_x:
            raise AssertionError(f"Category {layout.category.name_en} enters the topic-safe area")

    for layout in top_layouts + bottom_layouts:
        real_count = len(layout.category.items)
        if real_count >= 2:
            sides = {side_for_item(row, layout.start_side) for row in range(real_count)}
            if sides != {"left", "right"}:
                raise AssertionError(f"Category {layout.category.name_en} does not alternate left/right")


def dense_category(name: str) -> dict[str, object]:
    return {
        "name_en": name,
        "items": [
            {"subcategory": "Training", "items": ["Onboarding", "Skill matrix", "Certification"]},
            "Role clarity",
            {"subcategory": "Escalation path", "items": ["Ownership", "Response time", "Closure"]},
            "Handoff quality",
            {"subcategory": "Packaging", "items": ["Shock protection", "Label accuracy", "Handling"]},
        ],
    }


def verify_templates() -> None:
    md_template = TEMPLATES / "fishbone.template.md"
    json_template = TEMPLATES / "fishbone.template.json"
    fault_tree_md_template = TEMPLATES / "fault-tree.template.md"
    fault_tree_json_template = TEMPLATES / "fault-tree.template.json"
    for path in [md_template, json_template, fault_tree_md_template, fault_tree_json_template]:
        if not path.exists():
            raise AssertionError(f"Missing template: {path.name}")
        if not path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"Empty template: {path.name}")

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_diagram import parse_input

    md_data = parse_input(md_template)
    verify_template_structure(md_data, md_template.name)

    json_data = json.loads(json_template.read_text(encoding="utf-8"))
    if not isinstance(json_data, dict):
        raise AssertionError(f"{json_template.name}: JSON template must be an object")
    verify_template_structure(json_data, json_template.name)

    fault_md_data = parse_input(fault_tree_md_template)
    verify_fault_tree_template_structure(fault_md_data, fault_tree_md_template.name)

    fault_json_data = json.loads(fault_tree_json_template.read_text(encoding="utf-8"))
    if not isinstance(fault_json_data, dict):
        raise AssertionError(f"{fault_tree_json_template.name}: JSON template must be an object")
    verify_fault_tree_template_structure(fault_json_data, fault_tree_json_template.name)

    pid = os.getpid()
    template_outputs = [
        TEMPLATES / f"fishbone.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fishbone.template.json.{pid}.tmp.svg",
        TEMPLATES / f"fault-tree.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fault-tree.template.json.{pid}.tmp.svg",
    ]
    try:
        run_generate(md_template, template_outputs[0])
        run_generate(json_template, template_outputs[1])
        run_generate(fault_tree_md_template, template_outputs[2])
        run_generate(fault_tree_json_template, template_outputs[3])
        verify_svg_basics(template_outputs[0])
        verify_svg_basics(template_outputs[1])
        verify_fault_tree_svg_basics(template_outputs[2])
        verify_fault_tree_svg_basics(template_outputs[3])
    finally:
        for output_path in template_outputs:
            output_path.unlink(missing_ok=True)


def verify_template_structure(data: dict[str, object], label: str) -> None:
    if not str(data.get("topic", "")).strip():
        raise AssertionError(f"{label}: template must include a topic")

    categories = data.get("categories")
    if not isinstance(categories, list) or len(categories) < 2:
        raise AssertionError(f"{label}: template must include multiple categories")

    has_primary_cause = False
    has_subcategory = False
    for category in categories:
        if not isinstance(category, dict):
            continue
        items = category.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, str) and item.strip():
                has_primary_cause = True
            elif isinstance(item, dict) and str(item.get("subcategory", "")).strip():
                children = item.get("items")
                if isinstance(children, list) and any(isinstance(child, str) and child.strip() for child in children):
                    has_subcategory = True

    if not has_primary_cause:
        raise AssertionError(f"{label}: template must include at least one ordinary primary cause")
    if not has_subcategory:
        raise AssertionError(f"{label}: template must include at least one subcategory with child causes")


def verify_fault_tree_template_structure(data: dict[str, object], label: str) -> None:
    if str(data.get("diagram_type", "")).replace("-", "_") != "fault_tree":
        raise AssertionError(f"{label}: template must use diagram_type=fault_tree")

    top_event = data.get("top_event")
    if not isinstance(top_event, dict) or not str(top_event.get("label", "")).strip():
        raise AssertionError(f"{label}: template must include a labeled top_event")

    event_detail = data.get("event_detail")
    if not isinstance(event_detail, dict):
        raise AssertionError(f"{label}: template must include an event_detail object")
    has_detail_text = str(event_detail.get("text", "")).strip()
    bullets = event_detail.get("bullets")
    has_detail_bullets = isinstance(bullets, list) and any(str(item).strip() for item in bullets)
    if not has_detail_text and not has_detail_bullets:
        raise AssertionError(f"{label}: template event_detail must include text or bullets")

    tree = data.get("tree")
    if not isinstance(tree, dict):
        raise AssertionError(f"{label}: template must include a tree object")

    children = tree.get("children")
    if not isinstance(children, list) or len(children) < 2:
        raise AssertionError(f"{label}: template must include multiple first-level fault events")

    gates = {str(tree.get("gate", "")).upper()}
    has_basic_event = False
    has_nested_intermediate_event = False
    for child in children:
        if not isinstance(child, dict):
            continue
        gates.add(str(child.get("gate", "")).upper())
        child_events = child.get("children")
        if isinstance(child_events, list):
            has_basic_event = has_basic_event or any(
                isinstance(grandchild, dict) and str(grandchild.get("label", "")).strip()
                for grandchild in child_events
            )
            nested_intermediates = [
                grandchild
                for grandchild in child_events
                if isinstance(grandchild, dict)
                and str(grandchild.get("type", "")).replace("-", "_") == "intermediate_event"
                and isinstance(grandchild.get("children"), list)
            ]
            has_nested_intermediate_event = has_nested_intermediate_event or bool(nested_intermediates)
            for nested in nested_intermediates:
                gates.add(str(nested.get("gate", "")).upper())

    if not {"AND", "OR"}.issubset(gates):
        raise AssertionError(f"{label}: template must include both AND and OR gates")
    if not has_basic_event:
        raise AssertionError(f"{label}: template must include basic event leaves")
    if not has_nested_intermediate_event:
        raise AssertionError(f"{label}: template must include at least one nested intermediate-event example")


def verify_no_tmp_files(path: Path) -> None:
    if not path.exists():
        return
    tmp_files = list(path.glob("*tmp*"))
    if tmp_files:
        names = ", ".join(item.name for item in tmp_files)
        raise AssertionError(f"{path.name}: temporary files remain: {names}")


def verify_new_fishbone_entrypoint() -> None:
    stem = f"verify-new-fishbone-{os.getpid()}"
    input_path = WORK / f"{stem}.md"
    output_path = WORK / f"{stem}.svg"
    try:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_FISHBONE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_fishbone.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_fishbone.py did not create expected work files")
        verify_svg_basics(output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_FISHBONE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_fishbone.py should refuse to overwrite existing work files without --force")
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def verify_new_fault_tree_entrypoint() -> None:
    stem = f"verify-new-fault-tree-{os.getpid()}"
    input_path = FAULT_TREE_WORK / f"{stem}.md"
    output_path = FAULT_TREE_WORK / f"{stem}.svg"
    try:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_FAULT_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_fault_tree.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_fault_tree.py did not create expected work files")
        verify_fault_tree_svg_basics(output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_FAULT_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_fault_tree.py should refuse to overwrite existing work files without --force")
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def verify_render_work_entrypoint() -> None:
    stem = f"verify-render-work-{os.getpid()}"
    md_input_path = WORK / f"{stem}.md"
    json_input_path = WORK / f"{stem}.json"
    output_path = WORK / f"{stem}.svg"
    try:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FISHBONE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fishbone.py failed during render_work verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_work.py did not create the expected SVG")
        verify_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "fishbone.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_work.py --format json failed:\n{format_result.stderr}")
        verify_svg_basics(output_path)
    finally:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)


def verify_render_fault_tree_work_entrypoint() -> None:
    stem = f"verify-render-fault-tree-{os.getpid()}"
    md_input_path = FAULT_TREE_WORK / f"{stem}.md"
    json_input_path = FAULT_TREE_WORK / f"{stem}.json"
    output_path = FAULT_TREE_WORK / f"{stem}.svg"
    try:
        FAULT_TREE_WORK.mkdir(parents=True, exist_ok=True)
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FAULT_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fault_tree.py failed during render_fault_tree_work verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_FAULT_TREE_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_fault_tree_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_fault_tree_work.py did not create the expected SVG")
        verify_fault_tree_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "fault-tree.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_FAULT_TREE_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_fault_tree_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_FAULT_TREE_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_fault_tree_work.py --format json failed:\n{format_result.stderr}")
        verify_fault_tree_svg_basics(output_path)
    finally:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)


def verify_export_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-png-{os.getpid()}"
    input_path = WORK / f"{stem}.md"
    svg_path = WORK / f"{stem}.svg"
    png_path = WORK / f"{stem}.png"
    try:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FISHBONE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fishbone.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_export_fault_tree_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-fault-tree-png-{os.getpid()}"
    input_path = FAULT_TREE_WORK / f"{stem}.md"
    svg_path = FAULT_TREE_WORK / f"{stem}.svg"
    png_path = FAULT_TREE_WORK / f"{stem}.png"
    try:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FAULT_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fault_tree.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_FAULT_TREE_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_fault_tree_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_fault_tree_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"Fault tree PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_FAULT_TREE_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_fault_tree_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_work_name_validation() -> None:
    unsafe_names = ["../outside", r"..\outside", "has space", "UPPER", "name.ext"]
    for unsafe_name in unsafe_names:
        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FISHBONE), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode == 0:
            raise AssertionError(f"new_fishbone.py accepted unsafe name: {unsafe_name}")

        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode == 0:
            raise AssertionError(f"render_work.py accepted unsafe name: {unsafe_name}")

        fault_create_result = subprocess.run(
            [str(PYTHON), str(NEW_FAULT_TREE), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fault_create_result.returncode == 0:
            raise AssertionError(f"new_fault_tree.py accepted unsafe name: {unsafe_name}")

        fault_render_result = subprocess.run(
            [str(PYTHON), str(RENDER_FAULT_TREE_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fault_render_result.returncode == 0:
            raise AssertionError(f"render_fault_tree_work.py accepted unsafe name: {unsafe_name}")


def parse_path_numbers(path_data: str) -> list[float]:
    return [float(value) for value in re.findall(r"-?\d+\.\d+", path_data)]


if __name__ == "__main__":
    raise SystemExit(main())
