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
EXCLUSION_TREE_TESTCASES = ROOT / "testcases" / "exclusion-tree"
TWO_BY_TWO_TESTCASES = ROOT / "testcases" / "two-by-two-matrix"
ROADMAP_TESTCASES = ROOT / "testcases" / "roadmap-timeline"
FMEA_TESTCASES = ROOT / "testcases" / "fmea-table"
TEMPLATES = ROOT / "templates"
WORK = ROOT / "work" / "fishbone"
FAULT_TREE_WORK = ROOT / "work" / "fault-tree"
EXCLUSION_TREE_WORK = ROOT / "work" / "exclusion-tree"
TWO_BY_TWO_WORK = ROOT / "work" / "two-by-two-matrix"
ROADMAP_WORK = ROOT / "work" / "roadmap-timeline"
FMEA_WORK = ROOT / "work" / "fmea-table"
LUCIDE_CANDIDATES = ROOT / "assets" / "lucide-candidates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
NEW_FISHBONE = ROOT / "scripts" / "new_fishbone.py"
NEW_FAULT_TREE = ROOT / "scripts" / "new_fault_tree.py"
NEW_EXCLUSION_TREE = ROOT / "scripts" / "new_exclusion_tree.py"
NEW_TWO_BY_TWO = ROOT / "scripts" / "new_two_by_two_matrix.py"
NEW_ROADMAP = ROOT / "scripts" / "new_roadmap_timeline.py"
NEW_FMEA = ROOT / "scripts" / "new_fmea_table.py"
RENDER_WORK = ROOT / "scripts" / "render_work.py"
RENDER_FAULT_TREE_WORK = ROOT / "scripts" / "render_fault_tree_work.py"
RENDER_EXCLUSION_TREE_WORK = ROOT / "scripts" / "render_exclusion_tree_work.py"
RENDER_TWO_BY_TWO_WORK = ROOT / "scripts" / "render_two_by_two_matrix_work.py"
RENDER_ROADMAP_WORK = ROOT / "scripts" / "render_roadmap_timeline_work.py"
RENDER_FMEA_WORK = ROOT / "scripts" / "render_fmea_table_work.py"
EXPORT_PNG = ROOT / "scripts" / "export_png.py"
EXPORT_FAULT_TREE_PNG = ROOT / "scripts" / "export_fault_tree_png.py"
EXPORT_EXCLUSION_TREE_PNG = ROOT / "scripts" / "export_exclusion_tree_png.py"
EXPORT_TWO_BY_TWO_PNG = ROOT / "scripts" / "export_two_by_two_matrix_png.py"
EXPORT_ROADMAP_PNG = ROOT / "scripts" / "export_roadmap_timeline_png.py"
EXPORT_FMEA_PNG = ROOT / "scripts" / "export_fmea_table_png.py"
DIAGRAM_BUILDER_SERVER = ROOT / "scripts" / "diagram_builder_server.py"
PYTHON = Path(sys.executable)
SWIMLANE_BASE_H = 76
SWIMLANE_ROW_GAP = 36
SWIMLANE_MARKER_SLOT_GAP = 28

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
    ("fault-tree.eight-branches.example.json", "fault-tree.eight-branches.output.svg"),
]

EXCLUSION_TREE_TESTCASE_PAIRS = [
    ("exclusion-tree.input.example.json", "exclusion-tree.output.example.svg"),
    ("exclusion-tree.input.example.md", "exclusion-tree.output.md.svg"),
    ("exclusion-tree.long-text.example.json", "exclusion-tree.long-text.output.svg"),
    ("exclusion-tree.five-check-lanes.example.json", "exclusion-tree.five-check-lanes.output.svg"),
]

TWO_BY_TWO_TESTCASE_PAIRS = [
    ("two-by-two.action-priority.example.json", "two-by-two.action-priority.output.svg"),
    ("two-by-two.risk-benefit.example.json", "two-by-two.risk-benefit.output.svg"),
    ("two-by-two.evidence-impact.example.json", "two-by-two.evidence-impact.output.svg"),
    ("two-by-two.value-feasibility.example.json", "two-by-two.value-feasibility.output.svg"),
    ("two-by-two.urgency-importance.example.json", "two-by-two.urgency-importance.output.svg"),
    ("two-by-two.custom.example.json", "two-by-two.custom.output.svg"),
    ("two-by-two.markdown.example.md", "two-by-two.markdown.output.svg"),
]

ROADMAP_TESTCASE_PAIRS = [
    ("roadmap.swimlane.example.json", "roadmap.swimlane.output.svg"),
    ("roadmap.milestone.example.json", "roadmap.milestone.output.svg"),
    ("roadmap.markdown.example.md", "roadmap.markdown.output.svg"),
]

FMEA_TESTCASE_PAIRS = [
    ("fmea.input.example.json", "fmea.output.example.svg"),
    ("fmea.input.example.md", "fmea.output.md.svg"),
    ("fmea.long-text.example.json", "fmea.long-text.output.svg"),
]

TWO_BY_TWO_TEMPLATE_PRESETS = [
    "action_priority",
    "risk_benefit",
    "evidence_impact",
    "value_feasibility",
    "urgency_importance",
    "custom",
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

ALLOWED_PRESENTATION_FONT_WEIGHTS = {"400", "500", "600", "700", "normal", "bold"}


def main() -> int:
    for input_name, output_name in TESTCASE_PAIRS:
        run_generate(TESTCASES / input_name, TESTCASES / output_name)

    for input_name, output_name in FAULT_TREE_TESTCASE_PAIRS:
        run_generate(FAULT_TREE_TESTCASES / input_name, FAULT_TREE_TESTCASES / output_name)

    for input_name, output_name in EXCLUSION_TREE_TESTCASE_PAIRS:
        run_generate(EXCLUSION_TREE_TESTCASES / input_name, EXCLUSION_TREE_TESTCASES / output_name)

    for input_name, output_name in TWO_BY_TWO_TESTCASE_PAIRS:
        run_generate(TWO_BY_TWO_TESTCASES / input_name, TWO_BY_TWO_TESTCASES / output_name)

    for input_name, output_name in ROADMAP_TESTCASE_PAIRS:
        run_generate(ROADMAP_TESTCASES / input_name, ROADMAP_TESTCASES / output_name)

    for input_name, output_name in FMEA_TESTCASE_PAIRS:
        run_generate(FMEA_TESTCASES / input_name, FMEA_TESTCASES / output_name)

    for _, output_name in TESTCASE_PAIRS:
        verify_svg_basics(TESTCASES / output_name)

    for _, output_name in FAULT_TREE_TESTCASE_PAIRS:
        verify_fault_tree_svg_basics(FAULT_TREE_TESTCASES / output_name)
    verify_fault_tree_nested_gates(FAULT_TREE_TESTCASES / "fault-tree.nested-gates.output.svg")
    verify_fault_tree_multi_nested(FAULT_TREE_TESTCASES / "fault-tree.multi-nested.output.svg")
    verify_fault_tree_eight_branches(FAULT_TREE_TESTCASES / "fault-tree.eight-branches.output.svg")

    for _, output_name in EXCLUSION_TREE_TESTCASE_PAIRS:
        verify_exclusion_tree_svg_basics(EXCLUSION_TREE_TESTCASES / output_name)

    for _, output_name in TWO_BY_TWO_TESTCASE_PAIRS:
        verify_two_by_two_svg_basics(TWO_BY_TWO_TESTCASES / output_name)
    verify_two_by_two_item_limit()
    verify_two_by_two_notes_length_guard()

    for _, output_name in ROADMAP_TESTCASE_PAIRS:
        verify_roadmap_timeline_svg_basics(ROADMAP_TESTCASES / output_name)

    for _, output_name in FMEA_TESTCASE_PAIRS:
        verify_fmea_table_svg_basics(FMEA_TESTCASES / output_name)

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
    verify_new_exclusion_tree_entrypoint()
    verify_new_two_by_two_entrypoint()
    verify_new_roadmap_entrypoint()
    verify_new_fmea_entrypoint()
    verify_render_work_entrypoint()
    verify_render_fault_tree_work_entrypoint()
    verify_render_exclusion_tree_work_entrypoint()
    verify_render_two_by_two_work_entrypoint()
    verify_render_roadmap_work_entrypoint()
    verify_render_fmea_work_entrypoint()
    verify_export_png_entrypoint()
    verify_export_fault_tree_png_entrypoint()
    verify_export_exclusion_tree_png_entrypoint()
    verify_export_two_by_two_png_entrypoint()
    verify_export_roadmap_png_entrypoint()
    verify_export_fmea_png_entrypoint()
    verify_cmd_launchers()
    verify_diagram_builder_service()
    verify_work_name_validation()
    verify_no_tmp_files(TESTCASES)
    verify_no_tmp_files(FAULT_TREE_TESTCASES)
    verify_no_tmp_files(EXCLUSION_TREE_TESTCASES)
    verify_no_tmp_files(TWO_BY_TWO_TESTCASES)
    verify_no_tmp_files(ROADMAP_TESTCASES)
    verify_no_tmp_files(FMEA_TESTCASES)
    verify_no_tmp_files(TEMPLATES)
    verify_no_tmp_files(WORK)
    verify_no_tmp_files(FAULT_TREE_WORK)
    verify_no_tmp_files(EXCLUSION_TREE_WORK)
    verify_no_tmp_files(TWO_BY_TWO_WORK)
    verify_no_tmp_files(ROADMAP_WORK)
    verify_no_tmp_files(FMEA_WORK)

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


def verify_two_by_two_item_limit() -> None:
    stem = f"verify-two-by-two-limit-{os.getpid()}"
    input_path = TWO_BY_TWO_WORK / f"{stem}.json"
    output_path = TWO_BY_TWO_WORK / f"{stem}.svg"
    try:
        TWO_BY_TWO_WORK.mkdir(parents=True, exist_ok=True)
        data = {
            "diagram_type": "two_by_two_matrix",
            "preset": "action_priority",
            "title": "Too Many Items",
            "items": [
                {"id": f"I{index}", "name": f"Item {index}", "x_score": 3, "y_score": 3}
                for index in range(1, 22)
            ],
        }
        input_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        result = subprocess.run(
            [str(PYTHON), str(GENERATE), str(input_path), str(output_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            raise AssertionError("two-by-two renderer accepted more than 20 items")
        if "supports up to 20 items" not in result.stderr:
            raise AssertionError(f"two-by-two item limit error should be clear, got:\n{result.stderr}")
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def verify_two_by_two_notes_length_guard() -> None:
    stem = f"verify-two-by-two-notes-{os.getpid()}"
    input_path = TWO_BY_TWO_WORK / f"{stem}.json"
    output_path = TWO_BY_TWO_WORK / f"{stem}.svg"
    try:
        TWO_BY_TWO_WORK.mkdir(parents=True, exist_ok=True)
        data = {
            "diagram_type": "two_by_two_matrix",
            "preset": "action_priority",
            "title": "Notes Length Guard",
            "language": "zh",
            "notes": "优先执行高影响低工作量行动；为重大行动指定负责人、时间节点和验证标准；低优先事项资源允许时处理；高工作量低影响事项暂缓。",
            "items": [
                {"id": "A1", "name": "收集现场日志", "x_score": 1, "y_score": 5},
                {"id": "A2", "name": "分析固件状态", "x_score": 4, "y_score": 5},
                {"id": "A3", "name": "整理会议模板", "x_score": 1, "y_score": 1},
                {"id": "A4", "name": "重建历史数据库", "x_score": 5, "y_score": 1},
            ],
        }
        input_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        result = subprocess.run(
            [str(PYTHON), str(GENERATE), str(input_path), str(output_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"two-by-two long notes testcase failed:\n{result.stderr}")
        if "Notes exceeded the visible two-line area" not in result.stdout:
            raise AssertionError("two-by-two long notes should emit a shortening diagnostic")
        texts = [element.text or "" for element in ET.parse(output_path).getroot().iter() if element.tag.endswith("text")]
        note_lines = [text for text in texts if "优先执行" in text or text.endswith("...")]
        if not note_lines or not any(text.endswith("...") for text in note_lines):
            raise AssertionError("two-by-two long notes should render a visible shortened note ending with ...")
        if any(visual_len(text) > 48 for text in note_lines):
            raise AssertionError(f"two-by-two note lines should fit the visible note area: {note_lines}")
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


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
    verify_fault_tree_event_text_integrity(root, path.name)
    verify_fault_tree_connectors_avoid_top_block(root, path.name)
    verify_fault_event_rects_within_canvas(root, path.name)

    text = path.read_text(encoding="utf-8").lower()
    hits = [word for word in FORBIDDEN_WORDS if word in text]
    if hits:
        raise AssertionError(f"{path.name}: forbidden words found: {hits}")


def verify_exclusion_tree_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width < 1920 or height < 1080:
        raise AssertionError(f"{path.name}: canvas must not shrink below 1920x1080, got {width}x{height}")

    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "exclusion-top-event-block"]
    if len(top_blocks) != 1:
        raise AssertionError(f"{path.name}: expected one exclusion-top-event-block, got {len(top_blocks)}")
    top_block = top_blocks[0]
    if not top_block.tag.endswith("rect") or not top_block.attrib.get("rx"):
        raise AssertionError(f"{path.name}: exclusion-top-event-block must be a rounded rect")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    for required_class in [
        "exclusion-checkpoint",
        "exclusion-pass-chip",
        "exclusion-fail-chip",
        "exclusion-fail-conclusion",
        "exclusion-final-pass",
    ]:
        if required_class not in classes:
            raise AssertionError(f"{path.name}: missing required class {required_class}")
    if "lucide-icon" not in classes:
        raise AssertionError(f"{path.name}: exclusion-tree checkpoint badges should use the shared lucide icon library")

    legends = [element for element in root.iter() if element.attrib.get("id") == "exclusion-tree-legend"]
    if len(legends) != 1:
        raise AssertionError(f"{path.name}: expected one exclusion-tree-legend, got {len(legends)}")

    detail_panels = [element for element in root.iter() if element.attrib.get("id") == "exclusion-event-detail-panel"]
    if len(detail_panels) != 1:
        raise AssertionError(f"{path.name}: expected one exclusion-event-detail-panel, got {len(detail_panels)}")

    how_to_use = [element for element in root.iter() if element.attrib.get("id") == "exclusion-how-to-use"]
    if len(how_to_use) != 1:
        raise AssertionError(f"{path.name}: expected one exclusion-how-to-use, got {len(how_to_use)}")

    checkpoint_groups = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-checkpoint" in element.attrib.get("class", "")
    ]
    fail_groups = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-fail-conclusion" in element.attrib.get("class", "")
    ]
    if len(checkpoint_groups) < 3:
        raise AssertionError(f"{path.name}: expected at least 3 checkpoints, got {len(checkpoint_groups)}")
    if len(fail_groups) != len(checkpoint_groups):
        raise AssertionError(f"{path.name}: expected one fail conclusion per checkpoint")

    verify_exclusion_chip_alignment(root, path.name)
    verify_exclusion_language_fidelity(root, path.name)
    verify_exclusion_text_boxes(root, path.name)
    verify_exclusion_legend_alignment(root, path.name)
    verify_exclusion_cause_card_layout(root, path.name)
    verify_exclusion_content_cards(root, path.name)
    verify_exclusion_final_alignment(root, path.name)
    verify_exclusion_rects_within_canvas(root, path.name)
    verify_exclusion_auxiliary_layout(root, path.name)
    drop_connectors = [
        element
        for element in root.iter()
        if element.tag.endswith("path") and "exclusion-fail-drop-connector" in element.attrib.get("class", "")
    ]
    if len(drop_connectors) != len(checkpoint_groups):
        raise AssertionError(f"{path.name}: expected one fail drop connector per checkpoint")
    for connector_path in drop_connectors:
        path_data = connector_path.attrib.get("d", "")
        if path_data.count("L") < 2:
            raise AssertionError(f"{path.name}: fail drop connector should include horizontal and vertical segments")
        numbers = parse_path_numbers(path_data)
        if len(numbers) >= 6:
            entry_y = numbers[5]
            if not any(rect_y + 8 <= entry_y <= rect_y + 20 for _, rect_y, _, _ in exclusion_rects(root, "exclusion-fail-conclusion")):
                raise AssertionError(f"{path.name}: fail connector arrow should enter inside the target card edge")
    verify_exclusion_fail_drop_lanes(drop_connectors, path.name)
    verify_exclusion_fail_connectors_avoid_cards(root, drop_connectors, path.name)
    fail_chip_connectors = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and element.attrib.get("marker-end") != "url(#arrowNavy)"
    ]
    if len(fail_chip_connectors) < len(checkpoint_groups):
        raise AssertionError(f"{path.name}: expected visible connector lines into fail chips")

    text = path.read_text(encoding="utf-8").lower()
    hits = [word for word in FORBIDDEN_WORDS if word in text]
    if hits:
        raise AssertionError(f"{path.name}: forbidden words found: {hits}")


def verify_two_by_two_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")
    verify_svg_font_style(root, path.name, require_arial=True)
    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if (width, height) != (1920, 1080):
        raise AssertionError(f"{path.name}: two-by-two matrix should keep 1920x1080 canvas, got {width}x{height}")

    groups_by_id = {element.attrib.get("id"): element for element in root.iter() if element.tag.endswith("g")}
    for required_id in ["two-by-two-matrix", "matrix-side-table", "matrix-legend"]:
        if required_id not in groups_by_id:
            raise AssertionError(f"{path.name}: missing {required_id}")
    if "matrix-usage-note" in groups_by_id:
        raise AssertionError(f"{path.name}: two-by-two matrix should not render the old default Best for note")

    quadrants = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "matrix-quadrant" in element.attrib.get("class", "")
    ]
    if len(quadrants) != 4:
        raise AssertionError(f"{path.name}: expected four matrix quadrants, got {len(quadrants)}")
    quadrant_keys = {group.attrib.get("data-quadrant") for group in quadrants}
    if quadrant_keys != {"top_left", "top_right", "bottom_left", "bottom_right"}:
        raise AssertionError(f"{path.name}: unexpected quadrant keys: {quadrant_keys}")

    markers = [
        element
        for element in root.iter()
        if element.tag.endswith("circle") and "matrix-item-marker" in element.attrib.get("class", "")
    ]
    if not markers:
        raise AssertionError(f"{path.name}: expected matrix item markers")
    if len(markers) > 20:
        raise AssertionError(f"{path.name}: matrix body should not show too many item markers")

    texts = [element.text or "" for element in root.iter() if element.tag.endswith("text")]
    joined = "\n".join(texts)
    bilingual_lines = [text for text in texts if " / " in text and re.search(r"[\u4e00-\u9fff]", text)]
    if bilingual_lines:
        raise AssertionError(f"{path.name}: two-by-two matrix should not auto-render bilingual labels: {bilingual_lines[:2]}")
    verify_two_by_two_axis_endpoint_labels(root, path.name)
    icons = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "lucide-icon" in element.attrib.get("class", "")
    ]
    if len(icons) < 4:
        raise AssertionError(f"{path.name}: expected Lucide badge icons in the quadrant headers")
    body_grid_lines = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and "matrix-table-body-grid" in element.attrib.get("class", "")
    ]
    if not body_grid_lines:
        raise AssertionError(f"{path.name}: expected row-aware table body grid lines")
    if not any(element.attrib.get("stroke") == "#C5D3E4" for element in body_grid_lines):
        raise AssertionError(f"{path.name}: zebra table rows should use higher-contrast body grid lines")
    row_separators = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and "matrix-table-row-separator" in element.attrib.get("class", "")
    ]
    if not row_separators:
        raise AssertionError(f"{path.name}: expected table row separators above zebra backgrounds")
    if not all(element.attrib.get("stroke") == "#C5D3E4" for element in row_separators):
        raise AssertionError(f"{path.name}: table row separators should stay visible on white and zebra rows")
    table_rows = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "matrix-table-row" in element.attrib.get("class", "")
    ]
    if len(table_rows) > 20:
        raise AssertionError(f"{path.name}: decision table should never render more than 20 rows")
    if "more in table" in joined:
        raise AssertionError(f"{path.name}: matrix body should not use old '+N more in table' copy")
    legend = groups_by_id.get("matrix-legend")
    if legend is not None:
        rects = [child for child in list(legend) if child.tag.endswith("rect")]
        if rects and float(rects[0].attrib.get("width", "0")) > 1000:
            raise AssertionError(f"{path.name}: priority guide should not cover the right-side table column")
    if path.name == "two-by-two.action-priority.output.svg":
        for required_text in ["Quick Wins", "Major Projects", "Fill-ins", "Time Sinks", "Effort", "Impact"]:
            if required_text not in joined:
                raise AssertionError(f"{path.name}: missing expected action-priority text: {required_text}")
    if path.name == "two-by-two.evidence-impact.output.svg":
        for required_text in ["Priority Causes", "Critical Hypotheses", "Evidence", "Impact"]:
            if required_text not in joined:
                raise AssertionError(f"{path.name}: missing expected evidence-impact text: {required_text}")
    if path.name == "two-by-two.value-feasibility.output.svg":
        if "High Feasibility" not in joined or "Build Now" not in joined:
            raise AssertionError(f"{path.name}: feasibility preset should keep the high-feasibility direction")

    verify_two_by_two_rects_within_canvas(root, path.name)


