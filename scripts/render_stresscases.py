#!/usr/bin/env python3
"""Render optional diagram stresscases for manual visual review."""

from __future__ import annotations

import sys
from pathlib import Path

from generate_diagram import parse_input
from renderers.exclusion_tree import render_exclusion_tree_to_file
from renderers.fishbone import render_fishbone_to_file
from renderers.fault_tree import render_fault_tree_to_file


ROOT = Path(__file__).resolve().parents[1]
STRESSCASES_ROOT = ROOT / "stresscases"
ALLOWED_SUFFIXES = {".md", ".markdown", ".json"}


def main() -> int:
    if not STRESSCASES_ROOT.exists():
        print(f"Error: missing stresscases directory: {STRESSCASES_ROOT}", file=sys.stderr)
        return 1

    inputs = sorted(
        path
        for diagram_dir in STRESSCASES_ROOT.iterdir()
        if diagram_dir.is_dir()
        for path in diagram_dir.iterdir()
        if path.suffix.lower() in ALLOWED_SUFFIXES and path.stem.lower() != "readme"
    )
    if not inputs:
        print("Error: no stresscase inputs found.", file=sys.stderr)
        return 1

    for input_path in inputs:
        output_path = input_path.with_suffix(".svg")
        try:
            data = parse_input(input_path)
            diagram_type = str(data.get("diagram_type", "fishbone")).strip().lower().replace("-", "_")
            if diagram_type == "exclusion_tree":
                result = render_exclusion_tree_to_file(data, output_path)
            elif diagram_type == "fault_tree":
                result = render_fault_tree_to_file(data, output_path)
            elif diagram_type == "fishbone":
                result = render_fishbone_to_file(data, output_path)
            else:
                raise ValueError(f"Unsupported stresscase diagram_type: {diagram_type}")
        except Exception as exc:
            print(f"Error rendering {input_path.name}: {exc}", file=sys.stderr)
            return 1

        print(f"Generated: {Path(result['path']).relative_to(ROOT)}")
        diagnostics = result.get("diagnostics") or []
        if diagnostics:
            print("Diagnostics:")
            for diagnostic in diagnostics:
                print(f"- {diagnostic}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
