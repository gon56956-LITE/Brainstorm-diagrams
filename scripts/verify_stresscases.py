#!/usr/bin/env python3
"""Verify optional stresscases used for manual visual review."""

from __future__ import annotations

import subprocess
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
STRESSCASES_ROOT = ROOT / "stresscases"
FISHBONE_STRESSCASES = STRESSCASES_ROOT / "fishbone"
FAULT_TREE_STRESSCASES = STRESSCASES_ROOT / "fault-tree"
EXCLUSION_TREE_STRESSCASES = STRESSCASES_ROOT / "exclusion-tree"
RENDER_STRESSCASES = ROOT / "scripts" / "render_stresscases.py"
PYTHON = Path(sys.executable)

ALLOWED_SUFFIXES = {".md", ".markdown", ".json", ".svg"}
EXPECTED_FULL_STRESS_BRACES = 40
EXPECTED_FULL_STRESS_CATEGORIES = 8
EXPECTED_FAULT_TREE_BASIC_EVENTS = 20
EXPECTED_FAULT_TREE_INTERMEDIATE_EVENTS = 5


def main() -> int:
    verify_directory()
    run_render_stresscases()
    verify_fishbone_full_stress()
    verify_fault_tree_full_stress()
    verify_fault_tree_nested_gates_stress()
    verify_exclusion_tree_full_stress()
    print("Stresscase verification passed")
    return 0


def verify_directory() -> None:
    if not STRESSCASES_ROOT.exists():
        raise AssertionError("Missing stresscases directory")
    for required_dir in [FISHBONE_STRESSCASES, FAULT_TREE_STRESSCASES, EXCLUSION_TREE_STRESSCASES]:
        if not required_dir.exists():
            raise AssertionError(f"Missing stresscases directory: {required_dir.relative_to(ROOT)}")

    for diagram_dir in STRESSCASES_ROOT.iterdir():
        if not diagram_dir.is_dir():
            if diagram_dir.name == "README.md":
                continue
            raise AssertionError(f"Unexpected file in stresscases root: {diagram_dir.name}")

        for path in diagram_dir.iterdir():
            if path.is_dir():
                raise AssertionError(f"Unexpected subdirectory in stresscases/{diagram_dir.name}: {path.name}")
            if path.name == "README.md":
                continue
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                raise AssertionError(f"Unexpected file in stresscases/{diagram_dir.name}: {path.name}")
            if path.name.lower() == "readme.svg":
                raise AssertionError("README.md must not be rendered to README.svg")