def verify_two_by_two_axis_endpoint_labels(root: ET.Element, label: str) -> None:
    endpoint_texts = []
    for element in root.iter():
        if not element.tag.endswith("text"):
            continue
        text = element.text or ""
        x = float(element.attrib.get("x", "-1"))
        y = float(element.attrib.get("y", "-1"))
        if abs(y - 840) <= 1 or (abs(x - 112) <= 1 and (abs(y - 802) <= 1 or abs(y - 194) <= 1)):
            endpoint_texts.append(text)
    if len(endpoint_texts) != 4:
        raise AssertionError(f"{label}: expected four axis endpoint labels, got {endpoint_texts}")
    allowed = {"Low", "High", "低", "高"}
    invalid = [text for text in endpoint_texts if text not in allowed]
    if invalid:
        raise AssertionError(f"{label}: axis endpoints should be generic Low/High labels, got {invalid}")


def verify_two_by_two_rects_within_canvas(root: ET.Element, label: str) -> None:
    canvas_width = float(root.attrib["width"])
    canvas_height = float(root.attrib["height"])
    for rect in root.iter():
        if not rect.tag.endswith("rect"):
            continue
        attrs = rect.attrib
        if not {"x", "y", "width", "height"} <= set(attrs):
            continue
        x = float(attrs["x"])
        y = float(attrs["y"])
        width = float(attrs["width"])
        height = float(attrs["height"])
        if x < -0.1 or y < -0.1 or x + width > canvas_width + 0.1 or y + height > canvas_height + 0.1:
            raise AssertionError(
                f"{label}: two-by-two rect outside canvas: x={x}, y={y}, w={width}, h={height}, canvas={canvas_width}x{canvas_height}"
            )


def verify_roadmap_timeline_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")
    verify_svg_font_style(root, path.name, require_arial=True)
    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width < 1920 or height < 1080:
        raise AssertionError(f"{path.name}: roadmap timeline should not shrink below 1920x1080, got {width}x{height}")

    groups_by_id = {element.attrib.get("id"): element for element in root.iter() if element.tag.endswith("g")}
    if "roadmap-timeline" not in groups_by_id:
        raise AssertionError(f"{path.name}: missing roadmap-timeline root group")
    if "roadmap-legend" not in groups_by_id:
        raise AssertionError(f"{path.name}: missing roadmap legend")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    if "roadmap-grid" in classes or "roadmap-lane" in classes:
        for required_class in ["roadmap-grid", "roadmap-lane", "roadmap-initiative"]:
            if required_class not in classes:
                raise AssertionError(f"{path.name}: missing required class {required_class}")
        for required_id in ["roadmap-lanes", "roadmap-initiatives", "roadmap-table"]:
            if required_id not in groups_by_id:
                raise AssertionError(f"{path.name}: missing {required_id}")
        if "lucide-icon" not in classes:
            raise AssertionError(f"{path.name}: swimlane roadmap lane badges should use Lucide icons")
        verify_roadmap_legend_clear_of_swimlane_header(root, path.name)
        verify_roadmap_lane_marker_band_sizing(root, path.name)
        verify_roadmap_swimlane_lane_labels(root, path.name)
        verify_roadmap_swimlane_initiative_labels(root, path.name)
        verify_roadmap_swimlane_marker_labels(root, path.name)
        verify_roadmap_swimlane_markers_avoid_bars(root, path.name)
        verify_roadmap_swimlane_marker_band_consistency(root, path.name)
        verify_roadmap_table_readable_text(root, path.name)
        verify_roadmap_swimlane_table_milestone_links(root, path.name)
    else:
        for required_class in ["roadmap-milestone"]:
            if required_class not in classes:
                raise AssertionError(f"{path.name}: missing required class {required_class}")
        if "roadmap-table" not in groups_by_id:
            raise AssertionError(f"{path.name}: milestone timeline should include the milestone table")
        verify_roadmap_milestone_timeline_layout(root, path.name)

    text = "\n".join(element.text or "" for element in root.iter() if element.tag.endswith("text"))
    bilingual_lines = [line for line in text.splitlines() if " / " in line and re.search(r"[\u4e00-\u9fff]", line)]
    if bilingual_lines:
        raise AssertionError(f"{path.name}: roadmap timeline should not auto-render bilingual labels: {bilingual_lines[:2]}")
    if "Roadmap across models A, B, and C" in text:
        raise AssertionError(f"{path.name}: roadmap title area should not render subtitle text")

    verify_roadmap_legend_layout(root, path.name)
    verify_roadmap_summary_layout(root, path.name)
    verify_roadmap_rects_within_canvas(root, path.name)


