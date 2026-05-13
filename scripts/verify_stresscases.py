#!/usr/bin/env python3
"""Verify optional fishbone stresscases used for manual visual review."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
STRESSCASES = ROOT / "stresscases"
RENDER_STRESSCASES = ROOT / "scripts" / "render_stresscases.py"
PYTHON = Path(sys.executable)

ALLOWED_SUFFIXES = {".md", ".markdown", ".json", ".svg"}
EXPECTED_FULL_STRESS_BRACES = 40
EXPECTED_FULL_STRESS_CATEGORIES = 8


def main() -> int:
    verify_directory()
    run_render_stresscases()
    verify_full_stress()
    print("Stresscase verification passed")
    return 0


def verify_directory() -> None:
    if not STRESSCASES.exists():
        raise AssertionError("Missing stresscases directory")

    for path in STRESSCASES.iterdir():
        if path.is_dir():
            raise AssertionError(f"Unexpected subdirectory in stresscases: {path.name}")
        if path.name == "README.md":
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise AssertionError(f"Unexpected file in stresscases: {path.name}")
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


def verify_full_stress() -> None:
    input_path = STRESSCASES / "full-stress.md"
    output_path = STRESSCASES / "full-stress.svg"
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


if __name__ == "__main__":
    raise SystemExit(main())
