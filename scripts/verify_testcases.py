#!/usr/bin/env python3
"""Verify fishbone testcases, templates, and key SVG layout invariants."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TESTCASES = ROOT / "testcases"
TEMPLATES = ROOT / "templates"
WORK = ROOT / "work"
LUCIDE_CANDIDATES = ROOT / "assets" / "lucide-candidates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
NEW_FISHBONE = ROOT / "scripts" / "new_fishbone.py"
RENDER_WORK = ROOT / "scripts" / "render_work.py"
EXPORT_PNG = ROOT / "scripts" / "export_png.py"
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

    for _, output_name in TESTCASE_PAIRS:
        verify_svg_basics(TESTCASES / output_name)

    verify_canvas_dimensions()
    verify_subcategory_braces(TESTCASES / "fishbone.subcategory.output.md.svg")
    verify_primary_cause_connectors(TESTCASES / "fishbone.five-primary.output.svg")
    verify_branch_lengths()
    verify_category_labels_and_icons()
    verify_lucide_badge_candidates()
    verify_global_layout_planner()
    verify_templates()
    verify_new_fishbone_entrypoint()
    verify_render_work_entrypoint()
    verify_export_png_entrypoint()
    verify_work_name_validation()
    verify_no_tmp_files(TESTCASES)
    verify_no_tmp_files(TEMPLATES)
    verify_no_tmp_files(WORK)

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
    for path in [md_template, json_template]:
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

    pid = os.getpid()
    template_outputs = [
        TEMPLATES / f"fishbone.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fishbone.template.json.{pid}.tmp.svg",
    ]
    try:
        run_generate(md_template, template_outputs[0])
        run_generate(json_template, template_outputs[1])
        for output_path in template_outputs:
            verify_svg_basics(output_path)
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


def parse_path_numbers(path_data: str) -> list[float]:
    return [float(value) for value in re.findall(r"-?\d+\.\d+", path_data)]


if __name__ == "__main__":
    raise SystemExit(main())