def verify_fmea_table_svg_basics(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")
    verify_svg_font_style(root, path.name, require_arial=True)
    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width < 1920 or height < 1080:
        raise AssertionError(f"{path.name}: FMEA table should not shrink below 1920x1080, got {width}x{height}")

    groups_by_id = {element.attrib.get("id"): element for element in root.iter() if element.tag.endswith("g")}
    for required_id in ["fmea-table", "fmea-main-table", "fmea-rating-scale", "fmea-priority-guide"]:
        if required_id not in groups_by_id:
            raise AssertionError(f"{path.name}: missing {required_id}")
    if "fmea-focus-guide" in groups_by_id:
        raise AssertionError(f"{path.name}: FMEA focus card should not duplicate RPN guidance")
    text = "\n".join(element.text or "" for element in root.iter() if element.tag.endswith("text"))
    for required_text in ["Item / Function", "Potential Failure Mode", "RPN", "Recommended Actions"]:
        if required_text not in text:
            raise AssertionError(f"{path.name}: missing FMEA header {required_text}")
    risk_cells = [
        element
        for element in root.iter()
        if element.attrib.get("class") == "fmea-risk-cell"
    ]
    if not risk_cells:
        raise AssertionError(f"{path.name}: missing RPN risk cells")
    risk_levels = {cell.attrib.get("data-risk-level") for cell in risk_cells}
    if path.name == "fmea.output.example.svg" and {"high", "medium", "low"} - risk_levels:
        raise AssertionError(f"{path.name}: expected high, medium, and low RPN risk examples")
    if path.name == "fmea.output.example.svg":
        expected_rpns = {"200", "112", "24"}
        actual_rpns = {cell.attrib.get("data-rpn") for cell in risk_cells}
        if not expected_rpns <= actual_rpns:
            raise AssertionError(f"{path.name}: RPN calculation mismatch, got {sorted(actual_rpns)}")
    score_cells = [
        element
        for element in root.iter()
        if element.attrib.get("class") == "fmea-score-cell"
    ]
    if len(score_cells) < len(risk_cells) * 3:
        raise AssertionError(f"{path.name}: S/O/D score cells should use explicit color-coded score text")
    status_badges = [
        element
        for element in root.iter()
        if element.attrib.get("class") == "fmea-status-badge"
    ]
    if len(status_badges) < len(risk_cells):
        raise AssertionError(f"{path.name}: status cells should render icon badges")
    grid_lines = [
        element
        for element in root.iter()
        if element.attrib.get("class") == "fmea-grid-line"
    ]
    if len(grid_lines) < 18:
        raise AssertionError(f"{path.name}: FMEA table grid should draw explicit overlay lines")
    verify_fmea_table_rects_within_canvas(root, path.name)


def verify_fmea_table_rects_within_canvas(root: ET.Element, label: str) -> None:
    width = float(root.attrib["width"])
    height = float(root.attrib["height"])
    for rect in root.iter():
        if not rect.tag.endswith("rect"):
            continue
        x = float(rect.attrib.get("x", "0"))
        y = float(rect.attrib.get("y", "0"))
        w = float(rect.attrib.get("width", "0"))
        h = float(rect.attrib.get("height", "0"))
        if x < -1 or y < -1 or x + w > width + 1 or y + h > height + 1:
            raise AssertionError(f"{label}: FMEA rect outside canvas at {x},{y},{w},{h}")


def verify_svg_font_style(root: ET.Element, label: str, *, require_arial: bool = False) -> None:
    for element in root.iter():
        weight = element.attrib.get("font-weight")
        if weight and weight not in ALLOWED_PRESENTATION_FONT_WEIGHTS:
            raise AssertionError(f"{label}: non-standard SVG font weight {weight} may render differently in PNG export")
        family = element.attrib.get("font-family")
        if require_arial and family and family != "Arial":
            raise AssertionError(f"{label}: expected Arial SVG font family, got {family}")


def verify_roadmap_legend_layout(root: ET.Element, label: str) -> None:
    legend = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-legend"), None)
    if legend is None:
        return
    rects = [child for child in list(legend) if child.tag.endswith("rect")]
    if not rects:
        raise AssertionError(f"{label}: roadmap legend missing background rect")
    rect = rects[0]
    bottom = float(rect.attrib.get("y", "0")) + float(rect.attrib.get("height", "0"))
    for text in legend.iter():
        if text.tag.endswith("text") and float(text.attrib.get("y", "0")) > bottom - 12:
            raise AssertionError(f"{label}: roadmap legend text collides with the bottom border")


def verify_roadmap_summary_layout(root: ET.Element, label: str) -> None:
    summary = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-summary-panel"), None)
    if summary is None:
        return
    rects = [child for child in list(summary) if child.tag.endswith("rect")]
    if not rects:
        raise AssertionError(f"{label}: roadmap summary panel missing background rect")
    rect = rects[0]
    bottom = float(rect.attrib.get("y", "0")) + float(rect.attrib.get("height", "0"))
    for text in summary.iter():
        if text.tag.endswith("text") and float(text.attrib.get("y", "0")) > bottom - 16:
            raise AssertionError(f"{label}: roadmap summary text should stay inside its card")


def verify_roadmap_legend_clear_of_swimlane_header(root: ET.Element, label: str) -> None:
    legend = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-legend"), None)
    header = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-time-header"), None)
    if legend is None or header is None:
        return
    legend_rects = [child for child in list(legend) if child.tag.endswith("rect")]
    header_rects = [child for child in list(header) if child.tag.endswith("rect")]
    if not legend_rects or not header_rects:
        return
    legend_bottom = max(float(rect.attrib.get("y", "0")) + float(rect.attrib.get("height", "0")) for rect in legend_rects)
    header_top = min(float(rect.attrib.get("y", "0")) for rect in header_rects)
    if header_top - legend_bottom < 24:
        raise AssertionError(f"{label}: swimlane time header should stay at least 24px below the legend")


def verify_roadmap_lane_marker_band_sizing(root: ET.Element, label: str) -> None:
    for lane_group in root.iter():
        if not lane_group.tag.endswith("g") or "roadmap-lane" not in lane_group.attrib.get("class", "").split():
            continue
        marker_band = lane_group.attrib.get("data-marker-band")
        row_count_text = lane_group.attrib.get("data-row-count")
        slot_count_text = lane_group.attrib.get("data-marker-slot-count")
        height_text = lane_group.attrib.get("data-lane-height")
        if marker_band not in {"true", "false"} or not row_count_text or slot_count_text is None or not height_text:
            raise AssertionError(f"{label}: roadmap lanes should expose marker-band sizing metadata")
        row_count = int(float(row_count_text))
        slot_count = int(float(slot_count_text))
        height = float(height_text)
        if (slot_count > 0) != (marker_band == "true"):
            raise AssertionError(f"{label}: roadmap marker-band metadata should match marker slot need")
        expected = SWIMLANE_BASE_H + (row_count - 1) * SWIMLANE_ROW_GAP + slot_count * SWIMLANE_MARKER_SLOT_GAP
        if abs(height - expected) > 0.1:
            raise AssertionError(f"{label}: roadmap lane height should depend on marker-band need, got {height}, expected {expected}")


def verify_roadmap_swimlane_lane_labels(root: ET.Element, label: str) -> None:
    lanes_group = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-lanes"), None)
    if lanes_group is None:
        return
    panel_rect = next((child for child in list(lanes_group) if child.tag.endswith("rect")), None)
    if panel_rect is None:
        return
    panel_right = float(panel_rect.attrib.get("x", "0")) + float(panel_rect.attrib.get("width", "0"))
    for lane_group in lanes_group.iter():
        if not lane_group.tag.endswith("g") or "roadmap-lane" not in lane_group.attrib.get("class", "").split():
            continue
        text = next((child for child in list(lane_group) if child.tag.endswith("text") and child.text), None)
        if text is None:
            raise AssertionError(f"{label}: roadmap lane missing visible lane label")
        x = float(text.attrib.get("x", "0"))
        font_size = float(text.attrib.get("font-size", "15"))
        estimated_right = x + visual_len(text.text or "") * font_size * 0.56
        if estimated_right > panel_right - 12:
            raise AssertionError(f"{label}: swimlane label should stay inside the lane panel")


def verify_roadmap_swimlane_initiative_labels(root: ET.Element, label: str) -> None:
    for group in root.iter():
        if not group.tag.endswith("g") or "roadmap-initiative" not in group.attrib.get("class", "").split():
            continue
        rect = next((child for child in list(group) if child.tag.endswith("rect")), None)
        text = next((child for child in list(group) if child.tag.endswith("text")), None)
        if rect is None or text is None:
            raise AssertionError(f"{label}: roadmap initiative missing bar or label")
        rect_x = float(rect.attrib.get("x", "0"))
        rect_w = float(rect.attrib.get("width", "0"))
        text_x = float(text.attrib.get("x", "0"))
        font_size = float(text.attrib.get("font-size", "13"))
        estimated_w = visual_len(text.text or "") * font_size * 0.56
        if text_x - estimated_w / 2 < rect_x + 4 or text_x + estimated_w / 2 > rect_x + rect_w - 4:
            raise AssertionError(f"{label}: initiative label should stay inside its bar")


def verify_roadmap_milestone_timeline_layout(root: ET.Element, label: str) -> None:
    axis_lines = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and element.attrib.get("marker-end") == "url(#arrowNavy)"
    ]
    if not axis_lines:
        return
    axis = axis_lines[0]
    axis_start = float(axis.attrib.get("x1", "0"))
    axis_y = float(axis.attrib.get("y1", "0"))
    axis_end = float(axis.attrib.get("x2", "0"))
    canvas_width = float(root.attrib["width"])
    left_margin = axis_start
    right_margin = canvas_width - axis_end
    if abs(left_margin - right_margin) > 1:
        raise AssertionError(f"{label}: milestone timeline axis margins should be balanced")

    phase_group = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-phases"), None)
    if phase_group is not None:
        for rect in phase_group.iter():
            if rect.tag.endswith("rect") and float(rect.attrib.get("y", "0")) <= axis_y:
                raise AssertionError(f"{label}: milestone phase bands should stay below the timeline axis")

    legend_rect = None
    legend_group = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-legend"), None)
    if legend_group is not None:
        for rect in legend_group.iter():
            if rect.tag.endswith("rect"):
                legend_rect = (
                    float(rect.attrib.get("x", "0")),
                    float(rect.attrib.get("y", "0")),
                    float(rect.attrib.get("width", "0")),
                    float(rect.attrib.get("height", "0")),
                )
                break

    milestone_group = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-milestones"), None)
    if milestone_group is not None:
        card_rects = []
        for rect in milestone_group.iter():
            if rect.tag.endswith("rect"):
                card_rect = (
                    float(rect.attrib.get("x", "0")),
                    float(rect.attrib.get("y", "0")),
                    float(rect.attrib.get("width", "0")),
                    float(rect.attrib.get("height", "0")),
                )
                card_rects.append(card_rect)
                rect_bottom = float(rect.attrib.get("y", "0")) + float(rect.attrib.get("height", "0"))
                if rect_bottom >= axis_y:
                    raise AssertionError(f"{label}: milestone detail cards should stay above the timeline axis")
                if legend_rect and rects_overlap(card_rect, legend_rect, 0):
                    raise AssertionError(f"{label}: milestone detail cards should not overlap the legend")
        for index, first in enumerate(card_rects):
            fx, fy, fw, fh = first
            for second in card_rects[index + 1:]:
                sx, sy, sw, sh = second
                if rects_overlap(first, second, 0):
                    raise AssertionError(f"{label}: milestone detail cards should not overlap")


def verify_roadmap_swimlane_marker_labels(root: ET.Element, label: str) -> None:
    header = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-time-header"), None)
    if header is None:
        return
    rects = [child for child in list(header) if child.tag.endswith("rect")]
    if not rects:
        return
    header_bottom = max(float(rect.attrib.get("y", "0")) + float(rect.attrib.get("height", "0")) for rect in rects)
    marker_groups = [
        element
        for element in root.iter()
        if element.tag.endswith("g")
        and (
            "roadmap-milestone" in element.attrib.get("class", "")
            or "roadmap-decision" in element.attrib.get("class", "")
        )
    ]
    for group in marker_groups:
        for text in group.iter():
            if text.tag.endswith("text") and float(text.attrib.get("y", "0")) < header_bottom + 14:
                raise AssertionError(f"{label}: swimlane milestone labels should stay out of the time header")


def verify_roadmap_swimlane_markers_avoid_bars(root: ET.Element, label: str) -> None:
    initiative_rects: list[tuple[float, float, float, float]] = []
    marker_points: list[tuple[float, float]] = []
    for group in root.iter():
        if not group.tag.endswith("g"):
            continue
        class_name = group.attrib.get("class", "")
        if "roadmap-initiative" in class_name:
            for rect in list(group):
                if rect.tag.endswith("rect"):
                    initiative_rects.append(
                        (
                            float(rect.attrib.get("x", "0")),
                            float(rect.attrib.get("y", "0")),
                            float(rect.attrib.get("width", "0")),
                            float(rect.attrib.get("height", "0")),
                        )
                    )
        if "roadmap-milestone" in class_name or "roadmap-decision" in class_name:
            for shape in list(group):
                if shape.tag.endswith("circle"):
                    marker_points.append((float(shape.attrib.get("cx", "0")), float(shape.attrib.get("cy", "0"))))
                elif shape.tag.endswith("polygon"):
                    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", shape.attrib.get("points", ""))]
                    if values:
                        xs = values[0::2]
                        ys = values[1::2]
                        marker_points.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    for marker_x, marker_y in marker_points:
        for x, y, width, height in initiative_rects:
            if x - 6 <= marker_x <= x + width + 6 and y - 6 <= marker_y <= y + height + 6:
                raise AssertionError(f"{label}: swimlane milestone marker should not collide with initiative bars")


def verify_roadmap_swimlane_marker_band_consistency(root: ET.Element, label: str) -> None:
    marker_rects_by_lane: dict[str, list[tuple[float, float, float, float]]] = {}
    for group in root.iter():
        if not group.tag.endswith("g"):
            continue
        class_name = group.attrib.get("class", "")
        if "roadmap-milestone" not in class_name and "roadmap-decision" not in class_name:
            continue
        lane_id = group.attrib.get("data-lane-id", "")
        if not lane_id:
            continue
        rect = roadmap_marker_label_rect(group)
        if rect is not None:
            marker_rects_by_lane.setdefault(lane_id, []).append(rect)
    for lane_id, rects in marker_rects_by_lane.items():
        for index, first in enumerate(rects):
            for second in rects[index + 1:]:
                if rects_overlap(first, second, 2):
                    raise AssertionError(f"{label}: swimlane markers and decisions in lane {lane_id} should not overlap")


