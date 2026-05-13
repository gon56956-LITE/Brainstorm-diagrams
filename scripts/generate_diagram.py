#!/usr/bin/env python3
"""Generate brainstorm diagrams from JSON or structured Markdown input."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from renderers.fishbone import render_fishbone_to_file


SUPPORTED_DIAGRAMS = {"fishbone"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a brainstorm diagram as deterministic SVG."
    )
    parser.add_argument("input", help="Input .json, .md, or .txt file")
    parser.add_argument("output", help="Output .svg file")
    return parser.parse_args()


def parse_input(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")

    if suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("JSON input must be an object.")
        return data

    if suffix in {".md", ".markdown"}:
        return parse_structured_markdown(text)

    return {
        "diagram_type": "fishbone",
        "topic": collapse_text(text) or "Problem / Topic",
    }


def parse_structured_markdown(text: str) -> dict[str, Any]:
    topic = ""
    categories: list[dict[str, Any]] = []
    current_category: dict[str, Any] | None = None
    current_primary_index: int | None = None
    loose_lines: list[str] = []
    diagnostics: list[str] = []

    for raw_line in text.splitlines():
        raw_line = raw_line.rstrip()
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue

        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            if level == 1 and heading:
                topic = normalize_topic_heading(heading)
                current_category = None
                current_primary_index = None
            elif level == 2 and heading:
                current_category = {"name_en": heading, "items": []}
                categories.append(current_category)
                current_primary_index = None
            continue

        bullet = parse_bullet(raw_line)
        if bullet is not None:
            indent_level, bullet_text = bullet
            if current_category is not None and indent_level == 0:
                current_category["items"].append(bullet_text)
                current_primary_index = len(current_category["items"]) - 1
            elif current_category is not None and indent_level == 1:
                if current_primary_index is None:
                    diagnostics.append(f"Ignored nested bullet '{bullet_text}': no primary item appears before it.")
                else:
                    current_item = current_category["items"][current_primary_index]
                    if isinstance(current_item, str):
                        current_item = {"subcategory": current_item, "items": []}
                        current_category["items"][current_primary_index] = current_item
                    current_item["items"].append(bullet_text)
            elif current_category is not None:
                diagnostics.append(f"Ignored third-level markdown bullet '{bullet_text}': only subcategory child items are supported.")
            else:
                loose_lines.append(bullet_text)
            continue

        loose_lines.append(line)

    if not topic:
        topic = normalize_topic_heading(collapse_text(loose_lines)) or "Problem / Topic"

    return {
        "diagram_type": "fishbone",
        "topic": topic,
        "categories": categories,
        "_diagnostics": diagnostics,
    }


def parse_bullet(line: str) -> tuple[int, str] | None:
    expanded = line.replace("\t", "    ")
    match = re.match(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.+)$", expanded)
    if not match:
        return None
    indent = len(match.group(1))
    if indent == 0:
        level = 0
    elif indent < 4:
        level = 1
    else:
        level = 2
    return level, match.group(2).strip()


def normalize_topic_heading(text: str) -> str:
    text = text.strip()
    return re.sub(r"^(?:problem|topic|question|问题|主题|课题|目标)[:：]\s*", "", text, flags=re.I)


def collapse_text(value: Any) -> str:
    if isinstance(value, str):
        parts = value.splitlines()
    else:
        parts = [str(item) for item in value if str(item).strip()]
    return " ".join(part.strip() for part in parts if part.strip())


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        data = parse_input(input_path)
        diagram_type = str(data.get("diagram_type", "fishbone")).strip().lower()
        if diagram_type not in SUPPORTED_DIAGRAMS:
            raise ValueError(
                'This version of brainstorm-diagrams supports only diagram_type="fishbone". '
                "The requested diagram type can be added in a future version."
            )
        result = render_fishbone_to_file(data, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated: {result['path']}")
    print(f"Format: {result['format']}")
    print(f"Diagram type: {result['diagram_type']}")
    print(f"Theme: {result['theme']}")
    print("Diagnostics:")
    diagnostics = result.get("diagnostics") or []
    if diagnostics:
        for diagnostic in diagnostics:
            print(f"- {diagnostic}")
    else:
        print("- none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