def run_render_stresscases() -> None:
    result = subprocess.run(
        [str(PYTHON), str(RENDER_STRESSCASES)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"render_stresscases.py failed:\n{result.stderr}")
    if "README.svg" in result.stdout:
        raise AssertionError("render_stresscases.py rendered README.md unexpectedly")


def verify_fishbone_full_stress() -> None:
    input_path = FISHBONE_STRESSCASES / "full-stress.md"
    output_path = FISHBONE_STRESSCASES / "full-stress.svg"
    if not input_path.exists():
        raise AssertionError("Missing full-stress.md")
    if not output_path.exists():
        raise AssertionError("Missing full-stress.svg")

    root = ET.parse(output_path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError("full-stress.svg root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width <= 1920 or height <= 1080:
        raise AssertionError(f"full-stress.svg must expand beyond 1920x1080, got {width}x{height}")

    topic_blocks = [element for element in root.iter() if element.attrib.get("id") == "topic-block"]
    if len(topic_blocks) != 1:
        raise AssertionError(f"Expected one topic-block, got {len(topic_blocks)}")
    topic_block = topic_blocks[0]
    topic_x = float(topic_block.attrib["x"])
    topic_w = float(topic_block.attrib["width"])
    if topic_x < width * 0.75 or topic_x + topic_w > width:
        raise AssertionError("topic-block must remain on the right side of the expanded canvas")

    category_labels = [
        element
        for element in root.iter()
        if element.tag.endswith("text")
        and (element.text or "").startswith("Category ")
        and element.attrib.get("font-size") == "26"
        and element.attrib.get("font-weight") == "700"
    ]
    if len(category_labels) != EXPECTED_FULL_STRESS_CATEGORIES:
        raise AssertionError(f"Expected {EXPECTED_FULL_STRESS_CATEGORIES} category labels, got {len(category_labels)}")

    braces = [
        element
        for element in root.iter()
        if element.tag.endswith("path") and element.attrib.get("class") == "child-curly-brace"
    ]
    if len(braces) != EXPECTED_FULL_STRESS_BRACES:
        raise AssertionError(f"Expected {EXPECTED_FULL_STRESS_BRACES} child braces, got {len(braces)}")


def verify_fault_tree_full_stress() -> None:
    input_path = FAULT_TREE_STRESSCASES / "full-stress.json"
    output_path = FAULT_TREE_STRESSCASES / "full-stress.svg"
    if not input_path.exists():
        raise AssertionError("Missing fault-tree/full-stress.json")
    if not output_path.exists():
        raise AssertionError("Missing fault-tree/full-stress.svg")

    root = ET.parse(output_path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError("fault-tree full-stress.svg root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width > 2240:
        raise AssertionError(f"fault-tree full-stress.svg should remain review-compact, got {width}x{height}")
    if height < 1080:
        raise AssertionError(f"fault-tree full-stress.svg should not shrink below 1080px height, got {width}x{height}")
    verify_fault_event_rects_within_canvas(root, "fault-tree full-stress.svg")

    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "top-event-block"]
    if len(top_blocks) != 1:
        raise AssertionError(f"Expected one top-event-block, got {len(top_blocks)}")

    detail_panels = [element for element in root.iter() if element.attrib.get("id") == "fault-event-detail-panel"]
    if len(detail_panels) != 1:
        raise AssertionError(f"Expected one fault-event-detail-panel, got {len(detail_panels)}")
    detail_rects = [child for child in list(detail_panels[0]) if child.tag.endswith("rect")]
    if not detail_rects:
        raise AssertionError("fault-tree event detail panel missing rect")
    detail_bottom = float(detail_rects[0].attrib["y"]) + float(detail_rects[0].attrib["height"])

    legends = [element for element in root.iter() if element.attrib.get("id") == "fault-tree-legend"]
    if len(legends) != 1:
        raise AssertionError(f"Expected one fault-tree-legend, got {len(legends)}")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    if "fault-gate-or" not in classes or "fault-gate-and" not in classes:
        raise AssertionError("fault-tree full-stress.svg must include both AND and OR gates")

    intermediate_events = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "fault-intermediate-event" in element.attrib.get("class", "")
    ]
    if len(intermediate_events) != EXPECTED_FAULT_TREE_INTERMEDIATE_EVENTS:
        raise AssertionError(
            f"Expected {EXPECTED_FAULT_TREE_INTERMEDIATE_EVENTS} intermediate events, got {len(intermediate_events)}"
        )
    intermediate_tops = []
    for group in intermediate_events:
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if rects:
            intermediate_tops.append(float(rects[0].attrib["y"]))
    if not intermediate_tops:
        raise AssertionError("fault-tree intermediate events missing rects")
    if detail_bottom >= min(intermediate_tops):
        raise AssertionError("fault-tree event detail panel overlaps the first intermediate event row")

    basic_events = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "fault-basic-event" in element.attrib.get("class", "")
    ]
    if len(basic_events) != EXPECTED_FAULT_TREE_BASIC_EVENTS:
        raise AssertionError(f"Expected {EXPECTED_FAULT_TREE_BASIC_EVENTS} basic events, got {len(basic_events)}")

    expanded_cards = 0
    basic_centers: dict[int, list[float]] = {}
    for group in basic_events:
        if any(child.tag.endswith("circle") for child in list(group)):
            raise AssertionError("fault-tree basic events must not render internal circle markers")
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        if not rects:
            raise AssertionError("fault-tree basic event group missing rect")
        width_value = float(rects[0].attrib.get("width", "0"))
        height_value = float(rects[0].attrib.get("height", "0"))
        center_x = round(float(rects[0].attrib.get("x", "0")) + width_value / 2)
        basic_centers.setdefault(center_x, []).append(float(rects[0].attrib.get("y", "0")))
        if width_value > 170 or height_value > 62:
            expanded_cards += 1
    if expanded_cards < 10:
        raise AssertionError(f"Expected many content-sized basic event cards, got {expanded_cards}")
    if len(basic_centers) != EXPECTED_FAULT_TREE_INTERMEDIATE_EVENTS:
        raise AssertionError(f"Expected {EXPECTED_FAULT_TREE_INTERMEDIATE_EVENTS} stacked basic-event columns, got {len(basic_centers)}")
    for center_x, y_values in basic_centers.items():
        if len(y_values) != 4:
            raise AssertionError(f"Expected 4 stacked basic events at x={center_x}, got {len(y_values)}")
        if y_values != sorted(y_values):
            raise AssertionError(f"Basic events at x={center_x} are not vertically ordered")
    verify_fault_tree_branch_connectors(root, "fault-tree full-stress.svg", min_trunks=5, min_branches=20)


def verify_fault_tree_nested_gates_stress() -> None:
    input_path = FAULT_TREE_STRESSCASES / "nested-gates.json"
    output_path = FAULT_TREE_STRESSCASES / "nested-gates.svg"
    if not input_path.exists():
        raise AssertionError("Missing fault-tree/nested-gates.json")
    if not output_path.exists():
        raise AssertionError("Missing fault-tree/nested-gates.svg")

    root = ET.parse(output_path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError("fault-tree nested-gates.svg root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width > 2240 or height < 1080:
        raise AssertionError(f"fault-tree nested-gates.svg should stay review-compact and at least 1080px high, got {width}x{height}")
    if height <= 1080:
        raise AssertionError(f"fault-tree nested-gates.svg should expand vertically for dense nested content, got {width}x{height}")
    verify_fault_event_rects_within_canvas(root, "fault-tree nested-gates.svg")

    text_values = [element.text or "" for element in root.iter() if element.tag.endswith("text")]
    required_labels = [
        "Power Path Mixed",
        "Logic",
        "Fuse Opens Under",
        "Startup Surge",
        "Control Path Mixed",
        "Ready Signal Not",
        "Detected",
    ]
    missing = [label for label in required_labels if label not in text_values]
    if missing:
        raise AssertionError(f"fault-tree nested-gates.svg missing expected labels: {missing}")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    if classes.count("fault-intermediate-event") < 6:
        raise AssertionError("fault-tree nested-gates.svg must include nested intermediate events")
    if classes.count("fault-gate-or") < 3 or classes.count("fault-gate-and") < 2:
        raise AssertionError("fault-tree nested-gates.svg must include nested AND and OR gates")

    basic_events = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "fault-basic-event" in element.attrib.get("class", "")
    ]
    if len(basic_events) < 14:
        raise AssertionError(f"fault-tree nested-gates.svg should render dense nested leaves, got {len(basic_events)}")
    verify_fault_tree_branch_connectors(root, "fault-tree nested-gates.svg", min_trunks=5, min_branches=14)


def verify_exclusion_tree_full_stress() -> None:
    input_path = EXCLUSION_TREE_STRESSCASES / "full-stress.json"
    output_path = EXCLUSION_TREE_STRESSCASES / "full-stress.svg"
    if not input_path.exists():
        raise AssertionError("Missing exclusion-tree/full-stress.json")
    if not output_path.exists():
        raise AssertionError("Missing exclusion-tree/full-stress.svg")

    root = ET.parse(output_path).getroot()
    if not root.tag.endswith("svg"):
        raise AssertionError("exclusion-tree full-stress.svg root is not svg")

    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    if width != 1920 or height < 1080:
        raise AssertionError(f"exclusion-tree full-stress.svg should keep 1920px width and at least 1080px height, got {width}x{height}")
    if height <= 1080:
        raise AssertionError(f"exclusion-tree full-stress.svg should expand vertically for 6 checks, got {width}x{height}")

    top_blocks = [element for element in root.iter() if element.attrib.get("id") == "exclusion-top-event-block"]
    if len(top_blocks) != 1:
        raise AssertionError(f"Expected one exclusion-top-event-block, got {len(top_blocks)}")
    detail_panels = [element for element in root.iter() if element.attrib.get("id") == "exclusion-event-detail-panel"]
    if len(detail_panels) != 1:
        raise AssertionError(f"Expected one exclusion-event-detail-panel, got {len(detail_panels)}")

    classes = " ".join(element.attrib.get("class", "") for element in root.iter())
    for required_class in [
        "exclusion-checkpoint",
        "exclusion-pass-chip",
        "exclusion-fail-chip",
        "exclusion-fail-conclusion",
        "exclusion-final-pass",
    ]:
        if required_class not in classes:
            raise AssertionError(f"exclusion-tree full-stress.svg missing {required_class}")

    checkpoints = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-checkpoint" in element.attrib.get("class", "")
    ]
    fail_cards = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-fail-conclusion" in element.attrib.get("class", "")
    ]
    if len(checkpoints) != 6:
        raise AssertionError(f"Expected 6 exclusion checkpoints, got {len(checkpoints)}")
    if len(fail_cards) != 6:
        raise AssertionError(f"Expected 6 fail conclusion cards, got {len(fail_cards)}")
    content_groups = checkpoints + fail_cards
    top_events = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-top-event" in element.attrib.get("class", "")
    ]
    final_cards_for_language = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-final-pass" in element.attrib.get("class", "")
    ]
    content_groups.extend(top_events)
    content_groups.extend(final_cards_for_language)
    bilingual_lines = [
        child.text or ""
        for group in content_groups
        for child in list(group)
        if child.tag.endswith("text") and " / " in (child.text or "")
    ]
    if bilingual_lines:
        raise AssertionError(f"exclusion-tree full-stress.svg should not auto-render bilingual labels: {bilingual_lines[:2]}")
    for group in checkpoints:
        rects = [child for child in list(group) if child.tag.endswith("rect")]
        texts = [child for child in list(group) if child.tag.endswith("text")]
        if not rects:
            raise AssertionError("exclusion-tree full-stress.svg checkpoint missing rect")
        rect_y = float(rects[0].attrib.get("y", "0"))
        rect_h = float(rects[0].attrib.get("height", "0"))
        for text in texts:
            text_y = float(text.attrib.get("y", "0"))
            if text_y < rect_y + 20 or text_y > rect_y + rect_h - 12:
                raise AssertionError("exclusion-tree full-stress.svg checkpoint text should stay inside its card")
    fail_card_rects = []
    for group in fail_cards:
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
    fail_card_heights = [rect[3] for rect in fail_card_rects]
    if len(set(round(value, 1) for value in fail_card_x_values)) < 2:
        raise AssertionError("exclusion-tree full-stress.svg should stagger fail conclusion cards horizontally")
    for previous_x, next_x in zip(fail_card_x_values, fail_card_x_values[1:]):
        if next_x > previous_x + 0.1:
            raise AssertionError("exclusion-tree full-stress.svg fail cards should step from upper-right to lower-left")
    for previous, current in zip(fail_card_rects, fail_card_rects[1:]):
        previous_bottom = previous[1] + previous[3]
        if current[1] < previous_bottom + 18:
            raise AssertionError("exclusion-tree full-stress.svg fail cards should not vertically collide")
    if max(fail_card_heights) <= 150:
        raise AssertionError("exclusion-tree full-stress.svg should content-size fail conclusion card heights")
    drop_connectors = [
        element
        for element in root.iter()
        if element.tag.endswith("path") and "exclusion-fail-drop-connector" in element.attrib.get("class", "")
    ]
    if len(drop_connectors) != 6:
        raise AssertionError(f"Expected 6 fail drop connectors, got {len(drop_connectors)}")
    fail_chip_inputs = [
        element
        for element in root.iter()
        if element.tag.endswith("line") and element.attrib.get("marker-end") != "url(#arrowNavy)"
    ]
    if len(fail_chip_inputs) < 6:
        raise AssertionError("exclusion-tree full-stress.svg should include visible connector lines into fail chips")
    final_connectors = [
        element
        for element in root.iter()
        if element.tag.endswith("path") and "exclusion-final-pass-connector" in element.attrib.get("class", "")
    ]
    if len(final_connectors) != 1:
        raise AssertionError("exclusion-tree full-stress.svg should include one final pass connector")
    path_numbers = parse_path_numbers(final_connectors[0].attrib.get("d", ""))
    x_values = path_numbers[0::2]
    if len(set(round(value, 1) for value in x_values)) != 1:
        raise AssertionError("exclusion-tree full-stress.svg final pass connector should drop straight into the final card")
    final_cards = [
        element
        for element in root.iter()
        if element.tag.endswith("g") and "exclusion-final-pass" in element.attrib.get("class", "")
    ]
    if len(final_cards) != 1:
        raise AssertionError("exclusion-tree full-stress.svg should include one final pass card")
    final_rects = [child for child in list(final_cards[0]) if child.tag.endswith("rect")]
    if not final_rects:
        raise AssertionError("exclusion-tree full-stress.svg final pass card missing rect")
    final_rect = final_rects[0]
    final_width = float(final_rect.attrib.get("width", "0"))
    final_y = float(final_rect.attrib.get("y", "0"))
    if final_width < 360:
        raise AssertionError("exclusion-tree full-stress.svg final pass card should be wider than cause cards")
    if fail_card_rects and final_y > max(rect[1] + rect[3] for rect in fail_card_rects) + 20:
        raise AssertionError("exclusion-tree full-stress.svg final pass card should not be pushed below unrelated fail cards")

    legends = [element for element in root.iter() if element.attrib.get("id") == "exclusion-tree-legend"]
    how_to_use = [element for element in root.iter() if element.attrib.get("id") == "exclusion-how-to-use"]
    if len(legends) != 1 or len(how_to_use) != 1:
        raise AssertionError("exclusion-tree full-stress.svg must include legend and how-to-use panels")
    decorative_dots = [
        element
        for element in root.iter()
        if element.tag.endswith("circle") and element.attrib.get("fill", "").lower() == "#d8e7f6"
    ]
    if decorative_dots:
        raise AssertionError("exclusion-tree full-stress.svg should not include background dots near content")
    how_rects = [child for child in list(how_to_use[0]) if child.tag.endswith("rect")]
    legend_rects = [child for child in list(legends[0]) if child.tag.endswith("rect")]
    if not how_rects or not legend_rects:
        raise AssertionError("exclusion-tree full-stress.svg auxiliary panels missing rects")
    how_rect = how_rects[0]
    how_x = float(how_rect.attrib.get("x", "0"))
    how_y = float(how_rect.attrib.get("y", "0"))
    how_w = float(how_rect.attrib.get("width", "0"))
    required_y = float(legend_rects[0].attrib.get("y", "0")) + float(legend_rects[0].attrib.get("height", "0")) + 36
    for x, y, w, h in fail_card_rects:
        if x < how_x + how_w + 28 and x + w > how_x - 28:
            required_y = max(required_y, y + h + 36)
    if abs(how_y - required_y) > 1.0:
        raise AssertionError("exclusion-tree full-stress.svg how-to-use panel should sit at the highest non-colliding right-side position")


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


def parse_path_numbers(path_data: str) -> list[float]:
    return [float(value) for value in re.findall(r"-?\d+\.\d+", path_data)]


if __name__ == "__main__":
    raise SystemExit(main())