def roadmap_marker_label_rect(group: ET.Element) -> tuple[float, float, float, float] | None:
    center: tuple[float, float] | None = None
    label_text = ""
    label_x = 0.0
    label_y = 0.0
    for child in list(group):
        if child.tag.endswith("circle"):
            center = (float(child.attrib.get("cx", "0")), float(child.attrib.get("cy", "0")))
        elif child.tag.endswith("polygon"):
            values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", child.attrib.get("points", ""))]
            if values:
                xs = values[0::2]
                ys = values[1::2]
                center = (sum(xs) / len(xs), sum(ys) / len(ys))
        elif child.tag.endswith("text"):
            label_text = child.text or ""
            label_x = float(child.attrib.get("x", "0"))
            label_y = float(child.attrib.get("y", "0"))
    if center is None:
        return None
    cx, cy = center
    text_right = label_x + visual_len(label_text) * 6.8
    left = min(cx - 12, label_x)
    top = min(cy - 12, label_y - 13)
    right = max(cx + 12, text_right)
    bottom = max(cy + 12, label_y + 3)
    return (left, top, right - left, bottom - top)


def verify_roadmap_table_readable_text(root: ET.Element, label: str) -> None:
    table = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-table"), None)
    if table is None:
        return
    font_sizes = [
        float(element.attrib.get("font-size", "0"))
        for element in table.iter()
        if element.tag.endswith("text")
    ]
    if font_sizes and min(font_sizes) < 13:
        raise AssertionError(f"{label}: roadmap table text should not be smaller than 13px")


def verify_roadmap_swimlane_table_milestone_links(root: ET.Element, label: str) -> None:
    if label != "roadmap.swimlane.output.svg":
        return
    table = next((element for element in root.iter() if element.attrib.get("id") == "roadmap-table"), None)
    if table is None:
        raise AssertionError(f"{label}: missing roadmap table")
    table_text = "\n".join(element.text or "" for element in table.iter() if element.tag.endswith("text"))
    for expected in ["M1: Model A Launch", "M2: DVT Complete"]:
        if expected not in table_text:
            raise AssertionError(f"{label}: swimlane initiative table should link related key milestones, missing {expected}")


def verify_roadmap_rects_within_canvas(root: ET.Element, label: str) -> None:
    canvas_width = float(root.attrib["width"])
    canvas_height = float(root.attrib["height"])
    for rect in root.iter():
        if not rect.tag.endswith("rect"):
            continue
        attrs = rect.attrib
        if not {"x", "y", "width", "height"} <= set(attrs):
            continue
        x = float(attrs["x"])
        y = float(attrs["y"])
        width = float(attrs["width"])
        height = float(attrs["height"])
        if x < -0.1 or y < -0.1 or x + width > canvas_width + 0.1 or y + height > canvas_height + 0.1:
            raise AssertionError(
                f"{label}: roadmap rect outside canvas: x={x}, y={y}, w={width}, h={height}, canvas={canvas_width}x{canvas_height}"
            )


def verify_exclusion_chip_alignment(root: ET.Element, label: str) -> None:
    def chip_rect_y(class_name: str) -> list[float]:
        values: list[float] = []
        for group in root.iter():
            if not group.tag.endswith("g") or class_name not in group.attrib.get("class", ""):
                continue
            rects = [child for child in list(group) if child.tag.endswith("rect")]
            if rects:
                values.append(float(rects[0].attrib.get("y", "0")))
        return sorted(values)

    pass_y = chip_rect_y("exclusion-pass-chip")
    fail_y = chip_rect_y("exclusion-fail-chip")
    if len(pass_y) != len(fail_y):
        raise AssertionError(f"{label}: pass/fail chip counts differ: {len(pass_y)} vs {len(fail_y)}")
    for index, (pass_value, fail_value) in enumerate(zip(pass_y, fail_y), start=1):
        if abs(pass_value - fail_value) > 0.1:
            raise AssertionError(f"{label}: pass/fail chips for checkpoint {index} are not horizontally aligned")


def verify_exclusion_text_boxes(root: ET.Element, label: str) -> None:
    groups = [
        element
        for element in root.iter()
        if element.tag.endswith("g")
        and (
            "exclusion-checkpoint" in element.attrib.get("class", "")
            or "exclusion-top-event" in element.attrib.get("class", "")
        )
    ]
    for group in groups:
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        texts = [child for child in list(group) if child.tag.endswith("text")]
        if not rects or not texts:
            continue
        rect = rects[0]
        rect_y = float(rect.attrib.get("y", "0"))
        rect_h = float(rect.attrib.get("height", "0"))
        text_ys = [float(text.attrib.get("y", "0")) for text in texts]
        top_gap = min(text_ys) - rect_y
        bottom_gap = rect_y + rect_h - max(text_ys)
        if abs(top_gap - bottom_gap) > 10:
            raise AssertionError(f"{label}: top/checkpoint text should be vertically balanced")
        for text in texts:
            text_y = float(text.attrib.get("y", "0"))
            if text_y < rect_y + 20 or text_y > rect_y + rect_h - 12:
                raise AssertionError(f"{label}: top/checkpoint text should stay inside its content-sized card")


def verify_exclusion_language_fidelity(root: ET.Element, label: str) -> None:
    content_texts: list[str] = []
    for group in root.iter():
        if not group.tag.endswith("g"):
            continue
        class_name = group.attrib.get("class", "")
        if not any(
            token in class_name
            for token in [
                "exclusion-top-event",
                "exclusion-checkpoint",
                "exclusion-fail-conclusion",
                "exclusion-final-pass",
                "exclusion-pass-chip",
                "exclusion-fail-chip",
            ]
        ):
            continue
        content_texts.extend(child.text or "" for child in list(group) if child.tag.endswith("text"))
    bilingual_lines = [text for text in content_texts if " / " in text]
    if bilingual_lines:
        raise AssertionError(f"{label}: exclusion-tree content should not auto-render bilingual labels: {bilingual_lines[:2]}")


def verify_exclusion_legend_alignment(root: ET.Element, label: str) -> None:
    legends = [element for element in root.iter() if element.attrib.get("id") == "exclusion-tree-legend"]
    if not legends:
        return
    rows: list[tuple[float, float]] = []
    for child in list(legends[0]):
        if not child.tag.endswith("text"):
            continue
        text = child.text or ""
        if text == "Legend":
            continue
        if float(child.attrib.get("x", "0")) < 1620:
            continue
        rows.append((float(child.attrib.get("y", "0")), 0.0))
    expected_centers = [126.0, 202.0, 278.0, 354.0, 430.0]
    label_ys = [row[0] for row in rows[:5]]
    if len(label_ys) < 5:
        raise AssertionError(f"{label}: legend should include five aligned labels")
    for text_y, center_y in zip(label_ys, expected_centers):
        if abs((text_y - 6) - center_y) > 1:
            raise AssertionError(f"{label}: legend labels should align with icon centers")


def verify_exclusion_cause_card_layout(root: ET.Element, label: str) -> None:
    fail_card_rects: list[tuple[float, float, float, float]] = []
    for group in root.iter():
        if not group.tag.endswith("g") or "exclusion-fail-conclusion" not in group.attrib.get("class", ""):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if rects:
            rect = rects[0]
            fail_card_rects.append(
                (
                    float(rect.attrib.get("x", "0")),
                    float(rect.attrib.get("y", "0")),
                    float(rect.attrib.get("width", "0")),
                    float(rect.attrib.get("height", "0")),
                )
            )
    fail_card_x_values = [rect[0] for rect in fail_card_rects]
    if len(fail_card_x_values) >= 3 and len(set(round(value, 1) for value in fail_card_x_values)) < 2:
        raise AssertionError(f"{label}: fail conclusion cards should not all share one x column")
    for previous_x, next_x in zip(fail_card_x_values, fail_card_x_values[1:]):
        if next_x > previous_x + 0.1:
            raise AssertionError(f"{label}: fail conclusion cards should step from upper-right to lower-left")
    for previous, current in zip(fail_card_rects, fail_card_rects[1:]):
        previous_bottom = previous[1] + previous[3]
        if current[1] < previous_bottom + 18:
            raise AssertionError(f"{label}: fail conclusion cards should not vertically collide")


def verify_exclusion_content_cards(root: ET.Element, label: str) -> None:
    final_heights = []
    final_rects: list[tuple[float, float, float, float]] = []
    fail_rects: list[tuple[float, float, float, float]] = []
    fail_heights = []
    detail_heights = []
    final_text_lines: list[str] = []
    bottom_gaps: list[tuple[str, float]] = []
    for group in root.iter():
        class_name = group.attrib.get("class", "")
        group_id = group.attrib.get("id", "")
        if not group.tag.endswith("g"):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            continue
        height = float(rects[0].attrib.get("height", "0"))
        texts = [child for child in list(group) if child.tag.endswith("text")]
        if texts and (
            "exclusion-final-pass" in class_name
            or "exclusion-fail-conclusion" in class_name
            or (group_id == "exclusion-event-detail-panel" and height > 220)
        ):
            rect_y = float(rects[0].attrib.get("y", "0"))
            last_text_y = max(float(child.attrib.get("y", "0")) for child in texts)
            bottom_gaps.append((class_name or group_id, rect_y + float(rects[0].attrib.get("height", "0")) - last_text_y))
        if "exclusion-final-pass" in class_name:
            final_heights.append(height)
            final_rects.append(
                (
                    float(rects[0].attrib.get("x", "0")),
                    float(rects[0].attrib.get("y", "0")),
                    float(rects[0].attrib.get("width", "0")),
                    height,
                )
            )
            final_text_lines.extend((child.text or "") for child in list(group) if child.tag.endswith("text"))
        elif "exclusion-fail-conclusion" in class_name:
            fail_heights.append(height)
            fail_width = float(rects[0].attrib.get("width", "0"))
            fail_rects.append(
                (
                    float(rects[0].attrib.get("x", "0")),
                    float(rects[0].attrib.get("y", "0")),
                    fail_width,
                    height,
                )
            )
            if fail_width < 360:
                raise AssertionError(f"{label}: fail conclusion cards should be wide enough for readable details")
        elif group_id == "exclusion-event-detail-panel":
            detail_heights.append(height)
    if not final_heights or final_heights[0] < 96:
        raise AssertionError(f"{label}: final pass card should keep enough height for its content")
    if final_rects and final_rects[0][2] < 460:
        raise AssertionError(f"{label}: final pass card should be wider than cause cards")
    if fail_heights and min(fail_heights) < 96:
        raise AssertionError(f"{label}: fail conclusion cards should keep enough height for their content")
    if detail_heights and detail_heights[0] < 220:
        raise AssertionError(f"{label}: event detail panel should preserve the minimum content height")
    large_bottom_gaps = [(name, gap) for name, gap in bottom_gaps if gap > 36]
    if large_bottom_gaps:
        raise AssertionError(f"{label}: content card bottom padding should stay compact: {large_bottom_gaps[:2]}")
    if final_rects:
        for fail_rect in fail_rects:
            if rects_overlap(final_rects[0], fail_rect, 24):
                raise AssertionError(f"{label}: final pass card should not collide with fail conclusion cards")
        final_line_limit = int((final_rects[0][2] - 106) / 7) + 2
        long_final_lines = [line for line in final_text_lines if visual_len(line) > final_line_limit]
        if long_final_lines:
            raise AssertionError(f"{label}: final pass card text should wrap within the card: {long_final_lines[:2]}")

    final_connectors = [
        element
        for element in root.iter()
        if element.tag.endswith("path") and "exclusion-final-pass-connector" in element.attrib.get("class", "")
    ]
    if len(final_connectors) != 1:
        raise AssertionError(f"{label}: expected one final pass connector")
    path_numbers = parse_path_numbers(final_connectors[0].attrib.get("d", ""))
    x_values = path_numbers[0::2]
    if len(set(round(value, 1) for value in x_values)) != 1:
        raise AssertionError(f"{label}: final pass connector should drop straight into the final card")
    if final_rects:
        final_x, final_y, final_w, _ = final_rects[0]
        final_anchor_x = x_values[0]
        if not (final_x <= final_anchor_x <= final_x + final_w):
            raise AssertionError(f"{label}: final pass connector should enter within final card width")
        fail_bottoms = []
        for group in root.iter():
            if not group.tag.endswith("g") or "exclusion-fail-conclusion" not in group.attrib.get("class", ""):
                continue
            rects = [child for child in list(group) if child.tag.endswith("rect")]
            if rects:
                fail_bottoms.append(float(rects[0].attrib.get("y", "0")) + float(rects[0].attrib.get("height", "0")))
        if fail_bottoms and final_y > max(fail_bottoms) + 20:
            raise AssertionError(f"{label}: final pass card should not be pushed below unrelated fail cards")


def verify_exclusion_final_alignment(root: ET.Element, label: str) -> None:
    checkpoint_rects = exclusion_rects(root, "exclusion-checkpoint")
    fail_rects = exclusion_rects(root, "exclusion-fail-conclusion")
    final_rects = exclusion_rects(root, "exclusion-final-pass")
    if not checkpoint_rects or not fail_rects or not final_rects:
        return
    last_checkpoint = checkpoint_rects[-1]
    last_fail = fail_rects[-1]
    final_rect = final_rects[0]
    if abs(final_rect[0] - last_checkpoint[0]) > 1.0:
        raise AssertionError(f"{label}: final pass card should align with the last checkpoint left edge")
    corridor = last_fail[0] - (final_rect[0] + final_rect[2])
    if corridor < 24:
        raise AssertionError(f"{label}: final pass card should preserve a corridor before the last fail card")


