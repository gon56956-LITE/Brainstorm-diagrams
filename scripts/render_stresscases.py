#!/usr/bin/env python3
"""Render optional fishbone stresscases for manual visual review."""

from __future__ import annotations

import sys
from pathlib import Path

from generate_diagram import parse_input
from renderers.fishbone import render_fishbone_to_file


ROOT = Path(__file__).resolve().parents[1]
STRESSCASES = ROOT / "stresscases" / "fishbone"


def main() -> int:
    if not STRESSCASES.exists():
        print(f"Error: missing stresscases directory: {STRESSCASES}", file=sys.stderr)
        return 1

    inputs = sorted(
        path
        for path in STRESSCASES.iterdir()
        if path.suffix.lower() in {".md", ".markdown", ".json"} and path.stem.lower() != "readme"
    )
    if not inputs:
        print("Error: no stresscase inputs found.", file=sys.stderr)
        return 1

    for input_path in inputs:
        output_path = input_path.with_suffix(".svg")
        try:
            data = parse_input(input_path)
            result = render_fishbone_to_file(data, output_path)
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