def verify_exclusion_rects_within_canvas(root: ET.Element, label: str) -> None:
    canvas_width = float(root.attrib["width"])
    canvas_height = float(root.attrib["height"])
    for rect in root.iter():
        if not rect.tag.endswith("rect"):
            continue
        attrs = rect.attrib
        if not {"x", "y", "width", "height"} <= set(attrs):
            continue
        x = float(attrs["x"])
        y = float(attrs["y"])
        width = float(attrs["width"])
        height = float(attrs["height"])
        if x < -0.1 or y < -0.1 or x + width > canvas_width + 0.1 or y + height > canvas_height + 0.1:
            raise AssertionError(
                f"{label}: exclusion-tree rect outside canvas: x={x}, y={y}, w={width}, h={height}, canvas={canvas_width}x{canvas_height}"
            )


def verify_exclusion_fail_drop_lanes(drop_connectors: list[ET.Element], label: str) -> None:
    vertical_segments: list[tuple[float, float, float]] = []
    for connector_path in drop_connectors:
        numbers = parse_path_numbers(connector_path.attrib.get("d", ""))
        if len(numbers) < 6:
            continue
        drop_x = numbers[4]
        y1 = min(numbers[3], numbers[5])
        y2 = max(numbers[3], numbers[5])
        vertical_segments.append((drop_x, y1, y2))

    for index, previous in enumerate(vertical_segments):
        for current in vertical_segments[index + 1 :]:
            same_lane = abs(previous[0] - current[0]) <= 0.1
            overlap = min(previous[2], current[2]) - max(previous[1], current[1])
            if same_lane and overlap > 1:
                raise AssertionError(f"{label}: fail drop connectors should not overlap in the same vertical lane")


def verify_exclusion_fail_connectors_avoid_cards(root: ET.Element, drop_connectors: list[ET.Element], label: str) -> None:
    clearance = 24.0
    fail_rects = exclusion_rects(root, "exclusion-fail-conclusion")
    final_rects = exclusion_rects(root, "exclusion-final-pass")
    for index, connector_path in enumerate(drop_connectors):
        segments = orthogonal_segments(connector_path.attrib.get("d", ""))
        obstacles = [rect for rect_index, rect in enumerate(fail_rects) if rect_index != index]
        obstacles.extend(final_rects)
        for segment in segments:
            for rect in obstacles:
                if segment_hits_rect(segment, rect, clearance):
                    raise AssertionError(f"{label}: fail connector {index + 1} intersects a content card")


def exclusion_rects(root: ET.Element, class_name: str) -> list[tuple[float, float, float, float]]:
    rects: list[tuple[float, float, float, float]] = []
    for group in root.iter():
        if not group.tag.endswith("g") or class_name not in group.attrib.get("class", ""):
            continue
        child_rects = [child for child in list(group) if child.tag.endswith("rect")]
        if child_rects:
            rect = child_rects[0]
            rects.append(
                (
                    float(rect.attrib.get("x", "0")),
                    float(rect.attrib.get("y", "0")),
                    float(rect.attrib.get("width", "0")),
                    float(rect.attrib.get("height", "0")),
                )
            )
    return rects


def orthogonal_segments(path_data: str) -> list[tuple[float, float, float, float]]:
    numbers = parse_path_numbers(path_data)
    points = list(zip(numbers[0::2], numbers[1::2]))
    return [
        (x1, y1, x2, y2)
        for (x1, y1), (x2, y2) in zip(points, points[1:])
        if abs(x1 - x2) < 0.1 or abs(y1 - y2) < 0.1
    ]


def segment_hits_rect(segment: tuple[float, float, float, float], rect: tuple[float, float, float, float], margin: float) -> bool:
    x1, y1, x2, y2 = segment
    rect_x, rect_y, rect_w, rect_h = rect
    left = rect_x - margin
    right = rect_x + rect_w + margin
    top = rect_y - margin
    bottom = rect_y + rect_h + margin
    if abs(y1 - y2) < 0.1:
        seg_left = min(x1, x2)
        seg_right = max(x1, x2)
        return top < y1 < bottom and seg_left < right and seg_right > left
    if abs(x1 - x2) < 0.1:
        seg_top = min(y1, y2)
        seg_bottom = max(y1, y2)
        return left < x1 < right and seg_top < bottom and seg_bottom > top
    return False


def rects_overlap(first: tuple[float, float, float, float], second: tuple[float, float, float, float], margin: float) -> bool:
    first_x, first_y, first_w, first_h = first
    second_x, second_y, second_w, second_h = second
    return (
        first_x < second_x + second_w + margin
        and first_x + first_w > second_x - margin
        and first_y < second_y + second_h + margin
        and first_y + first_h > second_y - margin
    )


def visual_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in text)


def verify_exclusion_auxiliary_layout(root: ET.Element, label: str) -> None:
    decorative_dots = [
        element
        for element in root.iter()
        if element.tag.endswith("circle") and element.attrib.get("fill", "").lower() == "#d8e7f6"
    ]
    if decorative_dots:
        raise AssertionError(f"{label}: decorative dots should not be placed near exclusion-tree content")

    how_to_use = [element for element in root.iter() if element.attrib.get("id") == "exclusion-how-to-use"]
    if len(how_to_use) != 1:
        return
    how_rects = [child for child in list(how_to_use[0]) if child.tag.endswith("rect")]
    if not how_rects:
        raise AssertionError(f"{label}: how-to-use panel missing rect")
    how_rect = how_rects[0]
    how_x = float(how_rect.attrib.get("x", "0"))
    how_y = float(how_rect.attrib.get("y", "0"))
    how_w = float(how_rect.attrib.get("width", "0"))

    legend_bottom = 0.0
    legends = [element for element in root.iter() if element.attrib.get("id") == "exclusion-tree-legend"]
    if legends:
        legend_rects = [child for child in list(legends[0]) if child.tag.endswith("rect")]
        if legend_rects:
            legend_bottom = float(legend_rects[0].attrib.get("y", "0")) + float(legend_rects[0].attrib.get("height", "0"))

    required_y = legend_bottom + 36
    for group in root.iter():
        if not group.tag.endswith("g") or "exclusion-fail-conclusion" not in group.attrib.get("class", ""):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            continue
        rect = rects[0]
        x = float(rect.attrib.get("x", "0"))
        y = float(rect.attrib.get("y", "0"))
        w = float(rect.attrib.get("width", "0"))
        h = float(rect.attrib.get("height", "0"))
        if x < how_x + how_w + 28 and x + w > how_x - 28:
            required_y = max(required_y, y + h + 36)

    if abs(how_y - required_y) > 1.0:
        raise AssertionError(f"{label}: how-to-use panel should sit at the highest non-colliding right-side position")


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


def verify_fault_tree_event_text_integrity(root: ET.Element, label: str) -> None:
    protected_classes = [
        "fault-top-event",
        "fault-intermediate-event",
        "fault-basic-event",
    ]
    for group in root.iter():
        if not group.tag.endswith("g"):
            continue
        class_name = group.attrib.get("class", "")
        if not any(token in class_name for token in protected_classes):
            continue
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        texts = [child for child in list(group) if child.tag.endswith("text")]
        if not rects:
            raise AssertionError(f"{label}: fault event group missing rect")
        rect = rects[0]
        rect_y = float(rect.attrib.get("y", "0"))
        rect_h = float(rect.attrib.get("height", "0"))
        for text in texts:
            value = text.text or ""
            if "..." in value:
                raise AssertionError(f"{label}: fault event text must not be ellipsized: {value}")
            text_y = float(text.attrib.get("y", "0"))
            if text_y < rect_y + 16 or text_y > rect_y + rect_h - 8:
                raise AssertionError(f"{label}: fault event text should stay inside its content-sized card")


def verify_fault_tree_connectors_avoid_top_block(root: ET.Element, label: str) -> None:
    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "top-event-block"]
    if len(top_blocks) != 1:
        return
    top = top_blocks[0]
    top_x = float(top.attrib.get("x", "0"))
    top_y = float(top.attrib.get("y", "0"))
    top_w = float(top.attrib.get("width", "0"))
    top_h = float(top.attrib.get("height", "0"))
    top_right = top_x + top_w
    top_bottom = top_y + top_h

    for line in root.iter():
        if not line.tag.endswith("line"):
            continue
        x1 = float(line.attrib.get("x1", "0"))
        x2 = float(line.attrib.get("x2", "0"))
        y1 = float(line.attrib.get("y1", "0"))
        y2 = float(line.attrib.get("y2", "0"))
        if abs(y1 - y2) > 0.1:
            continue
        line_left = min(x1, x2)
        line_right = max(x1, x2)
        overlaps_top_x = line_left < top_right and line_right > top_x
        crosses_top_y = top_y < y1 < top_bottom
        if overlaps_top_x and crosses_top_y:
            raise AssertionError(f"{label}: horizontal connector crosses through the top event block")


def verify_fault_tree_nested_gates(path: Path) -> None:
    root = ET.parse(path).getroot()
    svg_text = path.read_text(encoding="utf-8")
    required_labels = [
        "Power Path Issue",
        "Fuse Opens Under Startup",
        "Surge",
        "Control Path Issue",
        "Ready Signal Not Detected",
    ]
    missing = [label for label in required_labels if label not in svg_text]
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


def verify_fault_tree_eight_branches(path: Path) -> None:
    root = ET.parse(path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError(f"{path.name}: root is not svg")

    svg_text = path.read_text(encoding="utf-8")
    required_labels = [
        "Laser Source",
        "Instability",
        "Optical Coupling",
        "Drift",
        "Thermal Control",
        "Failure",
        "Electrical Drive",
        "Abnormality",
        "Package Mechanical",
        "Stress",
        "Material Process",
        "Weakness",
        "External Environment",
        "Overstress",
        "Measurement System",
        "Error",
    ]
    missing = [label for label in required_labels if label not in svg_text]
    if missing:
        raise AssertionError(f"{path.name}: expected all eight first-level branches to render, missing labels: {missing}")

    intermediate_events = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "fault-intermediate-event" in element.attrib.get("class", "")
    ]
    if len(intermediate_events) != 8:
        raise AssertionError(f"{path.name}: expected 8 first-level intermediate events, got {len(intermediate_events)}")

    svg_text = path.read_text(encoding="utf-8")
    if "only the first" in svg_text:
        raise AssertionError(f"{path.name}: fault tree must not truncate eight first-level branches")
    verify_fault_tree_branch_connectors(root, path.name, min_trunks=8, min_branches=16)


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


def two_by_two_template_paths() -> list[Path]:
    paths = [
        TEMPLATES / "two-by-two-matrix.template.md",
        TEMPLATES / "two-by-two-matrix.template.json",
    ]
    for preset in TWO_BY_TWO_TEMPLATE_PRESETS:
        if preset == "action_priority":
            continue
        slug = preset.replace("_", "-")
        paths.append(TEMPLATES / f"two-by-two-matrix.{slug}.template.md")
        paths.append(TEMPLATES / f"two-by-two-matrix.{slug}.template.json")
    return paths


def roadmap_template_paths() -> list[Path]:
    return [
        TEMPLATES / "roadmap-timeline.template.md",
        TEMPLATES / "roadmap-timeline.template.json",
        TEMPLATES / "roadmap-timeline.swimlane-roadmap.template.md",
        TEMPLATES / "roadmap-timeline.swimlane-roadmap.template.json",
        TEMPLATES / "roadmap-timeline.milestone-timeline.template.md",
        TEMPLATES / "roadmap-timeline.milestone-timeline.template.json",
    ]


def verify_templates() -> None:
    md_template = TEMPLATES / "fishbone.template.md"
    json_template = TEMPLATES / "fishbone.template.json"
    fault_tree_md_template = TEMPLATES / "fault-tree.template.md"
    fault_tree_json_template = TEMPLATES / "fault-tree.template.json"
    exclusion_tree_md_template = TEMPLATES / "exclusion-tree.template.md"
    exclusion_tree_json_template = TEMPLATES / "exclusion-tree.template.json"
    two_by_two_templates = two_by_two_template_paths()
    roadmap_templates = roadmap_template_paths()
    fmea_md_template = TEMPLATES / "fmea-table.template.md"
    fmea_json_template = TEMPLATES / "fmea-table.template.json"
    two_by_two_md_template = TEMPLATES / "two-by-two-matrix.template.md"
    two_by_two_json_template = TEMPLATES / "two-by-two-matrix.template.json"
    for path in [
        md_template,
        json_template,
        fault_tree_md_template,
        fault_tree_json_template,
        exclusion_tree_md_template,
        exclusion_tree_json_template,
        *two_by_two_templates,
        *roadmap_templates,
        fmea_md_template,
        fmea_json_template,
    ]:
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

    exclusion_md_data = parse_input(exclusion_tree_md_template)
    verify_exclusion_tree_template_structure(exclusion_md_data, exclusion_tree_md_template.name)

    exclusion_json_data = json.loads(exclusion_tree_json_template.read_text(encoding="utf-8"))
    if not isinstance(exclusion_json_data, dict):
        raise AssertionError(f"{exclusion_tree_json_template.name}: JSON template must be an object")
    verify_exclusion_tree_template_structure(exclusion_json_data, exclusion_tree_json_template.name)

    for template_path in two_by_two_templates:
        if template_path.suffix == ".md":
            two_by_two_data = parse_input(template_path)
        else:
            two_by_two_data = json.loads(template_path.read_text(encoding="utf-8"))
            if not isinstance(two_by_two_data, dict):
                raise AssertionError(f"{template_path.name}: JSON template must be an object")
        verify_two_by_two_template_structure(two_by_two_data, template_path.name)
        verify_two_by_two_template_guidance(template_path, two_by_two_data)

    for template_path in roadmap_templates:
        if template_path.suffix == ".md":
            roadmap_data = parse_input(template_path)
        else:
            roadmap_data = json.loads(template_path.read_text(encoding="utf-8"))
            if not isinstance(roadmap_data, dict):
                raise AssertionError(f"{template_path.name}: JSON template must be an object")
        verify_roadmap_template_structure(roadmap_data, template_path.name)

    fmea_md_data = parse_input(fmea_md_template)
    verify_fmea_template_structure(fmea_md_data, fmea_md_template.name)

    fmea_json_data = json.loads(fmea_json_template.read_text(encoding="utf-8"))
    if not isinstance(fmea_json_data, dict):
        raise AssertionError(f"{fmea_json_template.name}: JSON template must be an object")
    verify_fmea_template_structure(fmea_json_data, fmea_json_template.name)

    pid = os.getpid()
    template_outputs = [
        TEMPLATES / f"fishbone.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fishbone.template.json.{pid}.tmp.svg",
        TEMPLATES / f"fault-tree.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fault-tree.template.json.{pid}.tmp.svg",
        TEMPLATES / f"exclusion-tree.template.md.{pid}.tmp.svg",
        TEMPLATES / f"exclusion-tree.template.json.{pid}.tmp.svg",
        *[TEMPLATES / f"{path.name}.{pid}.tmp.svg" for path in two_by_two_templates],
        *[TEMPLATES / f"{path.name}.{pid}.tmp.svg" for path in roadmap_templates],
        TEMPLATES / f"fmea-table.template.md.{pid}.tmp.svg",
        TEMPLATES / f"fmea-table.template.json.{pid}.tmp.svg",
    ]
    try:
        run_generate(md_template, template_outputs[0])
        run_generate(json_template, template_outputs[1])
        run_generate(fault_tree_md_template, template_outputs[2])
        run_generate(fault_tree_json_template, template_outputs[3])
        run_generate(exclusion_tree_md_template, template_outputs[4])
        run_generate(exclusion_tree_json_template, template_outputs[5])
        two_by_two_output_start = 6
        two_by_two_output_end = two_by_two_output_start + len(two_by_two_templates)
        roadmap_output_start = two_by_two_output_end
        roadmap_output_end = roadmap_output_start + len(roadmap_templates)
        fmea_output_start = roadmap_output_end
        for template_path, output_path in zip(two_by_two_templates, template_outputs[two_by_two_output_start:two_by_two_output_end]):
            run_generate(template_path, output_path)
        for template_path, output_path in zip(roadmap_templates, template_outputs[roadmap_output_start:roadmap_output_end]):
            run_generate(template_path, output_path)
        run_generate(fmea_md_template, template_outputs[fmea_output_start])
        run_generate(fmea_json_template, template_outputs[fmea_output_start + 1])
        verify_svg_basics(template_outputs[0])
        verify_svg_basics(template_outputs[1])
        verify_fault_tree_svg_basics(template_outputs[2])
        verify_fault_tree_svg_basics(template_outputs[3])
        verify_exclusion_tree_svg_basics(template_outputs[4])
        verify_exclusion_tree_svg_basics(template_outputs[5])
        for output_path in template_outputs[two_by_two_output_start:two_by_two_output_end]:
            verify_two_by_two_svg_basics(output_path)
        for output_path in template_outputs[roadmap_output_start:roadmap_output_end]:
            verify_roadmap_timeline_svg_basics(output_path)
        verify_fmea_table_svg_basics(template_outputs[fmea_output_start])
        verify_fmea_table_svg_basics(template_outputs[fmea_output_start + 1])
    finally:
        for output_path in template_outputs:
            output_path.unlink(missing_ok=True)


def verify_cmd_launchers() -> None:
    launchers = {
        "fishbone_tool.cmd": "scripts\\new_fishbone.py",
        "鱼骨图工具.cmd": "fishbone_tool.cmd",
        "fault_tree_tool.cmd": "scripts\\new_fault_tree.py",
        "故障树工具.cmd": "fault_tree_tool.cmd",
        "exclusion_tree_tool.cmd": "scripts\\new_exclusion_tree.py",
        "排除树工具.cmd": "exclusion_tree_tool.cmd",
        "two_by_two_matrix_tool.cmd": "scripts\\new_two_by_two_matrix.py",
        "二乘二矩阵工具.cmd": "two_by_two_matrix_tool.cmd",
        "roadmap_timeline_tool.cmd": "scripts\\new_roadmap_timeline.py",
        "fmea_table_tool.cmd": "scripts\\new_fmea_table.py",
        "FMEA表工具.cmd": "fmea_table_tool.cmd",
        "路线图时间线工具.cmd": "roadmap_timeline_tool.cmd",
        "diagram_builder.cmd": "scripts\\diagram_builder_server.py",
        "图表编辑器.cmd": "diagram_builder.cmd",
    }
    for name, expected_text in launchers.items():
        path = ROOT / name
        if not path.exists():
            raise AssertionError(f"Missing launcher: {name}")
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="ignore")
        if expected_text not in text:
            raise AssertionError(f"{name}: launcher does not reference {expected_text}")
        if b"\n" in raw.replace(b"\r\n", b""):
            raise AssertionError(f"{name}: Windows launcher must use CRLF line endings so cmd.exe can resolve labels")
        if expected_text.endswith(".cmd") and "%*" not in text:
            raise AssertionError(f"{name}: wrapper launcher should forward command-line arguments with %*")


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


def verify_exclusion_tree_template_structure(data: dict[str, object], label: str) -> None:
    if str(data.get("diagram_type", "")).replace("-", "_") != "exclusion_tree":
        raise AssertionError(f"{label}: template must use diagram_type=exclusion_tree")

    problem = data.get("problem")
    if not isinstance(problem, dict) or not (str(problem.get("text_en", "")).strip() or str(problem.get("text_zh", "")).strip()):
        raise AssertionError(f"{label}: template must include a problem object")

    event_detail = data.get("event_detail")
    if not isinstance(event_detail, dict):
        raise AssertionError(f"{label}: template must include an event_detail object")
    has_detail_text = str(event_detail.get("text", "")).strip()
    bullets = event_detail.get("bullets")
    has_detail_bullets = isinstance(bullets, list) and any(str(item).strip() for item in bullets)
    if not has_detail_text and not has_detail_bullets:
        raise AssertionError(f"{label}: template event_detail must include text or bullets")

    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) < 3:
        raise AssertionError(f"{label}: template must include at least 3 checks")

    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise AssertionError(f"{label}: check {index} must be an object")
        if not (str(check.get("text_en", "")).strip() or str(check.get("text_zh", "")).strip()):
            raise AssertionError(f"{label}: check {index} must include text")
        conclusion = check.get("fail_conclusion")
        if not isinstance(conclusion, dict) or not (
            str(conclusion.get("text_en", "")).strip() or str(conclusion.get("text_zh", "")).strip()
        ):
            raise AssertionError(f"{label}: check {index} must include a fail_conclusion")

    final_pass = data.get("final_pass_conclusion")
    if not isinstance(final_pass, dict) or not (
        str(final_pass.get("text_en", "")).strip() or str(final_pass.get("text_zh", "")).strip()
    ):
        raise AssertionError(f"{label}: template must include final_pass_conclusion")


def verify_two_by_two_template_structure(data: dict[str, object], label: str) -> None:
    if str(data.get("diagram_type", "")).replace("-", "_") != "two_by_two_matrix":
        raise AssertionError(f"{label}: template must use diagram_type=two_by_two_matrix")
    preset = str(data.get("preset", "")).strip()
    if not preset:
        raise AssertionError(f"{label}: template must include a preset")
    if preset not in TWO_BY_TWO_TEMPLATE_PRESETS:
        raise AssertionError(f"{label}: template uses unsupported preset: {preset}")
    if str(data.get("subtitle", "")).strip() or data.get("show_subtitle"):
        raise AssertionError(f"{label}: two-by-two templates should not include hidden subtitle metadata")
    items = data.get("items")
    if not isinstance(items, list) or len(items) < 4:
        raise AssertionError(f"{label}: template must include at least four items")
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise AssertionError(f"{label}: item {index} must be an object")
        if not str(item.get("id", "")).strip() or not str(item.get("name", "")).strip():
            raise AssertionError(f"{label}: item {index} must include id and name")
        if str(item.get("notes", item.get("note", ""))).strip():
            raise AssertionError(f"{label}: template item {index} should not include non-rendered item-level notes")


def verify_two_by_two_template_guidance(path: Path, data: dict[str, object]) -> None:
    text = path.read_text(encoding="utf-8")
    for required in ["4-20", "Maximum supported item count is 20", "1 to 5"]:
        if required not in text:
            raise AssertionError(f"{path.name}: template guidance should mention {required!r}")
    if path.suffix == ".json":
        guidance = data.get("_template_guidance")
        if not isinstance(guidance, dict):
            raise AssertionError(f"{path.name}: JSON template must include _template_guidance")
        for key in ["item_limit", "score_range", "axis_mapping", "visible_notes"]:
            if not str(guidance.get(key, "")).strip():
                raise AssertionError(f"{path.name}: _template_guidance missing {key}")
    if path.suffix == ".md" and "| Notes |" in text:
        raise AssertionError(f"{path.name}: Markdown template should not include item-level Notes column")


def verify_roadmap_template_structure(data: dict[str, object], label: str) -> None:
    if str(data.get("diagram_type", "")).replace("-", "_") != "roadmap_timeline":
        raise AssertionError(f"{label}: template must use diagram_type=roadmap_timeline")
    if str(data.get("preset", "")).strip() not in {"swimlane_roadmap", "milestone_timeline"}:
        raise AssertionError(f"{label}: template must use a supported roadmap preset")
    if not str(data.get("title", "")).strip():
        raise AssertionError(f"{label}: template must include a title")
    if str(data.get("subtitle", "")).strip():
        raise AssertionError(f"{label}: roadmap templates should not include title-area subtitle metadata")
    if not str(data.get("goal", "")).strip():
        raise AssertionError(f"{label}: roadmap templates should include a visible goal line")

    preset = str(data.get("preset", "")).strip()
    if preset == "swimlane_roadmap":
        periods = data.get("periods", data.get("time_periods"))
        if not isinstance(periods, list) or len(periods) < 3:
            raise AssertionError(f"{label}: swimlane roadmap template must include at least three periods")
        for index, period in enumerate(periods, start=1):
            if not isinstance(period, dict) or not str(period.get("label", "")).strip():
                raise AssertionError(f"{label}: period {index} must include a label")
        lanes = data.get("lanes")
        initiatives = data.get("initiatives")
        if not isinstance(lanes, list) or len(lanes) < 2:
            raise AssertionError(f"{label}: swimlane roadmap template must include multiple lanes")
        if not isinstance(initiatives, list) or len(initiatives) < 2:
            raise AssertionError(f"{label}: swimlane roadmap template must include multiple initiatives")
    else:
        milestones = data.get("milestones")
        if not isinstance(milestones, list) or len(milestones) < 4:
            raise AssertionError(f"{label}: milestone timeline template must include multiple milestones")
        if data.get("show_table") is not True:
            raise AssertionError(f"{label}: milestone timeline template should enable the milestone table")


def verify_fmea_template_structure(data: dict[str, object], label: str) -> None:
    if str(data.get("diagram_type", "")).replace("-", "_") != "fmea_table":
        raise AssertionError(f"{label}: template must use diagram_type=fmea_table")
    if not str(data.get("title", "")).strip():
        raise AssertionError(f"{label}: template must include a title")
    if not str(data.get("goal", "")).strip():
        raise AssertionError(f"{label}: template must include a goal")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) < 3:
        raise AssertionError(f"{label}: template must include at least three FMEA rows")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise AssertionError(f"{label}: row {index} must be an object")
        for required in ["item_function", "failure_mode", "severity", "occurrence", "detection", "recommended_actions"]:
            if required not in row:
                raise AssertionError(f"{label}: row {index} missing {required}")


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


def verify_new_exclusion_tree_entrypoint() -> None:
    stem = f"verify-new-exclusion-tree-{os.getpid()}"
    input_path = EXCLUSION_TREE_WORK / f"{stem}.md"
    output_path = EXCLUSION_TREE_WORK / f"{stem}.svg"
    try:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_EXCLUSION_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_exclusion_tree.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_exclusion_tree.py did not create expected work files")
        verify_exclusion_tree_svg_basics(output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_EXCLUSION_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_exclusion_tree.py should refuse to overwrite existing work files without --force")
    finally:
        input_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)


def verify_new_two_by_two_entrypoint() -> None:
    stem = f"verify-new-two-by-two-{os.getpid()}"
    input_path = TWO_BY_TWO_WORK / f"{stem}.md"
    preset_input_path = TWO_BY_TWO_WORK / f"{stem}-preset.md"
    output_path = TWO_BY_TWO_WORK / f"{stem}.svg"
    preset_output_path = TWO_BY_TWO_WORK / f"{stem}-preset.svg"
    try:
        TWO_BY_TWO_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, preset_input_path, output_path, preset_output_path]:
            path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_two_by_two_matrix.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_two_by_two_matrix.py did not create expected work files")
        verify_two_by_two_svg_basics(output_path)

        preset_result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), f"{stem}-preset", "--format", "md", "--preset", "value_feasibility"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if preset_result.returncode != 0:
            raise AssertionError(f"new_two_by_two_matrix.py failed with --preset:\n{preset_result.stderr}")
        if "preset: value_feasibility" not in preset_input_path.read_text(encoding="utf-8"):
            raise AssertionError("new_two_by_two_matrix.py --preset did not copy the requested preset template")
        verify_two_by_two_svg_basics(preset_output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_two_by_two_matrix.py should refuse to overwrite existing work files without --force")
    finally:
        for path in [input_path, preset_input_path, output_path, preset_output_path]:
            path.unlink(missing_ok=True)


def verify_new_roadmap_entrypoint() -> None:
    stem = f"verify-new-roadmap-{os.getpid()}"
    input_path = ROADMAP_WORK / f"{stem}.md"
    preset_input_path = ROADMAP_WORK / f"{stem}-preset.md"
    output_path = ROADMAP_WORK / f"{stem}.svg"
    preset_output_path = ROADMAP_WORK / f"{stem}-preset.svg"
    try:
        ROADMAP_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, preset_input_path, output_path, preset_output_path]:
            path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_roadmap_timeline.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_roadmap_timeline.py did not create expected work files")
        verify_roadmap_timeline_svg_basics(output_path)

        preset_result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), f"{stem}-preset", "--format", "md", "--preset", "milestone_timeline"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if preset_result.returncode != 0:
            raise AssertionError(f"new_roadmap_timeline.py failed with --preset:\n{preset_result.stderr}")
        if "preset: milestone_timeline" not in preset_input_path.read_text(encoding="utf-8"):
            raise AssertionError("new_roadmap_timeline.py --preset did not copy the requested preset template")
        verify_roadmap_timeline_svg_basics(preset_output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_roadmap_timeline.py should refuse to overwrite existing work files without --force")
    finally:
        for path in [input_path, preset_input_path, output_path, preset_output_path]:
            path.unlink(missing_ok=True)


def verify_new_fmea_entrypoint() -> None:
    stem = f"verify-new-fmea-{os.getpid()}"
    input_path = FMEA_WORK / f"{stem}.md"
    output_path = FMEA_WORK / f"{stem}.svg"
    try:
        FMEA_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, output_path]:
            path.unlink(missing_ok=True)
        result = subprocess.run(
            [str(PYTHON), str(NEW_FMEA), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"new_fmea_table.py failed:\n{result.stderr}")
        if not input_path.exists() or not output_path.exists():
            raise AssertionError("new_fmea_table.py did not create expected work files")
        verify_fmea_table_svg_basics(output_path)

        overwrite_result = subprocess.run(
            [str(PYTHON), str(NEW_FMEA), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if overwrite_result.returncode == 0:
            raise AssertionError("new_fmea_table.py should refuse to overwrite existing work files without --force")
    finally:
        for path in [input_path, output_path]:
            path.unlink(missing_ok=True)


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


def verify_render_exclusion_tree_work_entrypoint() -> None:
    stem = f"verify-render-exclusion-tree-{os.getpid()}"
    md_input_path = EXCLUSION_TREE_WORK / f"{stem}.md"
    json_input_path = EXCLUSION_TREE_WORK / f"{stem}.json"
    output_path = EXCLUSION_TREE_WORK / f"{stem}.svg"
    try:
        EXCLUSION_TREE_WORK.mkdir(parents=True, exist_ok=True)
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_EXCLUSION_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_exclusion_tree.py failed during render_exclusion_tree_work verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_EXCLUSION_TREE_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_exclusion_tree_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_exclusion_tree_work.py did not create the expected SVG")
        verify_exclusion_tree_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "exclusion-tree.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_EXCLUSION_TREE_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_exclusion_tree_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_EXCLUSION_TREE_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_exclusion_tree_work.py --format json failed:\n{format_result.stderr}")
        verify_exclusion_tree_svg_basics(output_path)
    finally:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)


def verify_render_two_by_two_work_entrypoint() -> None:
    stem = f"verify-render-two-by-two-{os.getpid()}"
    md_input_path = TWO_BY_TWO_WORK / f"{stem}.md"
    json_input_path = TWO_BY_TWO_WORK / f"{stem}.json"
    output_path = TWO_BY_TWO_WORK / f"{stem}.svg"
    try:
        TWO_BY_TWO_WORK.mkdir(parents=True, exist_ok=True)
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_two_by_two_matrix.py failed during render_two_by_two verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_TWO_BY_TWO_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_two_by_two_matrix_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_two_by_two_matrix_work.py did not create the expected SVG")
        verify_two_by_two_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "two-by-two-matrix.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_TWO_BY_TWO_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_two_by_two_matrix_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_TWO_BY_TWO_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_two_by_two_matrix_work.py --format json failed:\n{format_result.stderr}")
        verify_two_by_two_svg_basics(output_path)
    finally:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)


def verify_render_roadmap_work_entrypoint() -> None:
    stem = f"verify-render-roadmap-{os.getpid()}"
    md_input_path = ROADMAP_WORK / f"{stem}.md"
    json_input_path = ROADMAP_WORK / f"{stem}.json"
    output_path = ROADMAP_WORK / f"{stem}.svg"
    try:
        ROADMAP_WORK.mkdir(parents=True, exist_ok=True)
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_roadmap_timeline.py failed during render_roadmap verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_ROADMAP_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_roadmap_timeline_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_roadmap_timeline_work.py did not create the expected SVG")
        verify_roadmap_timeline_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "roadmap-timeline.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_ROADMAP_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_roadmap_timeline_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_ROADMAP_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_roadmap_timeline_work.py --format json failed:\n{format_result.stderr}")
        verify_roadmap_timeline_svg_basics(output_path)
    finally:
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)


def verify_render_fmea_work_entrypoint() -> None:
    stem = f"verify-render-fmea-{os.getpid()}"
    md_input_path = FMEA_WORK / f"{stem}.md"
    json_input_path = FMEA_WORK / f"{stem}.json"
    output_path = FMEA_WORK / f"{stem}.svg"
    try:
        FMEA_WORK.mkdir(parents=True, exist_ok=True)
        for path in [md_input_path, json_input_path, output_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FMEA), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fmea_table.py failed during render_fmea verification:\n{create_result.stderr}")

        output_path.unlink(missing_ok=True)
        render_result = subprocess.run(
            [str(PYTHON), str(RENDER_FMEA_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render_result.returncode != 0:
            raise AssertionError(f"render_fmea_table_work.py failed:\n{render_result.stderr}")
        if not output_path.exists():
            raise AssertionError("render_fmea_table_work.py did not create the expected SVG")
        verify_fmea_table_svg_basics(output_path)

        json_input_path.write_text((TEMPLATES / "fmea-table.template.json").read_text(encoding="utf-8"), encoding="utf-8")
        ambiguous_result = subprocess.run(
            [str(PYTHON), str(RENDER_FMEA_WORK), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if ambiguous_result.returncode == 0:
            raise AssertionError("render_fmea_table_work.py should require --format when md and json inputs both exist")

        format_result = subprocess.run(
            [str(PYTHON), str(RENDER_FMEA_WORK), stem, "--format", "json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if format_result.returncode != 0:
            raise AssertionError(f"render_fmea_table_work.py --format json failed:\n{format_result.stderr}")
        verify_fmea_table_svg_basics(output_path)
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


def verify_export_exclusion_tree_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-exclusion-tree-png-{os.getpid()}"
    input_path = EXCLUSION_TREE_WORK / f"{stem}.md"
    svg_path = EXCLUSION_TREE_WORK / f"{stem}.svg"
    png_path = EXCLUSION_TREE_WORK / f"{stem}.png"
    try:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_EXCLUSION_TREE), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_exclusion_tree.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_EXCLUSION_TREE_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_exclusion_tree_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_exclusion_tree_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"Exclusion tree PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_EXCLUSION_TREE_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_exclusion_tree_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_export_two_by_two_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-two-by-two-png-{os.getpid()}"
    input_path = TWO_BY_TWO_WORK / f"{stem}.md"
    svg_path = TWO_BY_TWO_WORK / f"{stem}.svg"
    png_path = TWO_BY_TWO_WORK / f"{stem}.png"
    try:
        TWO_BY_TWO_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_two_by_two_matrix.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_TWO_BY_TWO_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_two_by_two_matrix_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_two_by_two_matrix_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"Two-by-two PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_TWO_BY_TWO_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_two_by_two_matrix_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_export_roadmap_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-roadmap-png-{os.getpid()}"
    input_path = ROADMAP_WORK / f"{stem}.md"
    svg_path = ROADMAP_WORK / f"{stem}.svg"
    png_path = ROADMAP_WORK / f"{stem}.png"
    try:
        ROADMAP_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_roadmap_timeline.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_ROADMAP_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_roadmap_timeline_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_roadmap_timeline_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"Roadmap timeline PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_ROADMAP_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_roadmap_timeline_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_export_fmea_png_entrypoint() -> None:
    from PIL import Image

    stem = f"verify-export-fmea-png-{os.getpid()}"
    input_path = FMEA_WORK / f"{stem}.md"
    svg_path = FMEA_WORK / f"{stem}.svg"
    png_path = FMEA_WORK / f"{stem}.png"
    try:
        FMEA_WORK.mkdir(parents=True, exist_ok=True)
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)

        create_result = subprocess.run(
            [str(PYTHON), str(NEW_FMEA), stem, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise AssertionError(f"new_fmea_table.py failed during PNG export verification:\n{create_result.stderr}")

        export_result = subprocess.run(
            [str(PYTHON), str(EXPORT_FMEA_PNG), stem],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if export_result.returncode != 0:
            raise AssertionError(f"export_fmea_table_png.py failed:\n{export_result.stderr}")
        if not png_path.exists():
            raise AssertionError("export_fmea_table_png.py did not create the expected PNG")

        svg_size = svg_dimensions(svg_path)
        with Image.open(png_path) as image:
            if image.size != svg_size:
                raise AssertionError(f"FMEA PNG dimensions {image.size} do not match SVG dimensions {svg_size}")

        unsafe_result = subprocess.run(
            [str(PYTHON), str(EXPORT_FMEA_PNG), "../outside"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if unsafe_result.returncode == 0:
            raise AssertionError("export_fmea_table_png.py accepted an unsafe name")
    finally:
        for path in [input_path, svg_path, png_path]:
            path.unlink(missing_ok=True)


def verify_diagram_builder_service() -> None:
    from PIL import Image

    sys.path.insert(0, str(ROOT / "scripts"))
    import diagram_builder_server
    verify_diagram_builder_exclusion_language_ui(diagram_builder_server.INDEX_HTML)
    verify_diagram_builder_two_by_two_ui(diagram_builder_server.INDEX_HTML)
    verify_diagram_builder_roadmap_ui(diagram_builder_server.INDEX_HTML)
    verify_diagram_builder_load_file_ui(diagram_builder_server.INDEX_HTML)
    verify_diagram_builder_preview_zoom_ui(diagram_builder_server.INDEX_HTML)

    stems = {
        "fishbone": f"verify-builder-fishbone-{os.getpid()}",
        "fault_tree": f"verify-builder-fault-tree-{os.getpid()}",
        "exclusion_tree": f"verify-builder-exclusion-tree-{os.getpid()}",
        "two_by_two_matrix": f"verify-builder-two-by-two-{os.getpid()}",
        "roadmap_timeline": f"verify-builder-roadmap-{os.getpid()}",
    }
    paths: list[Path] = []
    try:
        fishbone_json = json.dumps(diagram_builder_server.load_template("fishbone"), ensure_ascii=False)
        loaded_type, loaded_data = diagram_builder_server.parse_uploaded_file("legacy-fishbone.json", fishbone_json)
        if loaded_type != "fishbone" or loaded_data.get("diagram_type") != "fishbone":
            raise AssertionError("diagram_builder_server failed to parse a loaded fishbone JSON file")

        exclusion_md = (TEMPLATES / "exclusion-tree.template.md").read_text(encoding="utf-8")
        loaded_type, loaded_data = diagram_builder_server.parse_uploaded_file("legacy-exclusion.md", exclusion_md)
        if loaded_type != "exclusion_tree" or loaded_data.get("diagram_type") != "exclusion_tree":
            raise AssertionError("diagram_builder_server failed to parse a loaded exclusion-tree Markdown file")

        two_by_two_md = (TEMPLATES / "two-by-two-matrix.template.md").read_text(encoding="utf-8")
        loaded_type, loaded_data = diagram_builder_server.parse_uploaded_file("legacy-two-by-two.md", two_by_two_md)
        if loaded_type != "two_by_two_matrix" or loaded_data.get("diagram_type") != "two_by_two_matrix":
            raise AssertionError("diagram_builder_server failed to parse a loaded two-by-two Markdown file")

        roadmap_md = (TEMPLATES / "roadmap-timeline.milestone-timeline.template.md").read_text(encoding="utf-8")
        loaded_type, loaded_data = diagram_builder_server.parse_uploaded_file("legacy-roadmap.md", roadmap_md)
        if loaded_type != "roadmap_timeline" or loaded_data.get("diagram_type") != "roadmap_timeline":
            raise AssertionError("diagram_builder_server failed to parse a loaded roadmap Markdown file")

        for diagram_type, stem in stems.items():
            data = diagram_builder_server.load_template(diagram_type)
            json_path = diagram_builder_server.save_work_json(diagram_type, stem, data)
            svg_text_message = diagram_builder_server.render_work(diagram_type, stem)
            png_message = diagram_builder_server.export_png(diagram_type, stem)
            svg_path = diagram_builder_server.work_path(diagram_type, stem, ".svg")
            png_path = diagram_builder_server.work_path(diagram_type, stem, ".png")
            paths.extend([json_path, svg_path, png_path])
            if not svg_path.exists() or not png_path.exists():
                raise AssertionError(f"diagram_builder_server did not create SVG/PNG for {diagram_type}")
            if "Generated:" not in svg_text_message and "Rendered" not in svg_text_message:
                raise AssertionError(f"Unexpected render message for {diagram_type}: {svg_text_message}")
            if "Exported PNG" not in png_message:
                raise AssertionError(f"Unexpected PNG message for {diagram_type}: {png_message}")
            if diagram_type == "fishbone":
                verify_svg_basics(svg_path)
            elif diagram_type == "fault_tree":
                verify_fault_tree_svg_basics(svg_path)
            elif diagram_type == "exclusion_tree":
                verify_exclusion_tree_svg_basics(svg_path)
            elif diagram_type == "two_by_two_matrix":
                verify_two_by_two_svg_basics(svg_path)
            elif diagram_type == "roadmap_timeline":
                verify_roadmap_timeline_svg_basics(svg_path)
            expected_size = svg_dimensions(svg_path)
            with Image.open(png_path) as image:
                if image.size != expected_size:
                    raise AssertionError(f"Builder PNG dimensions {image.size} do not match SVG dimensions {expected_size}")

        for unsafe_name in ["../outside", r"..\outside", "has space", "UPPER", "name.ext"]:
            try:
                diagram_builder_server.validate_work_name(unsafe_name)
            except ValueError:
                continue
            raise AssertionError(f"diagram_builder_server accepted unsafe name: {unsafe_name}")
    finally:
        for path in paths:
            path.unlink(missing_ok=True)


def verify_diagram_builder_exclusion_language_ui(index_html: str) -> None:
    start = index_html.find("function renderExclusionTreeForm()")
    end = index_html.find("function renderTwoByTwoForm()", start)
    if end < 0:
        end = index_html.find('$("newBtn")', start)
    exclusion_html = index_html[start:end] if start >= 0 and end > start else index_html
    forbidden = [
        "Problem EN",
        "Problem ZH",
        "Question EN",
        "Question ZH",
        "Pass Label EN",
        "Pass Label ZH",
        "Fail Label EN",
        "Fail Label ZH",
        "Fail Cause EN",
        "Fail Cause ZH",
        "Fail Detail EN",
        "Fail Detail ZH",
        "Conclusion EN",
        "Conclusion ZH",
        "Exclusion Tree /",
        'row("Title"',
        'row("Subtitle"',
        'row("Icon"',
        'row("Pass Label"',
        'row("Fail Label"',
    ]
    hits = [text for text in forbidden if text in exclusion_html]
    if hits:
        raise AssertionError(f"diagram builder exclusion-tree UI should use single-language fields, found: {hits}")


def verify_diagram_builder_two_by_two_ui(index_html: str) -> None:
    start = index_html.find("function renderTwoByTwoForm()")
    end = index_html.find('$("newBtn")', start)
    two_by_two_html = index_html[start:end] if start >= 0 and end > start else index_html
    if 'row("Subtitle"' in two_by_two_html:
        raise AssertionError("diagram builder two-by-two UI should not expose hidden subtitle controls")
    if "Short note" in two_by_two_html or "item.note" in two_by_two_html:
        raise AssertionError("diagram builder two-by-two UI should not expose non-rendered item-level note controls")
    if "matrix-item-row" not in two_by_two_html or "score-input" not in two_by_two_html:
        raise AssertionError("diagram builder two-by-two UI should use compact one-line item rows")
    if 'row("Name"' in two_by_two_html:
        raise AssertionError("diagram builder two-by-two UI should not put item name on a separate row")
    if "nextTwoByTwoItemId" not in two_by_two_html or "model.items.push({ id: nextTwoByTwoItemId()" not in two_by_two_html:
        raise AssertionError("diagram builder two-by-two Add Item should preserve preset/id letter prefixes")
    if "applyTwoByTwoPreset(value)" not in two_by_two_html or "TWO_BY_TWO_PRESET_TEMPLATES" not in index_html:
        raise AssertionError("diagram builder two-by-two preset changes should reload preset-specific template items")
    for expected_mapping in ['action_priority: "A"', 'evidence_impact: "C"', 'value_feasibility: "F"']:
        if expected_mapping not in index_html:
            raise AssertionError(f"diagram builder two-by-two ID prefix helper missing {expected_mapping}")
    for expected_template in ['id: "A1"', 'id: "C1"', 'id: "F1"', 'id: "T1"', 'id: "I1"']:
        if expected_template not in index_html:
            raise AssertionError(f"diagram builder two-by-two preset template missing {expected_template}")
    if 'row("Language"' in two_by_two_html:
        raise AssertionError("diagram builder two-by-two UI should rely on auto language detection, not expose Language")
    for required in ['row("Title"', 'row("Preset"', 'row("Notes"', "Add Item"]:
        if required not in two_by_two_html:
            raise AssertionError(f"diagram builder two-by-two UI missing expected control: {required}")
    for required_text in ["Maximum", "Scores are 1-5", "Decision Table shows every item"]:
        if required_text not in two_by_two_html:
            raise AssertionError(f"diagram builder two-by-two UI missing limit guidance: {required_text}")
    markdown_start = index_html.find("function twoByTwoToMarkdown()")
    markdown_end = index_html.find("async function loadSvgIfExists()", markdown_start)
    markdown_html = index_html[markdown_start:markdown_end] if markdown_start >= 0 and markdown_end > markdown_start else index_html
    if "subtitle:" in markdown_html:
        raise AssertionError("diagram builder two-by-two Markdown export should not write hidden subtitle metadata")
    if "notes:" not in markdown_html:
        raise AssertionError("diagram builder two-by-two Markdown export should preserve visible Notes")
    if "| Note |" in markdown_html or "item.note" in markdown_html:
        raise AssertionError("diagram builder two-by-two Markdown export should not write non-rendered item-level notes")


def verify_diagram_builder_roadmap_ui(index_html: str) -> None:
    if '<option value="roadmap_timeline">Roadmap Timeline</option>' not in index_html:
        raise AssertionError("diagram builder should expose Roadmap Timeline in the diagram type selector")
    start = index_html.find("function renderRoadmapForm()")
    end = index_html.find('$("newBtn")', start)
    roadmap_html = index_html[start:end] if start >= 0 and end > start else index_html
    if "function renderRoadmapForm()" not in roadmap_html:
        raise AssertionError("diagram builder roadmap UI missing renderRoadmapForm")
    if 'row("Subtitle"' in roadmap_html:
        raise AssertionError("diagram builder roadmap UI should not expose a title-area subtitle control")
    for required in [
        'row("Title"',
        'row("Goal"',
        'row("Preset"',
        "swimlane_roadmap",
        "milestone_timeline",
        "Time Periods",
        "Lanes",
        "Initiatives",
        "Milestones",
        "Decision Points",
        "Phases",
        "Notes",
    ]:
        if required not in roadmap_html:
            raise AssertionError(f"diagram builder roadmap UI missing expected control: {required}")
    if "ROADMAP_PRESET_TEMPLATES" not in index_html or "applyRoadmapPreset(value)" not in roadmap_html:
        raise AssertionError("diagram builder roadmap preset changes should reload preset-specific template data")
    if "applyRoadmapGranularity(value)" not in roadmap_html or "buildRoadmapPeriods(roadmapDateRange()" not in roadmap_html:
        raise AssertionError("diagram builder roadmap granularity changes should rebuild generated time periods")
    if "roadmap-period-row" not in roadmap_html or "roadmap-card-grid" not in roadmap_html:
        raise AssertionError("diagram builder roadmap UI should use compact period rows and card-style item editors")
    if "input(period.id" in roadmap_html or "input(period.subtitle" in roadmap_html:
        raise AssertionError("diagram builder roadmap period UI should not expose generated id/subtitle fields")
    if "roadmap_timeline: { minPeriods" not in index_html:
        raise AssertionError("diagram builder roadmap UI should expose roadmap validation limits")
    markdown_start = index_html.find("function roadmapToMarkdown()")
    markdown_end = index_html.find("async function loadSvgIfExists()", markdown_start)
    markdown_html = index_html[markdown_start:markdown_end] if markdown_start >= 0 and markdown_end > markdown_start else index_html
    if "**Goal:**" not in markdown_html:
        raise AssertionError("diagram builder roadmap Markdown export should write a visible Goal line")
    if "subtitle:" in markdown_html:
        raise AssertionError("diagram builder roadmap Markdown export should not write title-area subtitle metadata")


def verify_diagram_builder_load_file_ui(index_html: str) -> None:
    required = [
        "Load File",
        'id="fileInput"',
        "/api/parse-file",
        "loadSelectedFile",
        'id="recentSelect"',
        'id="loadRecentBtn"',
        "rememberRecent",
        "loadRecent",
        'id="saveAsBtn"',
        'id="saveAsDialog"',
        'id="saveAsJsonBtn"',
        'id="saveAsMarkdownBtn"',
        "openSaveAsDialog",
        "saveAsSource",
        "showSaveFilePicker",
        "sourceTextForFormat",
        "modelToMarkdown",
        'id="formErrors"',
        "collectValidationErrors",
        "updateValidation",
        'id="helpBtn"',
        'id="helpDialog"',
        "openHelpDialog",
        "closeHelpDialog",
        "Workflow",
        "File Types",
        "Diagram Limits",
        "latest 12 work files",
        'event.key === "Escape"',
        "main-toolbar",
        "Fishbone needs at least",
        "Exclusion tree needs at least",
        "recommended 3-5 first-level intermediate events",
        "Fault tree review is clearest",
        "collectValidationWarnings",
        "confirmValidationWarnings",
        "works best with",
        "Continue rendering this draft?",
        "normalized to the current simplified model",
    ]
    missing = [text for text in required if text not in index_html]
    if missing:
        raise AssertionError(f"diagram builder Load File UI is missing: {missing}")
    if "Load Saved" in index_html or "loadSaved" in index_html:
        raise AssertionError("diagram builder should expose Load File instead of Load Saved")
    forbidden = ["Load Template", "Open Work Folder", "Download JSON", "Download MD", 'id="downloadJsonBtn"', 'id="downloadMdBtn"']
    hits = [text for text in forbidden if text in index_html]
    if hits:
        raise AssertionError(f"diagram builder toolbar should use compact Save As actions, found: {hits}")
    if ".toolbar {\n      display: flex;\n      flex-wrap: nowrap;" in index_html:
        raise AssertionError("diagram builder should not force all toolbar instances to nowrap")
    if 'class="toolbar main-toolbar"' not in index_html:
        raise AssertionError("diagram builder top action bar should use a dedicated main-toolbar class")
    forbidden_hard_minimums = [
        "Fishbone needs at least ${LIMITS.fishbone.minCategories}",
        "Exclusion tree needs at least ${LIMITS.exclusion_tree.minChecks}",
    ]
    hits = [text for text in forbidden_hard_minimums if text in index_html]
    if hits:
        raise AssertionError(f"diagram builder should warn, not hard-block, below recommended counts: {hits}")


def verify_diagram_builder_preview_zoom_ui(index_html: str) -> None:
    required = [
        "zoom-controls",
        'id="zoomOutBtn"',
        'id="zoomInBtn"',
        'id="zoomFitBtn"',
        "setPreviewZoom",
        "applyPreviewZoom",
        "setPreviewSvg",
    ]
    missing = [text for text in required if text not in index_html]
    if missing:
        raise AssertionError(f"diagram builder preview zoom UI is missing: {missing}")
    if "minmax(500px, 0.82fr) minmax(640px, 1.18fr)" not in index_html:
        raise AssertionError("diagram builder editor/preview column ratio should reserve more width for preview")


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

        exclusion_create_result = subprocess.run(
            [str(PYTHON), str(NEW_EXCLUSION_TREE), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if exclusion_create_result.returncode == 0:
            raise AssertionError(f"new_exclusion_tree.py accepted unsafe name: {unsafe_name}")

        exclusion_render_result = subprocess.run(
            [str(PYTHON), str(RENDER_EXCLUSION_TREE_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if exclusion_render_result.returncode == 0:
            raise AssertionError(f"render_exclusion_tree_work.py accepted unsafe name: {unsafe_name}")

        two_by_two_create_result = subprocess.run(
            [str(PYTHON), str(NEW_TWO_BY_TWO), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if two_by_two_create_result.returncode == 0:
            raise AssertionError(f"new_two_by_two_matrix.py accepted unsafe name: {unsafe_name}")

        two_by_two_render_result = subprocess.run(
            [str(PYTHON), str(RENDER_TWO_BY_TWO_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if two_by_two_render_result.returncode == 0:
            raise AssertionError(f"render_two_by_two_matrix_work.py accepted unsafe name: {unsafe_name}")

        roadmap_create_result = subprocess.run(
            [str(PYTHON), str(NEW_ROADMAP), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if roadmap_create_result.returncode == 0:
            raise AssertionError(f"new_roadmap_timeline.py accepted unsafe name: {unsafe_name}")

        roadmap_render_result = subprocess.run(
            [str(PYTHON), str(RENDER_ROADMAP_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if roadmap_render_result.returncode == 0:
            raise AssertionError(f"render_roadmap_timeline_work.py accepted unsafe name: {unsafe_name}")

        fmea_create_result = subprocess.run(
            [str(PYTHON), str(NEW_FMEA), unsafe_name, "--format", "md"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fmea_create_result.returncode == 0:
            raise AssertionError(f"new_fmea_table.py accepted unsafe name: {unsafe_name}")

        fmea_render_result = subprocess.run(
            [str(PYTHON), str(RENDER_FMEA_WORK), unsafe_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fmea_render_result.returncode == 0:
            raise AssertionError(f"render_fmea_table_work.py accepted unsafe name: {unsafe_name}")


def parse_path_numbers(path_data: str) -> list[float]:
    return [float(value) for value in re.findall(r"-?\d+\.\d+", path_data)]


if __name__ == "__main__":
    raise SystemExit(main())
